import io
import base64
import re
import secrets
from datetime import timedelta

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone
from PIL import Image

from accounts.countries import COUNTRY_CODES
from accounts.models import User
from accounts.validators import password_problems, username_problems
from audit.services import client_ip, record, user_agent
from authentication.exceptions import AuthError
from authentication.limits import clear_failures, record_attempt, too_many
from authentication.models import (
    EmailVerification,
    GoogleAccount,
    LoginAttempt,
    MFAConfiguration,
    PasswordResetRequest,
    RecoveryCode,
    UserSession,
)
from authentication.tokens import (
    decrypt_secret,
    encrypt_secret,
    hash_recovery_code,
    hash_token,
    new_token,
    recovery_codes,
)
from notifications.mailer import (
    send_existing_account,
    send_mfa_disabled,
    send_mfa_enabled,
    send_new_login,
    send_password_changed,
    send_password_reset,
    send_security_alert,
    send_verification,
    send_welcome,
)

NEUTRAL_RESET = "If an account exists for that email, a reset message is on its way."
NEUTRAL_REGISTER = "Check your email for the next step. If the address can be used, a verification link is waiting."


def _ip(request):
    return client_ip(request)


def register_user(request, data):
    ip = _ip(request)
    if too_many("register", ip_address=ip, bucket="register_ip", failures_only=False):
        record("lockout", request=request, detail={"action": "register"})
        raise AuthError("Too many attempts. Wait a while and try again.", status=429, code="throttled")
    record_attempt("register", email=data.get("email", ""), ip_address=ip, succeeded=False)

    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    password = data.get("password") or ""
    confirm = data.get("confirm_password") or ""
    country = (data.get("country") or "").upper()
    interest = data.get("learning_interest") or ""

    if not full_name or len(full_name) > 150:
        raise AuthError("Enter your full name.", field="full_name")
    username_error = username_problems(username)
    if username_error:
        raise AuthError(username_error, field="username")
    if not email or "@" not in email:
        raise AuthError("Enter a valid email address.", field="email")
    if password != confirm:
        raise AuthError("The passwords do not match.", field="confirm_password")
    problems = password_problems(password, username=username, email=email, full_name=full_name)
    if problems:
        raise AuthError(" ".join(problems), field="password")
    if country not in COUNTRY_CODES:
        raise AuthError("Choose a country from the list.", field="country")
    if interest not in User.Interest.values:
        raise AuthError("Choose a learning interest.", field="learning_interest")
    if not data.get("accept_terms"):
        raise AuthError("Accept the Terms and Privacy Policy to continue.", field="accept_terms")

    existing = User.objects.filter(email=email).first()
    if existing:
        if existing.email_verified_at:
            send_existing_account(existing)
        else:
            _issue_verification(request, existing)
        record("register", request=request, user=existing, detail={"duplicate": True})
        return {"neutral": True, "email": email}

    if User.objects.filter(username__iexact=username).exists():
        raise AuthError("That username is taken. Choose another.", field="username")

    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            country=country,
            learning_interest=interest,
            is_active=False,
            accepted_terms_at=timezone.now(),
        )
        _issue_verification(request, user)
    record("register", request=request, user=user, detail={"duplicate": False})
    request.session["pending_email"] = email
    return {"neutral": True, "email": email}


def _issue_verification(request, user, purpose=EmailVerification.Purpose.VERIFY, new_email=""):
    raw, digest = new_token()
    EmailVerification.objects.filter(user=user, purpose=purpose, used_at__isnull=True).update(used_at=timezone.now())
    EmailVerification.objects.create(
        user=user,
        purpose=purpose,
        token_hash=digest,
        new_email=new_email,
        expires_at=timezone.now() + timedelta(hours=settings.VERIFICATION_TTL_HOURS),
    )
    link = request.build_absolute_uri(f"/verify-email/{raw}/")
    recipient = type("Recipient", (), {"email": new_email or user.email, "full_name": user.full_name})()
    send_verification(recipient, link)
    return raw


