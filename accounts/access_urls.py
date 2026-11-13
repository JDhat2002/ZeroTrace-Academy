from django.urls import path

from accounts import api

urlpatterns = [
    path("pro/", api.pro_access, name="api-pro-access"),
    path("elite/", api.elite_access, name="api-elite-access"),
    path("instructor/", api.instructor_access, name="api-instructor-access"),
]
