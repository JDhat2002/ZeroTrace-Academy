import json
import re
from functools import lru_cache
from pathlib import Path

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

ICON_DIR = Path(__file__).resolve().parent.parent / "icons"
_ROOT_ATTRS = re.compile(r"<svg[^>]*>", re.S)


@lru_cache(maxsize=None)
def _icon_body(name):
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        return None
    raw = path.read_text()
    match = _ROOT_ATTRS.search(raw)
    return raw[match.end():raw.rindex("</svg>")].strip()


@register.simple_tag
def icon(name, css="size-5", stroke="1.75"):
    """Inline a Lucide icon (ISC licence) from core/icons. Decorative by default."""
    body = _icon_body(name)
    if body is None:
        raise template.TemplateSyntaxError(f"Unknown icon '{name}'. Run scripts/sync_icons.py.")
    return mark_safe(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="{escape(stroke)}" stroke-linecap="round" stroke-linejoin="round" '
        f'class="{escape(css)}" aria-hidden="true" focusable="false">{body}</svg>'
    )


@register.filter
def level_class(level):
    return {
        "Beginner": "lvl-1",
        "Intermediate": "lvl-2",
        "Advanced": "lvl-3",
    }.get(level, "lvl-1")


@register.filter
def level_bars(level):
    return {"Beginner": 1, "Intermediate": 2, "Advanced": 3}.get(level, 1)


@register.simple_tag(takes_context=True)
def json_ld(context):
    if context.get("STATIC_EXPORT"):
        base = context["SITE_URL"]
    else:
        base = context["request"].build_absolute_uri("/").rstrip("/")
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "EducationalOrganization",
                "@id": f"{base}/#organization",
                "name": "ZeroTrace Academy",
                "alternateName": "ZeroTrace",
                "url": f"{base}/",
                "logo": f"{base}/static/img/logo-mark.svg",
                "description": "The complete cybersecurity learning, tools and simulation ecosystem.",
            },
            {
                "@type": "WebSite",
                "@id": f"{base}/#website",
                "url": f"{base}/",
                "name": "ZeroTrace Academy",
                "publisher": {"@id": f"{base}/#organization"},
            },
        ],
    }
    return mark_safe(json.dumps(data).replace("</", "<\\/"))
