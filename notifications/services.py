from django.utils import timezone

from notifications.models import ActivityEvent, Notification


def record_activity(user, category, summary, minutes=0):
    ActivityEvent.objects.create(user=user, category=category, summary=summary, minutes=minutes)
    Notification.objects.create(user=user, category=category if category in Notification.Category.values else "learning", summary=summary)


def unread_count(user):
    return Notification.objects.filter(user=user, read_at__isnull=True).count()


def mark_read(user, notification_id=None):
    rows = Notification.objects.filter(user=user, read_at__isnull=True)
    if notification_id:
        rows = rows.filter(pk=notification_id)
    rows.update(read_at=timezone.now())
