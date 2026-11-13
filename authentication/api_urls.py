from django.urls import path

from authentication import api

urlpatterns = [
    path("register/", api.register, name="api-register"),
    path("login/", api.login_api, name="api-login"),
    path("logout/", api.logout_api, name="api-logout"),
    path("verify-email/", api.verify_email_api, name="api-verify-email"),
    path("resend-verification/", api.resend_api, name="api-resend"),
    path("forgot-password/", api.forgot_api, name="api-forgot"),
    path("reset-password/", api.reset_api, name="api-reset"),
    path("mfa/setup/", api.mfa_setup, name="api-mfa-setup"),
    path("mfa/verify/", api.mfa_verify, name="api-mfa-verify"),
    path("mfa/disable/", api.mfa_disable, name="api-mfa-disable"),
    path("username-availability/", api.username_api, name="api-username"),
]
