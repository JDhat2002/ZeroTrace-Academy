import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from memberships.models import BillingAudit, Invoice, MembershipPlan, Payment, Subscription, WebhookEvent
from memberships.services import MembershipError, add_billing_period, price_for_interval


class BillingError(MembershipError):
    pass


def audit(action, *, user=None, category="", plan_code="", detail=None):
    return BillingAudit.objects.create(
        user=user if getattr(user, "pk", None) else None,
        action=action,
        category=category,
        plan_code=plan_code,
        detail=detail or {},
    )


def invoice_number():
    stamp = timezone.now().strftime("%Y%m%d")
    return f"ZT-{stamp}-{secrets.token_hex(4).upper()}"


def _as_int(value, label):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise BillingError(f"{label} must be a whole number of rupees.", status=400) from exc
    if number < 0:
        raise BillingError(f"{label} cannot be negative.", status=400)
    return number


def process_webhook(raw_body, signature):
    secret = settings.PAYMENT_WEBHOOK_SECRET
    if not secret:
        audit("webhook_rejected", detail={"reason": "secret-missing"})
        raise BillingError("Webhook secret is not configured.", status=503)
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(digest, signature.strip()):
        audit("webhook_rejected", detail={"reason": "signature"})
        raise BillingError("Webhook signature was not accepted.", status=401)
    try:
        payload = json.loads(raw_body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BillingError("Webhook body was not valid JSON.", status=400) from exc
    event_id = str(payload.get("id") or "").strip()
    if not event_id:
        raise BillingError("Webhook event id is required.", status=400)
    with transaction.atomic():
        event, created = WebhookEvent.objects.select_for_update().get_or_create(
            event_id=event_id,
            defaults={"payload_sha256": hashlib.sha256(raw_body).hexdigest()},
        )
        if not created and event.status == WebhookEvent.Status.APPLIED:
            return {"status": "duplicate", "event": event_id}
        if not created and event.status == WebhookEvent.Status.REJECTED:
            return {"status": "duplicate", "event": event_id, "detail": "This event was already rejected."}
        try:
            with transaction.atomic():
                result = _apply_payload(payload)
        except BillingError as exc:
            event.status = WebhookEvent.Status.REJECTED
            event.detail = {"message": exc.message}
            event.processed_at = timezone.now()
            event.save(update_fields=["status", "detail", "processed_at"])
            raise
        event.status = WebhookEvent.Status.APPLIED
        event.detail = result
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "detail", "processed_at"])
        return result


def _apply_payload(payload):
    kind = str(payload.get("type") or "")
    if kind == "payment.failed":
        return _record_failed(payload)
    if kind == "payment.refunded":
        return _record_refund(payload)
    if kind == "payment.confirmed":
        return _record_confirmed(payload)
    raise BillingError("Webhook type was not recognised.", status=400)


def _user_from_payload(payload):
    email = str(payload.get("email") or "").strip().lower()
    try:
        user_id = int(payload.get("user_id"))
    except (TypeError, ValueError) as exc:
        raise BillingError("Webhook user was not recognised.", status=400) from exc
    user = User.objects.filter(pk=user_id, email=email).first()
    if user is None:
        raise BillingError("Webhook user was not recognised.", status=404)
    return user


def _record_failed(payload):
    user = _user_from_payload(payload)
    key = str(payload.get("idempotency_key") or "").strip()
    if not key:
        raise BillingError("Idempotency key is required.", status=400)
    amount = _as_int(payload.get("amount"), "Amount")
    payment, created = Payment.objects.get_or_create(
        idempotency_key=key,
        defaults={
            "user": user,
            "amount_inr": amount,
            "currency": "INR",
            "status": Payment.Status.FAILED,
            "kind": payload.get("kind") or Payment.Kind.SUBSCRIPTION,
            "category": payload.get("category") or "",
            "provider_reference": str(payload.get("id") or ""),
        },
    )
    if not created and payment.status != Payment.Status.FAILED:
        raise BillingError("This payment was already recorded with a different status.", status=409)
    audit("payment_failed", user=user, category=payment.category, detail={"idempotency_key": key})
    return {"status": "failed", "payment": payment.pk}


