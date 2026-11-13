from django.urls import path

from profiles import views

urlpatterns = [
    path("dashboard/", views.dashboard_page, name="dashboard"),
    path("onboarding/", views.onboarding_page, name="onboarding"),
    path("account/profile/", views.profile_page, name="profile"),
]
