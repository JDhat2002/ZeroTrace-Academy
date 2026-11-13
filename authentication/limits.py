from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from authentication.models import LoginAttempt


def record_attempt(kind, *, email="", ip_address=None, succeeded=False):
    return LoginAttempt.objects.create(
        kind=kind,
        email=(email or "").lower(),
        ip_address=ip_address or None,
        succeeded=succeeded,
    )


def too_many(kind, *, email="", ip_address=None, bucket="login_ip", failures_only=True):
    rule = settings.AUTH_LIMITS[bucket]
    since = timezone.now() - timedelta(seconds=rule["window"])
    query = LoginAttempt.objects.filter(kind=kind, created_at__gte=since)
    if failures_only:
        query = query.filter(succeeded=False)
    if email:
        query = query.filter(email=email.lower())
    if ip_address:
        query = query.filter(ip_address=ip_address)
    return query.count() >= rule["limit"]


def clear_failures(kind, email):
    LoginAttempt.objects.filter(kind=kind, email=email.lower(), succeeded=False).delete()