def _record_refund(payload):
    key = str(payload.get("idempotency_key") or "").strip()
    payment = Payment.objects.filter(idempotency_key=key).first()
    if payment is None or payment.status != Payment.Status.CONFIRMED:
        raise BillingError("There is no confirmed payment to refund.", status=404)
    amount = _as_int(payload.get("amount", payment.amount_inr), "Refund")
    if amount > payment.amount_inr:
        raise BillingError("A refund cannot exceed the confirmed amount.", status=409)
    if payment.refund_inr == amount:
        return {"status": "duplicate", "payment": payment.pk}
    if payment.refund_inr and payment.refund_inr != amount:
        raise BillingError("This payment already has a different refund recorded.", status=409)
    payment.refund_inr = amount
    payment.save(update_fields=["refund_inr"])
    audit(
        "refund_recorded",
        user=payment.user,
        category=payment.category,
        plan_code=payment.plan.code if payment.plan_id else "",
        detail={"idempotency_key": key, "refund_inr": amount},
    )
    return {"status": "refunded", "payment": payment.pk, "refund_inr": amount}


def _record_confirmed(payload):
    sale_kind = str(payload.get("kind") or Payment.Kind.SUBSCRIPTION)
    if sale_kind in {Payment.Kind.WORKSHOP, Payment.Kind.TRAINING}:
        return _confirm_training(payload, sale_kind)
    if sale_kind != Payment.Kind.SUBSCRIPTION:
        raise BillingError("Payment kind was not recognised.", status=400)
    return _confirm_subscription(payload)


def _confirm_training(payload, sale_kind):
    user = _user_from_payload(payload)
    key = str(payload.get("idempotency_key") or "").strip()
    if not key:
        raise BillingError("Idempotency key is required.", status=400)
    amount = _as_int(payload.get("amount"), "Amount")
    if amount <= 0:
        raise BillingError("Collected training revenue must be greater than zero.", status=400)
    tax = _as_int(payload.get("tax") or 0, "Tax")
    fee = _as_int(payload.get("fee") or 0, "Fee")
    if tax + fee > amount:
        raise BillingError("Tax and fees cannot exceed the amount collected.", status=409)
    payment, created = Payment.objects.get_or_create(
        idempotency_key=key,
        defaults={
            "user": user,
            "amount_inr": amount,
            "tax_inr": tax,
            "fee_inr": fee,
            "currency": str(payload.get("currency") or "INR"),
            "status": Payment.Status.CONFIRMED,
            "kind": sale_kind,
            "category": "",
            "provider_reference": str(payload.get("id") or ""),
            "confirmed_at": timezone.now(),
        },
    )
    if not created:
        return {"status": "duplicate", "payment": payment.pk}
    _paid_invoice(payment)
    audit("training_collected", user=user, detail={"idempotency_key": key, "kind": sale_kind, "amount_inr": amount})
    return {"status": "confirmed", "payment": payment.pk, "kind": sale_kind}