def resend_verification(request, email):
    ip = _ip(request)
    email = (email or "").strip().lower()
    if too_many("resend", ip_address=ip, bucket="reset", failures_only=False):
        return
    record_attempt("resend", email=email, ip_address=ip, succeeded=False)
    user = User.objects.filter(email=email, email_verified_at__isnull=True).first()
    if user:
        _issue_verification(request, user)


def consume_verification(raw_token):
    digest = hash_token(raw_token)
    with transaction.atomic():
        row = (
            EmailVerification.objects.select_for_update()
            .select_related("user")
            .filter(token_hash=digest, used_at__isnull=True, expires_at__gt=timezone.now())
            .first()
        )
        if row is None:
            return None
        row.used_at = timezone.now()
        row.save(update_fields=["used_at"])
        user = row.user
        if row.purpose == EmailVerification.Purpose.EMAIL_CHANGE:
            if User.objects.filter(email=row.new_email).exclude(pk=user.pk).exists():
                return None
            user.email = row.new_email
        user.is_active = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email", "is_active", "email_verified_at"])
    record("verify", user=user)
    send_welcome(user)
    return user


def login_user(request, email, password, remember):
    email = (email or "").strip().lower()
    ip = _ip(request)
    if too_many("login", email=email, bucket="login_email") or too_many("login", ip_address=ip, bucket="login_ip"):
        record_attempt("login", email=email, ip_address=ip, succeeded=False)
        record("lockout", request=request, detail={"action": "login"})
        raise AuthError("Too many attempts. Wait a few minutes and try again.", status=429, code="throttled")

    user = User.objects.filter(email=email).first()
    if user is None or not user.check_password(password):
        record_attempt("login", email=email, ip_address=ip, succeeded=False)
        record("login_failed", request=request, user=user)
        raise AuthError("Invalid email or password.", code="invalid_credentials")
    if not user.is_active or not user.email_verified_at:
        record_attempt("login", email=email, ip_address=ip, succeeded=False)
        raise AuthError("Verify your email before signing in. You can resend the link from the verification page.", code="unverified")

    clear_failures("login", email)
    record_attempt("login", email=email, ip_address=ip, succeeded=True)
    return begin_authenticated_session(request, user, remember)


def begin_authenticated_session(request, user, remember):
    mfa = getattr(user, "mfa", None)
    if mfa and mfa.confirmed:
        request.session["pre_mfa_user"] = user.pk
        request.session["pre_mfa_remember"] = bool(remember)
        return {"state": "mfa"}
    if user.mfa_required or user.role == User.Role.ADMIN or user.is_staff:
        complete_login(request, user, remember)
        request.session["mfa_setup_required"] = True
        return {"state": "mfa_setup"}
    complete_login(request, user, remember)
    return {"state": "ok"}


def sign_in_with_google(request, profile):
    subject = str(profile.get("sub") or "").strip()
    email = str(profile.get("email") or "").strip().lower()
    verified = profile.get("email_verified") is True or profile.get("email_verified") == "true"
    if not subject or "@" not in email or not verified:
        raise AuthError("Google did not confirm that email address.", code="google_unverified")
    full_name = str(profile.get("name") or "").strip()[:150] or email.split("@", 1)[0]

    with transaction.atomic():
        link = GoogleAccount.objects.select_related("user").filter(subject=subject).first()
        if link:
            user = link.user
        else:
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.create_user(
                    email=email,
                    username=_google_username(email),
                    password=None,
                    full_name=full_name,
                    country="",
                    learning_interest=User.Interest.EXPLORE,
                    is_active=True,
                    email_verified_at=timezone.now(),
                    accepted_terms_at=timezone.now(),
                )
                send_welcome(user)
                record("register", request=request, user=user, detail={"provider": "google"})
            else:
                if GoogleAccount.objects.filter(user=user).exclude(subject=subject).exists():
                    raise AuthError("This email is already linked to a different Google account.", code="google_conflict")
                if not user.email_verified_at:
                    user.set_unusable_password()
                    user.is_active = True
                    user.email_verified_at = timezone.now()
                    user.save(update_fields=["password", "is_active", "email_verified_at"])
                    _revoke_all_sessions(user)
                    record("verify", request=request, user=user, detail={"provider": "google"})
                elif not user.is_active:
                    raise AuthError("This account cannot be used.", status=403, code="inactive")
            GoogleAccount.objects.create(user=user, subject=subject, email=email)
    if not user.is_active or not user.email_verified_at:
        raise AuthError("This account cannot be used.", status=403, code="inactive")
    record("google", request=request, user=user)
    return begin_authenticated_session(request, user, False)


