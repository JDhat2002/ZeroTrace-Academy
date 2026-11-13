from audit.models import SecurityEvent


def client_ip(request):
    if request is None:
        return None
    return request.META.get("REMOTE_ADDR") or None


def user_agent(request):
    if request is None:
        return ""
    return (request.META.get("HTTP_USER_AGENT") or "")[:256]


def record(kind, *, request=None, user=None, detail=None):
    return SecurityEvent.objects.create(
        user=user if getattr(user, "pk", None) else None,
        kind=kind,
        ip_address=client_ip(request),
        user_agent=user_agent(request),
        detail=detail or {},
    )