def _confirm_subscription(payload):
    user = _user_from_payload(payload)
    key = str(payload.get("idempotency_key") or "").strip()
    if not key:
        raise BillingError("Idempotency key is required.", status=400)
    interval = str(payload.get("interval") or "")
    if interval not in {"month", "year"}:
        raise BillingError("Billing interval must be month or year.", status=400)
    category = str(payload.get("category") or "")
    if category not in {Payment.Category.INDIVIDUAL, Payment.Category.TEAM, Payment.Category.CAMPUS}:
        raise BillingError("Subscription category was not recognised.", status=400)
    plan = MembershipPlan.objects.filter(code=payload.get("plan"), category=category).first()
    if plan is None:
        raise BillingError("That plan is not in this product catalogue.", status=404)
    if str(payload.get("currency") or "INR") != plan.currency:
        raise BillingError("Currency does not match the configured plan.", status=409)
    amount = _as_int(payload.get("amount"), "Amount")
    tax = _as_int(payload.get("tax") or 0, "Tax")
    fee = _as_int(payload.get("fee") or 0, "Fee")
    if tax + fee > amount:
        raise BillingError("Tax and fees cannot exceed the amount collected.", status=409)
    team = None
    institution = None
    if category == Payment.Category.TEAM:
        team = _team_for_owner(payload, user)
    elif category == Payment.Category.CAMPUS:
        institution = _institution_for_owner(payload, user)
    existing = Payment.objects.filter(idempotency_key=key).first()
    if existing:
        return {"status": "duplicate", "payment": existing.pk}
    expected, subscription = _expected_amount(user, plan, interval, category, team, institution)
    if amount != expected:
        audit(
            "payment_rejected",
            user=user,
            category=category,
            plan_code=plan.code,
            detail={"amount": amount, "expected": expected, "interval": interval},
        )
        raise BillingError(
            "The amount does not match the configured price for this interval. No discount was applied.",
            status=409,
        )
    payment = Payment.objects.create(
        user=user,
        plan=plan,
        team=team,
        institution=institution,
        category=category,
        kind=Payment.Kind.SUBSCRIPTION,
        billing_interval=interval,
        amount_inr=amount,
        tax_inr=tax,
        fee_inr=fee,
        currency=plan.currency,
        status=Payment.Status.CONFIRMED,
        provider_reference=str(payload.get("id") or ""),
        idempotency_key=key,
        confirmed_at=timezone.now(),
    )
    subscription = _extend_subscription(user, plan, interval, amount, subscription)
    if team is not None:
        team.plan = plan
        team.subscription = subscription
        team.status = team.Status.ACTIVE
        team.save(update_fields=["plan", "subscription", "status"])
    if institution is not None:
        institution.plan = plan
        institution.subscription = subscription
        institution.status = institution.Status.ACTIVE
        institution.save(update_fields=["plan", "subscription", "status"])
    if category == Payment.Category.INDIVIDUAL and plan.code in dict(User.Membership.choices):
        user.membership = plan.code
        user.save(update_fields=["membership"])
        Subscription.objects.filter(
            user=user,
            source=Subscription.Source.INDIVIDUAL,
            status=Subscription.Status.ACTIVE,
        ).exclude(pk=subscription.pk).update(status=Subscription.Status.EXPIRED, expires_at=timezone.now())
    _paid_invoice(payment)
    audit(
        "payment_confirmed",
        user=user,
        category=category,
        plan_code=plan.code,
        detail={"idempotency_key": key, "amount_inr": amount, "interval": interval, "subscription": subscription.pk},
    )
    return {"status": "confirmed", "payment": payment.pk, "subscription": subscription.pk}


def _team_for_owner(payload, user):
    from teams.models import Team, TeamMember

    try:
        team_id = int(payload.get("team_id"))
    except (TypeError, ValueError) as exc:
        raise BillingError("Team billing requires a team id.", status=400) from exc
    team = Team.objects.filter(pk=team_id).first()
    if team is None:
        raise BillingError("Team was not found.", status=404)
    owner = TeamMember.objects.filter(team=team, user=user, role=TeamMember.Role.OWNER, active=True).exists()
    if team.owner_id != user.id and not owner:
        raise BillingError("Only the team owner can be billed for this team.", status=403)
    return team


def _institution_for_owner(payload, user):
    from campus.models import CampusAccount, Institution

    try:
        institution_id = int(payload.get("institution_id"))
    except (TypeError, ValueError) as exc:
        raise BillingError("Campus billing requires an institution id.", status=400) from exc
    institution = Institution.objects.filter(pk=institution_id).first()
    if institution is None:
        raise BillingError("Institution was not found.", status=404)
    owner = CampusAccount.objects.filter(
        institution=institution,
        user=user,
        role=CampusAccount.Role.OWNER,
        active=True,
    ).exists()
    if institution.owner_id != user.id and not owner:
        raise BillingError("Only the institution owner can be billed for this campus.", status=403)
    return institution


def _expected_amount(user, plan, interval, category, team, institution):
    subscription = _find_subscription(user, plan, category, team, institution)
    if subscription and subscription.contracted_price_inr is not None and subscription.billing_interval:
        if subscription.billing_interval != interval:
            raise BillingError("Renewal interval does not match the subscription.", status=409)
        if plan.quote_only:
            return subscription.contracted_price_inr, subscription
        return subscription.contracted_price_inr, subscription
    if plan.quote_only:
        raise BillingError("A quotation has no catalogue price to charge.", status=409)
    return price_for_interval(plan, interval), subscription


