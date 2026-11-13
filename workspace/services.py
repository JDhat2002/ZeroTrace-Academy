from datetime import datetime, timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from authentication.models import UserSession
from labs.models import LabSession, VirtualMachine
from learning.models import Certificate, Enrolment
from learning.services import progress_percent
from memberships.models import UsageRecord
from notifications.models import ActivityEvent
from practice.models import Submission


def learning_minutes(user, since):
    total = ActivityEvent.objects.filter(user=user, category="learning", created_at__gte=since).aggregate(total=Sum("minutes"))
    return total["total"] or 0


def streak_days(user):
    dates = set(ActivityEvent.objects.filter(user=user, category="learning").annotate(day=TruncDate("created_at")).values_list("day", flat=True))
    if not dates:
        return 0
    day = timezone.localdate()
    if day not in dates:
        day = day - timedelta(days=1)
        if day not in dates:
            return 0
    count = 0
    while day in dates:
        count += 1
        day -= timedelta(days=1)
    return count


def week_bars(user):
    today = timezone.localdate()
    bars = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        end = start + timedelta(days=1)
        minutes = learning_minutes(user, start)
        minutes -= learning_minutes(user, end)
        bars.append({"label": day.strftime("%a"), "minutes": max(minutes, 0)})
    peak = max([bar["minutes"] for bar in bars] + [1])
    for bar in bars:
        bar["height"] = round(bar["minutes"] / peak * 100)
    return bars


def heatmap(user, weeks=16):
    today = timezone.localdate()
    start = today - timedelta(days=weeks * 7 - 1)
    counts = {
        row["day"]: row["total"]
        for row in ActivityEvent.objects.filter(user=user, created_at__date__gte=start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("minutes"))
    }
    columns = []
    day = start
    while day <= today:
        total = counts.get(day, 0) or 0
        level = 0 if not total else 1 if total < 30 else 2 if total < 60 else 3
        columns.append({"date": day.isoformat(), "level": level, "minutes": total})
        day += timedelta(days=1)
    return columns


def dashboard_metrics(user):
    enrolments = list(Enrolment.objects.filter(user=user).select_related("course"))
    percents = [progress_percent(row) for row in enrolments]
    now = timezone.now()
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    today_start = timezone.make_aware(datetime.combine(timezone.localdate(), datetime.min.time()))
    last_session = UserSession.objects.filter(user=user, revoked_at__isnull=True).order_by("-last_seen").first()
    return {
        "overall_progress": round(sum(percents) / len(percents)) if percents else 0,
        "courses_enrolled": len(enrolments),
        "courses_completed": sum(1 for row in enrolments if row.completed_at),
        "labs_completed": LabSession.objects.filter(user=user, status=LabSession.Status.COMPLETED).count(),
        "range_minutes": UsageRecord.objects.filter(user=user, metric=UsageRecord.Metric.RANGE).aggregate(total=Sum("amount"))["total"] or 0,
        "streak": streak_days(user),
        "certificates": Certificate.objects.filter(user=user).count(),
        "ctf_solved": Submission.objects.filter(user=user, correct=True).count(),
        "studied_today": learning_minutes(user, today_start),
        "week_minutes": learning_minutes(user, week_start),
        "month_minutes": learning_minutes(user, month_start),
        "last_active": last_session.last_seen if last_session else user.last_login,
        "running_machines": VirtualMachine.objects.filter(session__user=user, status=VirtualMachine.Status.RUNNING).count(),
    }


def daily_message(user, metrics):
    if metrics["studied_today"]:
        return f"You have {metrics['studied_today']} recorded minutes today."
    if metrics["streak"]:
        return f"Your learning streak is {metrics['streak']} days. A short session keeps it."
    if metrics["courses_enrolled"] == 0:
        return "No course is enrolled yet. The catalogue is in preview, and enrolment is stored for real."
    return "Nothing is recorded for today."
