from django.urls import path

from profiles.api import profile_api

urlpatterns = [
    path("", profile_api, name="api-profile"),
]