def _find_subscription(user, plan, category, team, institution):
    if team is not None and team.subscription_id:
        return team.subscription
    if institution is not None and institution.subscription_id:
        return institution.subscription
    if category != Payment.Category.INDIVIDUAL:
        return None
    return (
        Subscription.objects.filter(user=user, plan=plan, source=category)
        .exclude(status=Subscription.Status.EXPIRED)
        .order_by("-started_at")
        .first()
    )


def _extend_subscription(user, plan, interval, amount, subscription):
    now = timezone.now()
    if subscription is None:
        subscription = Subscription(
            user=user,
            plan=plan,
            source=plan.category,
            billing_interval=interval,
            contracted_price_inr=amount,
        )
    else:
        if subscription.contracted_price_inr is None:
            subscription.contracted_price_inr = amount
        subscription.plan = plan
        # Interval and contracted price stay as they were once set.
    anchor = subscription.expires_at if subscription.expires_at and subscription.expires_at > now else now
    subscription.expires_at = add_billing_period(anchor, subscription.billing_interval or interval)
    subscription.renews_at = subscription.expires_at
    subscription.current_period_end = subscription.expires_at
    subscription.status = Subscription.Status.ACTIVE
    subscription.cancel_at_period_end = False
    subscription.save()
    return subscription


def _paid_invoice(payment):
    if hasattr(payment, "invoice"):
        try:
            invoice = payment.invoice
        except Invoice.DoesNotExist:
            invoice = None
        if invoice:
            invoice.status = Invoice.Status.PAID
            invoice.amount_inr = payment.amount_inr
            invoice.save(update_fields=["status", "amount_inr"])
            return invoice
    return Invoice.objects.create(
        payment=payment,
        team=payment.team,
        institution=payment.institution,
        number=invoice_number(),
        status=Invoice.Status.PAID,
        category=payment.category,
        kind=payment.kind,
        amount_inr=payment.amount_inr,
        tax_inr=payment.tax_inr,
    )


def record_collected_training(user, *, payer, amount_inr, kind, tax_inr=0, fee_inr=0, note=""):
    if kind not in {Payment.Kind.WORKSHOP, Payment.Kind.TRAINING}:
        raise BillingError("Only a workshop or training receipt can be recorded here.", status=400)
    amount = _as_int(amount_inr, "Amount")
    tax = _as_int(tax_inr, "Tax")
    fee = _as_int(fee_inr, "Fee")
    if amount <= 0:
        raise BillingError("Enter the amount that was collected.", status=400)
    if tax + fee > amount:
        raise BillingError("Tax and fees cannot exceed the amount collected.", status=409)
    payment = Payment.objects.create(
        user=payer,
        amount_inr=amount,
        tax_inr=tax,
        fee_inr=fee,
        currency="INR",
        status=Payment.Status.CONFIRMED,
        kind=kind,
        category="",
        idempotency_key=f"manual-{secrets.token_hex(8)}",
        provider_reference=note[:128],
        confirmed_at=timezone.now(),
    )
    _paid_invoice(payment)
    audit("training_collected", user=user, detail={"payment": payment.pk, "kind": kind, "amount_inr": amount, "payer": payer.pk})
    return payment


def issue_outstanding_invoice(*, user, amount_inr, category, team=None, institution=None, note=""):
    amount = _as_int(amount_inr, "Amount")
    if amount <= 0:
        raise BillingError("An invoice needs an amount.", status=400)
    invoice = Invoice.objects.create(
        payment=None,
        team=team,
        institution=institution,
        number=invoice_number(),
        status=Invoice.Status.OUTSTANDING,
        category=category,
        kind=Payment.Kind.SUBSCRIPTION,
        amount_inr=amount,
        due_at=timezone.now() + timedelta(days=14),
    )
    audit("invoice_issued", user=user, category=category, detail={"invoice": invoice.number, "amount_inr": amount, "note": note[:200]})
    return invoice