def _google_username(email):
    local = re.sub(r"[^A-Za-z0-9_]", "", email.split("@", 1)[0])
    if not local[:1].isalpha():
        local = f"m{local}"
    local = (local or "member")[:20]
    if len(local) < 3:
        local = f"{local}user"[:20]
    candidate = local
    suffix = 2
    while username_problems(candidate) or User.objects.filter(username__iexact=candidate).exists():
        extra = str(suffix)
        candidate = f"{local[: 30 - len(extra)]}{extra}"
        suffix += 1
        if suffix > 100:
            candidate = f"m{secrets.token_hex(4)}"
            if not User.objects.filter(username__iexact=candidate).exists():
                return candidate
    return candidate


def verify_mfa(request, code):
    user_id = request.session.get("pre_mfa_user")
    if not user_id:
        raise AuthError("Sign in again before entering a verification code.", code="mfa_session")
    user = User.objects.filter(pk=user_id).first()
    ip = _ip(request)
    if user is None:
        raise AuthError("Sign in again before entering a verification code.", code="mfa_session")
    if too_many("mfa", email=user.email, bucket="mfa"):
        record("lockout", request=request, user=user, detail={"action": "mfa"})
        raise AuthError("Too many attempts. Wait a few minutes and try again.", status=429, code="throttled")
    if not _code_matches(user, code):
        record_attempt("mfa", email=user.email, ip_address=ip, succeeded=False)
        record("mfa_failed", request=request, user=user)
        raise AuthError("That code is not valid.", field="code")
    clear_failures("mfa", user.email)
    remember = request.session.pop("pre_mfa_remember", False)
    request.session.pop("pre_mfa_user", None)
    complete_login(request, user, remember)
    return user


def _code_matches(user, code):
    mfa = getattr(user, "mfa", None)
    if mfa and mfa.confirmed and code and pyotp.TOTP(decrypt_secret(mfa.secret_encrypted)).verify(code.strip(), valid_window=1):
        return True
    digest = hash_recovery_code(code or "")
    with transaction.atomic():
        row = RecoveryCode.objects.select_for_update().filter(user=user, code_hash=digest, used_at__isnull=True).first()
        if row is None:
            return False
        row.used_at = timezone.now()
        row.save(update_fields=["used_at"])
    return True


def complete_login(request, user, remember, event=True):
    known_ip = UserSession.objects.filter(user=user, ip_address=_ip(request), revoked_at__isnull=True).exists()
    login(request, user)
    request.session.set_expiry(settings.REMEMBER_SECONDS if remember else settings.STANDARD_SESSION_SECONDS)
    _track_session(request, user)
    if event:
        record("login", request=request, user=user)
    if event and not known_ip:
        record("suspicious_login", request=request, user=user)
        send_new_login(user, _ip(request))


def logout_user(request):
    key = request.session.session_key
    user = request.user if request.user.is_authenticated else None
    if key:
        UserSession.objects.filter(session_key=key, revoked_at__isnull=True).update(revoked_at=timezone.now())
    if user and user.is_authenticated:
        record("logout", request=request, user=user)
    logout(request)


def logout_all(request):
    user = request.user
    keys = list(UserSession.objects.filter(user=user, revoked_at__isnull=True).values_list("session_key", flat=True))
    UserSession.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())
    Session.objects.filter(session_key__in=keys).delete()
    record("logout_all", request=request, user=user)
    logout(request)


