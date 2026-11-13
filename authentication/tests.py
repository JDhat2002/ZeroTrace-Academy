import re
from datetime import timedelta

import pyotp
from django.contrib.sessions.models import Session
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from authentication.models import EmailVerification, MFAConfiguration, RecoveryCode, UserSession
from authentication.tokens import hash_recovery_code, hash_token

PASSWORD = "Correct-Horse-1"
NEW_PASSWORD = "Different-Horse-2"


def payload(**overrides):
    data = {
        "full_name": "Ada Lovelace",
        "username": "ada",
        "email": "ada@example.com",
        "password": PASSWORD,
        "confirm_password": PASSWORD,
        "country": "IN",
        "learning_interest": "explore",
        "accept_terms": True,
    }
    data.update(overrides)
    return data


def verified_user(**overrides):
    data = payload(**overrides)
    user = User.objects.create_user(
        email=data["email"],
        username=data["username"],
        password=data["password"],
        full_name=data["full_name"],
        country=data["country"],
        learning_interest=data["learning_interest"],
        is_active=True,
    )
    user.email_verified_at = timezone.now()
    user.onboarding_completed_at = timezone.now()
    user.save()
    return user


def token_from_mail(kind):
    body = mail.outbox[-1].body
    match = re.search(rf"/{kind}/([^/\s]+)/", body)
    assert match, body
    return match.group(1)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.api = APIClient()

    def test_register_verify_and_page_copy(self):
        response = self.client.get("/login/")
        self.assertContains(response, "YOUR SECURITY JOURNEY STARTS HERE.")
        response = self.client.get("/register/")
        self.assertContains(response, "CREATE YOUR ZEROTRACE ACCOUNT.")
        created = self.api.post("/api/auth/register/", payload(), format="json")
        self.assertEqual(created.status_code, 201)
        user = User.objects.get(email="ada@example.com")
        self.assertFalse(user.is_active)
        self.assertIsNone(user.email_verified_at)
        self.assertFalse(user.password.startswith(PASSWORD))
        token = token_from_mail("verify-email")
        self.assertFalse(EmailVerification.objects.filter(token_hash=token).exists())
        self.assertNotIn(PASSWORD, mail.outbox[-1].body)
        self.assertNotIn(PASSWORD, mail.outbox[-1].alternatives[0][0])
        verified = self.api.post("/api/auth/verify-email/", {"token": token}, format="json")
        self.assertEqual(verified.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        reused = self.api.post("/api/auth/verify-email/", {"token": token}, format="json")
        self.assertEqual(reused.status_code, 400)
        self.assertEqual(reused.data["detail"], "This link is invalid or has expired.")

    def test_duplicate_email_is_silent_and_username_conflict_is_not(self):
        self.api.post("/api/auth/register/", payload(), format="json")
        again = self.api.post(
            "/api/auth/register/",
            payload(username="ada_other", password=PASSWORD, confirm_password=PASSWORD),
            format="json",
        )
        self.assertEqual(again.status_code, 201)
        self.assertEqual(again.data["detail"], "Check your email for the next step.")
        self.assertEqual(User.objects.filter(email="ada@example.com").count(), 1)
        taken = self.api.post("/api/auth/register/", payload(email="other@example.com"), format="json")
        self.assertEqual(taken.status_code, 400)
        self.assertEqual(taken.data["field"], "username")
        self.assertFalse(User.objects.filter(email="other@example.com").exists())

    def test_weak_password_is_rejected(self):
        response = self.api.post("/api/auth/register/", payload(password="password123", confirm_password="password123"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["field"], "password")
        self.assertFalse(User.objects.exists())

    def test_login_errors_do_not_reveal_unknown_accounts(self):
        user = verified_user()
        missing = self.api.post("/api/auth/login/", {"email": "missing@example.com", "password": PASSWORD}, format="json")
        wrong = self.api.post("/api/auth/login/", {"email": user.email, "password": "Wrong-Horse-9!"}, format="json")
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.data, wrong.data)
        self.assertEqual(missing.data["detail"], "Invalid email or password.")
        user.is_active = False
        user.email_verified_at = None
        user.save(update_fields=["is_active", "email_verified_at"])
        unverified = self.api.post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
        self.assertEqual(unverified.data["code"], "unverified")

    def test_expired_verification_token(self):
        self.api.post("/api/auth/register/", payload(), format="json")
        token = token_from_mail("verify-email")
        EmailVerification.objects.filter(token_hash=hash_token(token)).update(expires_at=timezone.now() - timedelta(minutes=1))
        response = self.api.post("/api/auth/verify-email/", {"token": token}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.get(email="ada@example.com").is_active)

    def test_password_reset_is_neutral_single_use_and_expiring(self):
        user = verified_user()
        unknown = self.api.post("/api/auth/forgot-password/", {"email": "missing@example.com"}, format="json")
        known = self.api.post("/api/auth/forgot-password/", {"email": user.email}, format="json")
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.data, known.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(PASSWORD, mail.outbox[0].body)
        token = token_from_mail("reset-password")
        updated = self.api.post(
            "/api/auth/reset-password/",
            {"token": token, "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertNotIn(NEW_PASSWORD, mail.outbox[-1].body)
        reused = self.api.post(
            "/api/auth/reset-password/",
            {"token": token, "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD},
            format="json",
        )
        self.assertEqual(reused.status_code, 400)
        self.api.post("/api/auth/forgot-password/", {"email": user.email}, format="json")
        expired = token_from_mail("reset-password")
        from authentication.models import PasswordResetRequest

        PasswordResetRequest.objects.filter(token_hash=hash_token(expired)).update(expires_at=timezone.now() - timedelta(minutes=1))
        response = self.api.post(
            "/api/auth/reset-password/",
            {"token": expired, "password": "Another-Horse-3", "confirm_password": "Another-Horse-3"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "This link is invalid or has expired.")

    def test_login_logout_sessions_and_expiry(self):
        user = verified_user()
        user.onboarding_completed_at = None
        user.save(update_fields=["onboarding_completed_at"])
        response = self.client.post("/login/", {"email": "ada@example.com", "password": PASSWORD})
        self.assertRedirects(response, "/onboarding/")
        user.onboarding_completed_at = timezone.now()
        user.save(update_fields=["onboarding_completed_at"])
        self.assertEqual(self.client.get("/dashboard/").status_code, 200)
        self.assertContains(self.client.get("/account/sessions/"), "This device")
        row = UserSession.objects.get(user=user)
        revoked = self.client.post("/account/sessions/", {"session_id": row.pk})
        self.assertRedirects(revoked, "/login/")
        self.assertRedirects(self.client.get("/dashboard/"), "/login/?next=/dashboard/")

        signed = self.api.post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
        self.assertEqual(signed.data["state"], "ok")
        self.assertEqual(self.api.get("/api/sessions/").status_code, 200)
        self.api.post("/api/sessions/logout-all/")
        self.assertEqual(self.api.get("/api/profile/").status_code, 403)

        self.client.post("/login/", {"email": user.email, "password": PASSWORD})
        stored = Session.objects.get(session_key=self.client.session.session_key)
        stored.expire_date = timezone.now() - timedelta(hours=1)
        stored.save(update_fields=["expire_date"])
        self.assertRedirects(self.client.get("/dashboard/"), "/login/?next=/dashboard/")

    def test_login_is_rate_limited(self):
        verified_user()
        for _ in range(8):
            response = self.api.post("/api/auth/login/", {"email": "ada@example.com", "password": "Wrong-Horse-9!"}, format="json")
            self.assertEqual(response.status_code, 400)
        blocked = self.api.post("/api/auth/login/", {"email": "ada@example.com", "password": PASSWORD}, format="json")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.data["detail"], "Too many attempts. Wait a few minutes and try again.")

    def test_csrf_is_enforced_on_login(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/login/", {"email": "ada@example.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 403)

    def test_mfa_setup_invalid_code_and_single_use_recovery(self):
        user = verified_user()
        self.api.force_login(user)
        started = self.api.post("/api/auth/mfa/setup/")
        self.assertEqual(started.status_code, 200)
        secret = started.data["secret"]
        self.assertNotEqual(MFAConfiguration.objects.get(user=user).secret_encrypted, secret)
        bad = self.api.post("/api/auth/mfa/verify/", {"code": "000000"}, format="json")
        self.assertEqual(bad.status_code, 400)
        code = pyotp.TOTP(secret).now()
        confirmed = self.api.post("/api/auth/mfa/verify/", {"code": code}, format="json")
        self.assertEqual(confirmed.status_code, 200)
        recovery = confirmed.data["recovery_codes"]
        self.assertEqual(len(recovery), 10)
        self.assertFalse(RecoveryCode.objects.filter(code_hash=recovery[0]).exists())
        self.assertTrue(RecoveryCode.objects.filter(code_hash=hash_recovery_code(recovery[0])).exists())
        self.assertNotIn(secret, mail.outbox[-1].body)
        self.assertNotIn(recovery[0], mail.outbox[-1].body)
        self.api.post("/api/auth/logout/")
        challenge = self.api.post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
        self.assertEqual(challenge.data["state"], "mfa")
        invalid = self.api.post("/api/auth/mfa/verify/", {"code": "000000"}, format="json")
        self.assertEqual(invalid.status_code, 400)
        accepted = self.api.post("/api/auth/mfa/verify/", {"code": recovery[0]}, format="json")
        self.assertEqual(accepted.status_code, 200)
        self.api.post("/api/auth/logout/")
        self.api.post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json")
        reused = self.api.post("/api/auth/mfa/verify/", {"code": recovery[0]}, format="json")
        self.assertEqual(reused.status_code, 400)

    def test_administrators_must_keep_mfa(self):
        user = verified_user()
        user.role = User.Role.ADMIN
        user.save()
        response = self.client.post("/login/", {"email": user.email, "password": PASSWORD})
        self.assertRedirects(response, "/account/security/")
        self.assertRedirects(self.client.get("/dashboard/"), "/account/security/")
        denied = self.client.post("/account/security/", {"action": "disable", "password": PASSWORD, "code": "000000"})
        self.assertContains(denied, "Administrator accounts must keep two-factor authentication on.")

    def test_profile_permissions_and_onboarding(self):
        user = verified_user()
        self.api.force_login(user)
        blocked = self.api.patch("/api/profile/", {"role": "admin", "membership": "elite", "full_name": "Admin Ada"}, format="json")
        self.assertEqual(blocked.status_code, 403)
        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.MEMBER)
        self.assertEqual(user.membership, User.Membership.FREE)
        self.assertNotEqual(user.full_name, "Admin Ada")
        renamed = self.api.patch("/api/profile/", {"full_name": "Ada King"}, format="json")
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.data["full_name"], "Ada King")
        self.assertEqual(renamed.data["membership"], "free")
        self.assertEqual(self.api.get("/api/access/elite/").status_code, 403)
        self.assertEqual(self.api.get("/api/access/instructor/").status_code, 403)
        user.membership = User.Membership.ELITE
        user.role = User.Role.INSTRUCTOR
        user.save(update_fields=["membership", "role"])
        self.assertEqual(self.api.get("/api/access/elite/").status_code, 200)
        self.assertEqual(self.api.get("/api/access/pro/").status_code, 200)
        self.assertEqual(self.api.get("/api/access/instructor/").status_code, 200)
        user.membership = User.Membership.FREE
        user.role = User.Role.MEMBER
        user.onboarding_completed_at = None
        user.save()
        guided = self.api.post(
            "/api/onboarding/",
            {
                "experience_level": "beginner",
                "interests": ["soc"],
                "objective": "soc",
                "daily_minutes": 30,
                "complete": True,
            },
            format="json",
        )
        self.assertEqual(guided.status_code, 200)
        self.assertEqual(guided.data["recommendation"]["key"], "soc")
        self.assertTrue(guided.data["completed"])
        user.refresh_from_db()
        user.onboarding_completed_at = None
        user.save(update_fields=["onboarding_completed_at"])
        skipped = self.api.post("/api/onboarding/", {"skip": True}, format="json")
        self.assertTrue(skipped.data["completed"])

    def test_marketing_login_links_resolve(self):
        from django.conf import settings

        homepage = (settings.BASE_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/login/"', homepage)
        self.assertIn('href="/register/"', homepage)
        self.assertNotIn('href="login.html"', homepage)
        self.assertEqual(self.client.get("/login.html").status_code, 302)
        self.assertEqual(self.client.get("/register.html").status_code, 302)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class GoogleSignInTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_google_buttons_are_on_both_pages(self):
        self.assertContains(self.client.get("/login/"), "Sign in with Google")
        self.assertContains(self.client.get("/register/"), "Sign up with Google")

    def test_unconfigured_google_explains_what_is_missing(self):
        response = self.client.get("/auth/google/", follow=True)
        self.assertContains(response, "client ID and secret")
        self.assertEqual(response.request["PATH_INFO"], "/login/")

    @override_settings(GOOGLE_CLIENT_ID="client", GOOGLE_CLIENT_SECRET="secret")
    def test_start_redirects_to_google(self):
        response = self.client.get("/auth/google/?intent=register")
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])
        self.assertIn("client_id=client", response["Location"])
        self.assertNotIn("secret", response["Location"])

    @override_settings(GOOGLE_CLIENT_ID="client", GOOGLE_CLIENT_SECRET="secret")
    def test_callback_creates_and_links_accounts(self):
        from unittest.mock import patch

        from authentication.models import GoogleAccount

        self.client.get("/auth/google/")
        state = self.client.session["google_oauth_state"]
        profile = {"sub": "google-ada", "email": "ada@example.com", "email_verified": True, "name": "Ada Lovelace"}
        with patch("authentication.views.fetch_google_identity", return_value=profile):
            response = self.client.get("/auth/google/callback/", {"code": "code", "state": state})
        self.assertRedirects(response, "/onboarding/")
        user = User.objects.get(email="ada@example.com")
        self.assertTrue(user.email_verified)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.google_account.subject, "google-ada")
        self.assertNotIn(PASSWORD, mail.outbox[-1].body)

        self.client.post("/logout/")
        self.client.get("/auth/google/")
        state = self.client.session["google_oauth_state"]
        with patch("authentication.views.fetch_google_identity", return_value=profile):
            again = self.client.get("/auth/google/callback/", {"code": "code", "state": state})
        self.assertRedirects(again, "/onboarding/")
        self.assertEqual(GoogleAccount.objects.filter(subject="google-ada").count(), 1)

        self.client.post("/logout/")
        rejected = self.client.get("/auth/google/callback/", {"code": "code", "state": "tampered"})
        self.assertRedirects(rejected, "/login/")

    @override_settings(GOOGLE_CLIENT_ID="client", GOOGLE_CLIENT_SECRET="secret")
    def test_google_links_a_verified_account_and_replaces_an_unverified_password(self):
        from unittest.mock import patch

        verified = verified_user()
        self.client.get("/auth/google/")
        state = self.client.session["google_oauth_state"]
        with patch(
            "authentication.views.fetch_google_identity",
            return_value={"sub": "sub-verified", "email": verified.email, "email_verified": True, "name": "Ada Lovelace"},
        ):
            response = self.client.get("/auth/google/callback/", {"code": "code", "state": state})
        self.assertRedirects(response, "/dashboard/")
        verified.refresh_from_db()
        self.assertTrue(verified.has_usable_password())
        self.assertEqual(verified.google_account.subject, "sub-verified")

        pending = verified_user(email="pending@example.com", username="pending")
        pending.is_active = False
        pending.email_verified_at = None
        pending.save(update_fields=["is_active", "email_verified_at"])
        self.client.post("/logout/")
        self.client.get("/auth/google/")
        state = self.client.session["google_oauth_state"]
        with patch(
            "authentication.views.fetch_google_identity",
            return_value={"sub": "sub-pending", "email": pending.email, "email_verified": True, "name": "Pending User"},
        ):
            response = self.client.get("/auth/google/callback/", {"code": "code", "state": state})
        self.assertRedirects(response, "/dashboard/")
        pending.refresh_from_db()
        self.assertTrue(pending.email_verified)
        self.assertFalse(pending.has_usable_password())

    @override_settings(GOOGLE_CLIENT_ID="client", GOOGLE_CLIENT_SECRET="secret")
    def test_unconfirmed_google_email_and_mfa_are_enforced(self):
        from unittest.mock import patch

        from authentication.models import MFAConfiguration
        from authentication.tokens import encrypt_secret

        self.client.get("/auth/google/")
        state = self.client.session["google_oauth_state"]
        with patch(
            "authentication.views.fetch_google_identity",
            return_value={"sub": "nope", "email": "ada@example.com", "email_verified": False, "name": "Ada"},
        ):
            response = self.client.get("/auth/google/callback/", {"code": "code", "state": state})
        self.assertRedirects(response, "/login/")
        self.assertFalse(User.objects.filter(email="ada@example.com").exists())

        user = verified_user()
        MFAConfiguration.objects.create(user=user, secret_encrypted=encrypt_secret("JBSWY3DPEHPK3PXP"), confirmed=True)
        self.client.get("/auth/google/")
        state = self.client.session["google_oauth_state"]
        with patch(
            "authentication.views.fetch_google_identity",
            return_value={"sub": "mfa-user", "email": user.email, "email_verified": True, "name": "Ada Lovelace"},
        ):
            response = self.client.get("/auth/google/callback/", {"code": "code", "state": state})
        self.assertRedirects(response, "/login/mfa/")
        self.assertFalse(response.wsgi_request.user.is_authenticated)
