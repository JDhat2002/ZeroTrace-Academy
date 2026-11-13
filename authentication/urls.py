from django.urls import path

from authentication import views

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("auth/google/", views.google_start, name="google-start"),
    path("auth/google/callback/", views.google_callback, name="google-callback"),
    path("register/", views.register_page, name="register"),
    path("verify-email/success/", views.verify_success_page, name="verify-success"),
    path("verify-email/pending/", views.verify_pending_page, name="verify-pending"),
    path("verify-email/<str:token>/", views.verify_email_page, name="verify-email"),
    path("forgot-password/", views.forgot_page, name="forgot-password"),
    path("reset-password/<str:token>/", views.reset_page, name="reset-password"),
    path("login/mfa/", views.mfa_challenge_page, name="mfa-challenge"),
    path("account/recovery/", views.recovery_page, name="account-recovery"),
    path("account/sessions/", views.sessions_page, name="account-sessions"),
    path("account/security/", views.mfa_manage_page, name="mfa-manage"),
    path("logout/", views.logout_page, name="logout"),
]