def revoke_session(request, session_id):
    row = UserSession.objects.filter(user=request.user, pk=session_id, revoked_at__isnull=True).first()
    if row is None:
        raise AuthError("That session is not active.", status=404, code="not_found")
    row.revoked_at = timezone.now()
    row.save(update_fields=["revoked_at"])
    Session.objects.filter(session_key=row.session_key).delete()
    record("session_revoked", request=request, user=request.user)
    if row.session_key == request.session.session_key:
        logout(request)
        return True
    return False


def request_password_reset(request, email):
    email = (email or "").strip().lower()
    ip = _ip(request)
    limited = too_many("reset", email=email, bucket="reset", failures_only=False) or too_many(
        "reset", ip_address=ip, bucket="reset", failures_only=False
    )
    record_attempt("reset", email=email, ip_address=ip, succeeded=not limited)
    if limited:
        return
    user = User.objects.filter(email=email).first()
    record("reset_request", request=request, user=user)
    if user is None:
        return
    if not user.email_verified_at:
        _issue_verification(request, user)
        return
    raw, digest = new_token()
    PasswordResetRequest.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    PasswordResetRequest.objects.create(
        user=user,
        token_hash=digest,
        expires_at=timezone.now() + timedelta(minutes=settings.PASSWORD_RESET_TTL_MINUTES),
    )
    send_password_reset(user, request.build_absolute_uri(f"/reset-password/{raw}/"))


def reset_password(request, raw_token, password, confirm):
    if password != confirm:
        raise AuthError("The passwords do not match.", field="confirm_password")
    digest = hash_token(raw_token)
    with transaction.atomic():
        row = (
            PasswordResetRequest.objects.select_for_update()
            .select_related("user")
            .filter(token_hash=digest, used_at__isnull=True, expires_at__gt=timezone.now())
            .first()
        )
        if row is None:
            raise AuthError("This link is invalid or has expired.", code="expired")
        user = row.user
        problems = password_problems(password, username=user.username, email=user.email, full_name=user.full_name)
        if problems:
            raise AuthError(" ".join(problems), field="password")
        row.used_at = timezone.now()
        row.save(update_fields=["used_at"])
        user.set_password(password)
        user.save(update_fields=["password"])
        PasswordResetRequest.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    _revoke_all_sessions(user)
    send_password_changed(user)
    record("reset", request=request, user=user)
    return user


def change_password(request, current, password, confirm):
    user = request.user
    if not user.check_password(current):
        raise AuthError("Password confirmation did not match.", field="current_password", status=403)
    if password != confirm:
        raise AuthError("The passwords do not match.", field="confirm_password")
    problems = password_problems(password, username=user.username, email=user.email, full_name=user.full_name)
    if problems:
        raise AuthError(" ".join(problems), field="password")
    previous = list(UserSession.objects.filter(user=user, revoked_at__isnull=True).values_list("session_key", flat=True))
    user.set_password(password)
    user.save(update_fields=["password"])
    login(request, user)
    UserSession.objects.filter(session_key__in=previous).update(revoked_at=timezone.now())
    Session.objects.filter(session_key__in=previous).delete()
    _track_session(request, user)
    send_password_changed(user)
    record("password_changed", request=request, user=user)


def _track_session(request, user):
    if not request.session.session_key:
        request.session.save()
    if not request.session.session_key:
        return
    UserSession.objects.update_or_create(
        session_key=request.session.session_key,
        defaults={
            "user": user,
            "ip_address": _ip(request),
            "user_agent": user_agent(request),
            "revoked_at": None,
            "last_seen": timezone.now(),
        },
    )


def _revoke_all_sessions(user):
    keys = list(UserSession.objects.filter(user=user, revoked_at__isnull=True).values_list("session_key", flat=True))
    UserSession.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())
    Session.objects.filter(session_key__in=keys).delete()


