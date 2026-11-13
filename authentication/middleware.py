from django.contrib.auth import logout
from django.utils import timezone

from authentication.models import UserSession


class SessionActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            key = request.session.session_key
            row = UserSession.objects.filter(session_key=key).first() if key else None
            if row and (row.revoked_at is not None or row.user_id != user.id):
                logout(request)
            elif row:
                UserSession.objects.filter(pk=row.pk).update(last_seen=timezone.now())
        return self.get_response(request)
