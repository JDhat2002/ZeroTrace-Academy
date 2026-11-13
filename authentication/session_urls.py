from django.urls import path

from authentication import api

urlpatterns = [
    path("", api.session_list, name="api-sessions"),
    path("logout-all/", api.session_logout_all, name="api-logout-all"),
    path("<int:session_id>/", api.session_delete, name="api-session-delete"),
]
