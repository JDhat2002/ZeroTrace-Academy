import hmac
import secrets

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accounts.countries import COUNTRIES
from accounts.models import User
from audit.models import SecurityEvent
from audit.services import client_ip, record
from authentication.exceptions import AuthError
from authentication.google import authorization_url, configured, fetch_google_identity
from authentication.limits import record_attempt, too_many
from authentication.models import MFAConfiguration, UserSession
from authentication.services import (
    NEUTRAL_REGISTER,
    NEUTRAL_RESET,
    begin_mfa,
    change_password,
    confirm_mfa,
    consume_verification,
    disable_mfa,
    login_user,
    logout_user,
    sign_in_with_google,
    request_password_reset,
    resend_verification,
    reset_password,
    revoke_session,
    verify_mfa,
    logout_all,
)
import pyotp

from authentication.services import _qr_data_uri
from authentication.tokens import decrypt_secret


def destination(request):
    if request.session.get("mfa_setup_required"):
        return redirect("mfa-manage")
    if request.user.is_authenticated and not request.user.onboarding_completed_at:
        return redirect("onboarding")
    return redirect("dashboard")


def _guard_mfa(request):
    if request.session.get("mfa_setup_required") and getattr(request.resolver_match, "url_name", "") not in {
        "mfa-manage",
        "logout",
    }:
        return redirect("mfa-manage")
    return None


@require_http_methods(["GET", "POST"])
def login_page(request):
    if request.user.is_authenticated:
        return destination(request)
    error = request.session.pop("auth_error", "") if request.method == "GET" else ""
    if request.method == "POST":
        try:
            result = login_user(
                request,
                request.POST.get("email"),
                request.POST.get("password"),
                request.POST.get("remember") == "on",
            )
        except AuthError as exc:
            error = exc.message
        else:
            if result["state"] == "mfa":
                return redirect("mfa-challenge")
            return destination(request)
    return render(request, "auth/login.html", {"error": error, "email": request.POST.get("email", "")})


@require_http_methods(["GET", "POST"])
def register_page(request):
    if request.user.is_authenticated:
        return destination(request)
    error = request.session.pop("auth_error", "") if request.method == "GET" else ""
    field = ""
    sent = False
    if request.method == "POST":
        from authentication.services import register_user

        payload = {
            "full_name": request.POST.get("full_name"),
            "username": request.POST.get("username"),
            "email": request.POST.get("email"),
            "password": request.POST.get("password"),
            "confirm_password": request.POST.get("confirm_password"),
            "country": request.POST.get("country"),
            "learning_interest": request.POST.get("learning_interest"),
            "accept_terms": request.POST.get("accept_terms") == "on",
        }
        try:
            register_user(request, payload)
        except AuthError as exc:
            error = exc.message
            field = exc.field or ""
        else:
            sent = True
    return render(
        request,
        "auth/register.html",
        {
            "error": error,
            "field": field,
            "sent": sent,
            "neutral": NEUTRAL_REGISTER,
            "countries": COUNTRIES,
            "interests": User.Interest.choices,
            "posted": request.POST,
        },
    )


@require_http_methods(["GET"])
def verify_email_page(request, token):
    user = consume_verification(token)
    if user is None:
        return render(request, "auth/verify.html", {"state": "invalid"})
    from authentication.services import complete_login

    complete_login(request, user, remember=False)
    confirmed = MFAConfiguration.objects.filter(user=user, confirmed=True).exists()
    if (user.mfa_required or user.is_staff or user.role == User.Role.ADMIN) and not confirmed:
        request.session["mfa_setup_required"] = True
    return redirect("verify-success")


@require_http_methods(["GET", "POST"])
def verify_success_page(request):
    notice = ""
    if request.method == "POST":
        resend_verification(request, request.POST.get("email"))
        notice = "If an unverified account exists, a new link is on its way."
    return render(request, "auth/verify.html", {"state": "success", "notice": notice})


@require_http_methods(["GET", "POST"])
def verify_pending_page(request):
    notice = ""
    if request.method == "POST":
        resend_verification(request, request.POST.get("email"))
        notice = "If an unverified account exists, a new link is on its way."
    return render(request, "auth/verify.html", {"state": "pending", "notice": notice})


@require_http_methods(["GET", "POST"])
def forgot_page(request):
    sent = False
    if request.method == "POST":
        request_password_reset(request, request.POST.get("email"))
        sent = True
    return render(request, "auth/forgot.html", {"sent": sent, "neutral": NEUTRAL_RESET})


@require_http_methods(["GET", "POST"])
def reset_page(request, token):
    error = ""
    done = False
    if request.method == "POST":
        try:
            reset_password(
                request,
                token,
                request.POST.get("password") or "",
                request.POST.get("confirm_password") or "",
            )
        except AuthError as exc:
            error = exc.message
        else:
            done = True
    return render(request, "auth/reset.html", {"error": error, "done": done})


