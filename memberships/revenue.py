import calendar
from datetime import datetime, time

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from memberships.models import Invoice, OperatingCost, Payment, RevenueTarget, Subscription


def _add_months(start, months):
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)


def _bounds(target):
    start = timezone.make_aware(datetime.combine(target.starts_on, time.min))
    end_day = _add_months(target.starts_on, target.horizon_months)
    end = timezone.make_aware(datetime.combine(end_day, time.min))
    return start, end


def _money(qs):
    row = qs.aggregate(
        gross=Sum("amount_inr"),
        refunds=Sum("refund_inr"),
        tax=Sum("tax_inr"),
        fees=Sum("fee_inr"),
        count=Count("id"),
    )
    gross = row["gross"] or 0
    refunds = row["refunds"] or 0
    tax = row["tax"] or 0
    fees = row["fees"] or 0
    collected = gross - refunds
    return {
        "gross": gross,
        "refunds": refunds,
        "tax": tax,
        "fees": fees,
        "collected": collected,
        "net": collected - tax - fees,
        "count": row["count"] or 0,
    }


def _in_window(qs, start, end):
    return qs.annotate(collected_at=Coalesce("confirmed_at", "created_at")).filter(
        collected_at__gte=start,
        collected_at__lt=end,
    )


def revenue_report():
    target = RevenueTarget.objects.filter(code="first-seven-months").first()
    confirmed = Payment.objects.filter(status=Payment.Status.CONFIRMED)
    if target is None:
        window = confirmed.none()
        start = end = None
    else:
        start, end = _bounds(target)
        window = _in_window(confirmed, start, end)
    subscriptions = window.filter(kind=Payment.Kind.SUBSCRIPTION)
    lines = {
        "individual": _money(subscriptions.filter(category=Payment.Category.INDIVIDUAL)),
        "team": _money(subscriptions.filter(category=Payment.Category.TEAM)),
        "campus": _money(subscriptions.filter(category=Payment.Category.CAMPUS)),
        "workshops": _money(window.filter(kind__in=[Payment.Kind.WORKSHOP, Payment.Kind.TRAINING])),
        "monthly": _money(subscriptions.filter(billing_interval=Payment.Interval.MONTH)),
        "annual": _money(subscriptions.filter(billing_interval=Payment.Interval.YEAR)),
        "all": _money(window),
    }
    outstanding = Invoice.objects.filter(status=Invoice.Status.OUTSTANDING).aggregate(
        total=Sum("amount_inr"),
        count=Count("id"),
    )
    costs = OperatingCost.objects.all()
    if start and end:
        costs = costs.filter(incurred_on__gte=start.date(), incurred_on__lt=end.date())
    operating = costs.aggregate(total=Sum("amount_inr"), count=Count("id"))
    excluded = {
        "pending": Payment.objects.filter(status=Payment.Status.PENDING).count(),
        "failed": Payment.objects.filter(status=Payment.Status.FAILED).count(),
        "cancelled_subscriptions": Subscription.objects.filter(status=Subscription.Status.CANCELLED).count(),
    }
    operating_total = operating["total"] or 0
    return {
        "target": target,
        "window_start": start,
        "window_end": end,
        "lines": lines,
        "outstanding_total": outstanding["total"] or 0,
        "outstanding_count": outstanding["count"] or 0,
        "operating_total": operating_total,
        "operating_count": operating["count"] or 0,
        "after_costs": lines["all"]["net"] - operating_total,
        "excluded": excluded,
        "costs": costs.order_by("-incurred_on"),
    }
