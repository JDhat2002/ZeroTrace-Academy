from django.urls import path

from teams import views

urlpatterns = [
    path("", views.team_list, name="team-list"),
    path("<slug:slug>/", views.team_centre, name="team-centre"),
    path("<slug:slug>/learn/", views.team_learn, name="team-learn"),
]
