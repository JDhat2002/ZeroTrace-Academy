from django.urls import path

from campus import views

urlpatterns = [
    path("", views.campus_list, name="campus-list"),
    path("<slug:slug>/", views.campus_centre, name="campus-centre"),
    path("<slug:slug>/study/", views.campus_study, name="campus-study"),
]
