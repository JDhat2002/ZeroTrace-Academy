from django.urls import path

from workspace import api

urlpatterns = [
    path("", api.dashboard_api, name="api-dashboard"),
    path("enrol/", api.enrol_api, name="api-enrol"),
    path("progress/", api.progress_api, name="api-progress"),
    path("membership/", api.membership_api, name="api-membership"),
    path("notifications/", api.notifications_api, name="api-notifications"),
    path("labs/start/", api.lab_api, name="api-lab-start"),
    path("tools/launch/", api.tool_api, name="api-tool-launch"),
]
