from django.urls import path

from profiles.api import onboarding_api

urlpatterns = [
    path("", onboarding_api, name="api-onboarding"),
]
