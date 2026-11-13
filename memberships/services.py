import calendar
from datetime import datetime, time

from django.db.models import Sum
from django.utils import timezone

from accounts.access import has_membership
from memberships.models import MembershipPlan, Subscription, UsageRecord


class MembershipError(Exception):
    def __init__(self, message, status=403):
        super().__init__(message)
        self.message = message
        self.status = status


def price_for_interval(plan, interval):
    """Return the stored price for an interval. No discount is applied."""
    if plan.quote_only:
        raise MembershipError("This plan is issued by quotation. It has no self-serve price.", status=409)
    if interval == Subscription.Interval.YEAR or interval == "year":
        if plan.annual_price_inr is None:
            raise MembershipError("An annual price is not configured for this plan.", status=409)
        return plan.annual_price_inr
    if interval == Subscription.Interval.MONTH or interval == "month":
        return plan.price_inr
    raise MembershipError("Choose a monthly or annual interval.", status=400)


def add_billing_period(moment, interval):
    if interval == "year":
        return moment.replace(year=moment.year + 1)
    month = moment.month + 1
    year = moment.year
    if month > 12:
        month = 1
        year += 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def ensure_subscription(user):
    active = (
        Subscription.objects.select_related("plan")
        .filter(user=user, status=Subscription.Status.ACTIVE, source=Subscription.Source.INDIVIDUAL)
        .order_by("-started_at")
        .first()
    )
    if active:
        return active
    plan = MembershipPlan.objects.filter(code=user.membership, category=MembershipPlan.Category.INDIVIDUAL).first()
    plan = plan or MembershipPlan.objects.filter(code="free").first()
    if plan is None:
        return None
    return Subscription.objects.create(
        user=user,
        plan=plan,
        status=Subscription.Status.ACTIVE,
        source=Subscription.Source.INDIVIDUAL,
        billing_interval=Subscription.Interval.MONTH,
        contracted_price_inr=plan.price_inr,
    )


def current_plan(user):
    subscription = ensure_subscription(user)
    if subscription:
        return subscription.plan
    return MembershipPlan.objects.filter(code="free").first()


def individual_plans():
    return MembershipPlan.objects.filter(category=MembershipPlan.Category.INDIVIDUAL, is_public=True)


def request_plan_change(user, code):
    plan = MembershipPlan.objects.filter(
        code=code,
        is_public=True,
        category=MembershipPlan.Category.INDIVIDUAL,
    ).first()
    if plan is None:
        raise MembershipError("That plan is not in the individual catalogue.", status=404)
    current = current_plan(user)
    if current and plan.code == current.code:
        return current
    if plan.quote_only:
        raise MembershipError("This plan is issued by quotation.", status=403)
    if not plan.checkout_enabled:
        raise MembershipError(
            "Payments are not connected. A browser request cannot activate or bill this plan.",
            status=403,
        )
    raise MembershipError("Payment confirmation is required before a plan can change.", status=403)


def usage_summary(user):
    plan = current_plan(user)
    totals = {
        row["metric"]: row["total"]
        for row in UsageRecord.objects.filter(user=user).values("metric").annotate(total=Sum("amount"))
    }
    rows = []
    if plan is None:
        return rows
    mapping = [
        ("lab_minutes", "Lab minutes", plan.lab_minutes),
        ("range_minutes", "Cyber Range minutes", plan.range_minutes),
        ("vm_sessions", "Concurrent VM allowance", plan.vm_concurrent),
        ("vm_hours", "VM-hours", plan.vm_hours),
        ("storage_mb", "Storage (MB)", plan.storage_mb),
    ]
    for metric, label, allowance in mapping:
        used = totals.get(metric, 0) or 0
        rows.append({"metric": metric, "label": label, "allowance": allowance, "used": used})
    return rows


def user_has_plan(user, code):
    return has_membership(user, code)


def aware(moment):
    if timezone.is_naive(moment):
        return timezone.make_aware(moment, timezone.get_current_timezone())
    return moment


def start_of_day(day):
    return aware(datetime.combine(day, time.min))