@require_http_methods(["GET", "POST"])
def mfa_challenge_page(request):
    if request.user.is_authenticated:
        return destination(request)
    if not request.session.get("pre_mfa_user"):
        return redirect("login")
    error = ""
    if request.method == "POST":
        try:
            verify_mfa(request, request.POST.get("code"))
        except AuthError as exc:
            error = exc.message
        else:
            return destination(request)
    return render(request, "auth/mfa.html", {"error": error, "mode": "challenge"})


@login_required
@require_http_methods(["GET", "POST"])
def mfa_manage_page(request):
    error = ""
    codes = None
    password_done = False
    config = MFAConfiguration.objects.filter(user=request.user).first()
    enrollment = None
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "begin":
                enrollment = begin_mfa(request.user)
                config = MFAConfiguration.objects.filter(user=request.user).first()
            elif action == "confirm":
                codes = confirm_mfa(request.user, request.POST.get("code"))
                request.session.pop("mfa_setup_required", None)
                config = MFAConfiguration.objects.filter(user=request.user).first()
            elif action == "disable":
                disable_mfa(request, request.POST.get("password") or "", request.POST.get("code") or "")
                config = None
            elif action == "password":
                change_password(
                    request,
                    request.POST.get("current_password") or "",
                    request.POST.get("password") or "",
                    request.POST.get("confirm_password") or "",
                )
                password_done = True
        except AuthError as exc:
            error = exc.message
    if enrollment is None and config and not config.confirmed:
        secret = decrypt_secret(config.secret_encrypted)
        uri = pyotp.TOTP(secret).provisioning_uri(name=request.user.email, issuer_name="ZeroTrace Academy")
        enrollment = {"secret": secret, "qr": _qr_data_uri(uri)}
    events = SecurityEvent.objects.filter(user=request.user).order_by("-created_at")[:8]
    return render(
        request,
        "auth/security.html",
        {
            "error": error,
            "codes": codes,
            "config": config,
            "enrollment": enrollment,
            "password_done": password_done,
            "events": events,
            "setup_required": request.session.get("mfa_setup_required", False),
        },
    )


@require_http_methods(["GET", "POST"])
def recovery_page(request):
    return render(request, "auth/recovery.html", {"challenge": bool(request.session.get("pre_mfa_user"))})


@login_required
@require_http_methods(["GET", "POST"])
def logout_page(request):
    if request.method == "POST":
        logout_user(request)
        return redirect("login")
    return render(request, "auth/logout.html")


@login_required
@require_http_methods(["GET", "POST"])
def sessions_page(request):
    blocked = _guard_mfa(request)
    if blocked:
        return blocked
    notice = ""
    if request.method == "POST":
        try:
            if request.POST.get("action") == "all":
                logout_all(request)
                return redirect("login")
            current = revoke_session(request, request.POST.get("session_id"))
            if current:
                return redirect("login")
            notice = "That session was signed out."
        except AuthError as exc:
            notice = exc.message
    rows = UserSession.objects.filter(user=request.user, revoked_at__isnull=True).order_by("-last_seen")
    return render(
        request,
        "account/sessions.html",
        {"sessions": rows, "notice": notice, "current": request.session.session_key},
    )


def _google_error(request, message):
    request.session["auth_error"] = message
    target = "register" if request.session.pop("google_intent", "") == "register" else "login"
    return redirect(target)


@require_http_methods(["GET"])
def google_start(request):
    if request.user.is_authenticated:
        return destination(request)
    intent = "register" if request.GET.get("intent") == "register" else "login"
    request.session["google_intent"] = intent
    if not configured():
        return _google_error(request, "Google sign-in needs a client ID and secret in the server environment.")
    state = secrets.token_urlsafe(32)
    redirect_uri = request.build_absolute_uri("/auth/google/callback/")
    request.session["google_oauth_state"] = state
    request.session["google_redirect_uri"] = redirect_uri
    return redirect(authorization_url(redirect_uri, state))


@require_http_methods(["GET"])
def google_callback(request):
    if request.GET.get("error"):
        return _google_error(request, "Google sign-in was cancelled.")
    expected = request.session.pop("google_oauth_state", "")
    redirect_uri = request.session.pop("google_redirect_uri", "")
    sent = request.GET.get("state") or ""
    if not expected or not redirect_uri or not hmac.compare_digest(expected, sent):
        return _google_error(request, "Google sign-in could not be completed. Try again.")
    ip = client_ip(request)
    if too_many("google", ip_address=ip, bucket="login_ip", failures_only=False):
        record("lockout", request=request, detail={"action": "google"})
        return _google_error(request, "Too many attempts. Wait a few minutes and try again.")
    record_attempt("google", ip_address=ip, succeeded=False)
    try:
        profile = fetch_google_identity(request.GET.get("code") or "", redirect_uri)
        result = sign_in_with_google(request, profile)
    except AuthError as exc:
        return _google_error(request, exc.message)
    request.session.pop("google_intent", None)
    if result["state"] == "mfa":
        return redirect("mfa-challenge")
    return destination(request)
