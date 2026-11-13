from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from authentication.exceptions import AuthError
from authentication.services import (
    begin_mfa,
    confirm_mfa,
    disable_mfa,
    login_user,
    logout_all,
    logout_user,
    register_user,
    request_password_reset,
    resend_verification,
    reset_password,
    username_available,
    verify_mfa,
)


def _guard(func):
    def wrapped(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except AuthError as exc:
            body = {"detail": exc.message, "code": exc.code}
            if exc.field:
                body["field"] = exc.field
            return Response(body, status=exc.status)
    return wrapped


class AuthAnonThrottle(AnonRateThrottle):
    rate = "20/minute"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthAnonThrottle])
@_guard
def register(request):
    register_user(request, request.data)
    return Response({"detail": "Check your email for the next step."}, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthAnonThrottle])
@_guard
def login_api(request):
    result = login_user(
        request,
        request.data.get("email"),
        request.data.get("password"),
        bool(request.data.get("remember")),
    )
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@_guard
def logout_api(request):
    logout_user(request)
    return Response({"detail": "Signed out."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthAnonThrottle])
@_guard
def verify_email_api(request):
    from authentication.services import consume_verification

    user = consume_verification(request.data.get("token") or "")
    if user is None:
        raise AuthError("This link is invalid or has expired.", code="expired")
    return Response({"detail": "Email verified."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthAnonThrottle])
@_guard
def resend_api(request):
    resend_verification(request, request.data.get("email"))
    return Response({"detail": "If an unverified account exists, a new link is on its way."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthAnonThrottle])
@_guard
def forgot_api(request):
    request_password_reset(request, request.data.get("email"))
    return Response({"detail": "If an account exists for that email, a reset message is on its way."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthAnonThrottle])
@_guard
def reset_api(request):
    reset_password(
        request,
        request.data.get("token") or "",
        request.data.get("password") or "",
        request.data.get("confirm_password") or "",
    )
    return Response({"detail": "Password updated."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@_guard
def mfa_setup(request):
    return Response(begin_mfa(request.user))


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthAnonThrottle])
@_guard
def mfa_verify(request):
    if request.session.get("pre_mfa_user"):
        verify_mfa(request, request.data.get("code"))
        return Response({"detail": "Signed in."})
    if not request.user.is_authenticated:
        raise AuthError("Sign in again before entering a verification code.", status=401, code="mfa_session")
    codes = confirm_mfa(request.user, request.data.get("code"))
    request.session.pop("mfa_setup_required", None)
    return Response({"detail": "Two-factor authentication is on.", "recovery_codes": codes})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@_guard
def mfa_disable(request):
    disable_mfa(request, request.data.get("password") or "", request.data.get("code") or "")
    return Response({"detail": "Two-factor authentication is off."})


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
@throttle_classes([AuthAnonThrottle])
def username_api(request):
    from authentication.limits import record_attempt, too_many
    from audit.services import client_ip

    ip = client_ip(request)
    if too_many("username", ip_address=ip, bucket="username", failures_only=False):
        return Response({"detail": "Too many attempts."}, status=429)
    record_attempt("username", ip_address=ip, succeeded=False)
    name = (request.query_params.get("username") or "").strip()
    return Response({"available": username_available(name)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_list(request):
    from authentication.models import UserSession

    rows = UserSession.objects.filter(user=request.user, revoked_at__isnull=True).order_by("-last_seen")
    return Response([
        {
            "id": row.pk,
            "ip_address": row.ip_address,
            "user_agent": row.user_agent,
            "created_at": row.created_at,
            "last_seen": row.last_seen,
            "current": row.session_key == request.session.session_key,
        }
        for row in rows
    ])


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@_guard
def session_delete(request, session_id):
    from authentication.services import revoke_session

    current = revoke_session(request, session_id)
    return Response({"detail": "Session revoked.", "current": current})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@_guard
def session_logout_all(request):
    logout_all(request)
    return Response({"detail": "Signed out of every session."})
