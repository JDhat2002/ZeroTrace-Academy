from django.urls import path

from . import content, views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("pricing/", views.pricing, name="pricing"),
    path("departments/<slug:slug>/", views.department_detail, name="department"),
    path("tools/<slug:slug>/", views.tool_detail, name="tool"),
    path("partials/tools/", views.tools_partial, name="tools_partial"),
    path("partials/roadmaps/<slug:slug>/", views.roadmap_partial, name="roadmap_partial"),
    path("partials/ai-mentor/<slug:slug>/", views.mentor_partial, name="mentor_partial"),
]

urlpatterns += [
    path(page["path"], views.info_page, {"key": key}, name=f"page-{key}")
    for key, page in content.PAGES.items()
]
