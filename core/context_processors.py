from django.conf import settings

from . import content


def site(request):
    return {
        "SITE_NAME": "ZeroTrace Academy",
        "SITE_URL": settings.SITE_URL,
        "NAV": content.NAV,
        "FOOTER": content.FOOTER,
    }
