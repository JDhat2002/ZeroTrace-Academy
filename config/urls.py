from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from django.views.generic import RedirectView

from config.marketing import asset, marketing
from memberships.views import pricing_page

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.api_urls")),
    path("api/access/", include("accounts.access_urls")),
    path("api/profile/", include("profiles.api_urls")),
    path("api/sessions/", include("authentication.session_urls")),
    path("api/onboarding/", include("profiles.onboarding_urls")),
    path("api/dashboard/", include("workspace.api_urls")),
    path("api/billing/", include("memberships.webhook_urls")),
    path("pricing.html", pricing_page, name="public-pricing"),
    path("pricing/", RedirectView.as_view(url="/pricing.html", query_string=True)),
    path("", include("authentication.urls")),
    path("", include("profiles.urls")),
    path("app/", include("workspace.urls")),
    path("css/<path:path>", asset, {"root": "css"}),
    path("js/<path:path>", asset, {"root": "js"}),
    path("assets/<path:path>", asset, {"root": "assets"}),
    path("", marketing, {"page": "index.html"}),
    path("<path:page>", marketing),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