def begin_mfa(user):
    secret = pyotp.random_base32()
    config, _created = MFAConfiguration.objects.get_or_create(
        user=user,
        defaults={"secret_encrypted": encrypt_secret(secret)},
    )
    if config.confirmed:
        raise AuthError("Two-factor authentication is already on.", code="mfa_enabled")
    config.secret_encrypted = encrypt_secret(secret)
    config.confirmed = False
    config.enabled_at = None
    config.save()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="ZeroTrace Academy")
    return {"secret": secret, "otpauth": uri, "qr": _qr_data_uri(uri)}


def confirm_mfa(user, code):
    config = getattr(user, "mfa", None)
    if config is None or config.confirmed:
        raise AuthError("Start two-factor setup before confirming a code.", code="mfa_missing")
    if too_many("mfa", email=user.email, bucket="mfa"):
        record("lockout", user=user, detail={"action": "mfa"})
        raise AuthError("Too many attempts. Wait a few minutes and try again.", status=429, code="throttled")
    if not pyotp.TOTP(decrypt_secret(config.secret_encrypted)).verify((code or "").strip(), valid_window=1):
        record_attempt("mfa", email=user.email, succeeded=False)
        record("mfa_failed", user=user)
        raise AuthError("That code is not valid.", field="code")
    clear_failures("mfa", user.email)
    config.confirmed = True
    config.enabled_at = timezone.now()
    config.save(update_fields=["confirmed", "enabled_at"])
    codes = recovery_codes()
    RecoveryCode.objects.filter(user=user, used_at__isnull=True).delete()
    RecoveryCode.objects.bulk_create(
        [RecoveryCode(user=user, code_hash=hash_recovery_code(item)) for item in codes]
    )
    send_mfa_enabled(user)
    record("mfa_enabled", user=user)
    return codes


def disable_mfa(request, password, code):
    user = request.user
    if user.mfa_required or user.role == User.Role.ADMIN or user.is_staff:
        raise AuthError("Administrator accounts must keep two-factor authentication on.", status=403, code="mfa_required")
    if too_many("mfa", email=user.email, bucket="mfa"):
        raise AuthError("Too many attempts. Wait a few minutes and try again.", status=429, code="throttled")
    if not user.check_password(password) or not _code_matches(user, code):
        record_attempt("mfa", email=user.email, ip_address=_ip(request), succeeded=False)
        raise AuthError("Password or verification code did not match.", status=403, code="invalid")
    MFAConfiguration.objects.filter(user=user).delete()
    RecoveryCode.objects.filter(user=user).delete()
    send_mfa_disabled(user)
    record("mfa_disabled", request=request, user=user)
    send_security_alert(user, "Two-factor authentication was turned off after a password check.")


def request_email_change(request, new_email):
    new_email = (new_email or "").strip().lower()
    if "@" not in new_email:
        raise AuthError("Enter a valid email address.", field="email")
    if new_email == request.user.email:
        return
    owner = User.objects.filter(email=new_email).exclude(pk=request.user.pk).first()
    if owner:
        send_existing_account(owner)
        return
    _issue_verification(request, request.user, purpose=EmailVerification.Purpose.EMAIL_CHANGE, new_email=new_email)
    record("email_change", request=request, user=request.user)


def username_available(username):
    error = username_problems(username)
    if error:
        return False
    return not User.objects.filter(username__iexact=username).exists()


def _qr_data_uri(payload):
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def validate_avatar(uploaded):
    if uploaded.size > 2 * 1024 * 1024:
        raise AuthError("Use an image smaller than 2 MB.", field="avatar")
    try:
        image = Image.open(uploaded)
        image_format = (image.format or "").upper()
        image.verify()
    except AuthError:
        raise
    except Exception as exc:
        raise AuthError("Upload a PNG, JPEG, or WebP image.", field="avatar") from exc
    uploaded.seek(0)
    if image_format not in {"PNG", "JPEG", "WEBP"}:
        raise AuthError("Upload a PNG, JPEG, or WebP image.", field="avatar")
    return uploaded


# Imported for tests that inspect failed attempts.
_ = LoginAttempt
