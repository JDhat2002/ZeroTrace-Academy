from django.conf import settings
from django.db import models


class SecurityEvent(models.Model):
    class Kind(models.TextChoices):
        REGISTER = "register", "Registration"
        VERIFY = "verify", "Email verified"
        LOGIN = "login", "Login"
        LOGIN_FAILED = "login_failed", "Login failed"
        LOGOUT = "logout", "Logout"
        LOGOUT_ALL = "logout_all", "Logout all sessions"
        RESET_REQUEST = "reset_request", "Password reset requested"
        RESET = "reset", "Password reset"
        PASSWORD_CHANGED = "password_changed", "Password changed"
        MFA_ENABLED = "mfa_enabled", "MFA enabled"
        MFA_DISABLED = "mfa_disabled", "MFA disabled"
        MFA_FAILED = "mfa_failed", "MFA failed"
        SESSION_REVOKED = "session_revoked", "Session revoked"
        EMAIL_CHANGE = "email_change", "Email change"
        LOCKOUT = "lockout", "Throttled"
        SUSPICIOUS_LOGIN = "suspicious_login", "New sign-in location"
        GOOGLE = "google", "Google sign-in"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="security_events",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=256, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["kind", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.kind} {self.created_at:%Y-%m-%d %H:%M}"
