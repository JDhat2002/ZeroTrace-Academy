from django.conf import settings

from . import content


def site(request):
    return {
        "SITE_NAME": "ZeroTrace Academy",
        "SITE_URL": settings.SITE_URL,
        "STATIC_EXPORT": settings.STATIC_EXPORT,
        "NAV": content.NAV,
        "FOOTER": content.FOOTER,
    }
