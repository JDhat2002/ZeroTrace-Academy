import re
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client, override_settings
from django.urls import reverse

from core import content, services

TOOLS_PARTIAL_QUERY = re.compile(r'/partials/tools/\?category=([\w-]+)')
TOOLS_PUSH_URL = re.compile(r'hx-push-url="\?category=[\w-]+#tools"')


def export_urls():
    urls = [reverse("core:home"), reverse("core:pricing"), reverse("login"), reverse("register")]
    urls += [reverse(f"core:page-{key}") for key in content.PAGES]
    urls += [reverse("core:department", args=[d["slug"]]) for d in services.departments()]
    urls += [reverse("core:tool", args=[t["slug"]]) for t in content.TOOLS]
    urls += [reverse("core:roadmap_partial", args=[r["slug"]]) for r in services.roadmaps()]
    urls += [reverse("core:mentor_partial", args=[p["slug"]]) for p in services.mentor_prompts()]
    return urls


def rewrite(html):
    """Point query-string HTMX requests at the pre-rendered fragment files."""
    html = TOOLS_PARTIAL_QUERY.sub(r"/partials/tools/\1.html", html)
    return TOOLS_PUSH_URL.sub('hx-push-url="false"', html)


class Command(BaseCommand):
    help = "Render every public page and HTMX fragment into a static site folder."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="site", help="Output folder (default: site/)")
        parser.add_argument("--site-url", default="", help="Public URL, used for canonical and Open Graph tags")

    def handle(self, *args, out, site_url, **options):
        out_dir = (Path(settings.BASE_DIR) / out).resolve()
        if out_dir == Path(settings.BASE_DIR).resolve():
            raise CommandError("--out must be a subfolder of the project.")
        if out_dir.exists():
            shutil.rmtree(out_dir)

        with override_settings(STATIC_EXPORT=True, SITE_URL=site_url.rstrip("/"), ALLOWED_HOSTS=["testserver"]):
            client = Client()
            pages = [(url, "index.html") for url in export_urls()]
            pages += [(f"{reverse('core:tools_partial')}?category={f['key']}", None) for f in services.tool_filters()]
            for url, _ in pages:
                response = client.get(url)
                if response.status_code != 200:
                    raise CommandError(f"{url} returned {response.status_code}")
                path, _, query = url.partition("?")
                if query:
                    target = out_dir / path.strip("/") / f"{query.split('=', 1)[1]}.html"
                else:
                    target = out_dir / path.strip("/") / "index.html"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(rewrite(response.content.decode()), encoding="utf-8")

        (out_dir / "robots.txt").write_text("User-agent: *\nDisallow: /accounts/\nDisallow: /partials/\n", encoding="utf-8")
        shutil.copytree(Path(settings.BASE_DIR) / "static", out_dir / "static")
        self.stdout.write(self.style.SUCCESS(f"Exported {len(pages)} pages to {out_dir}"))
