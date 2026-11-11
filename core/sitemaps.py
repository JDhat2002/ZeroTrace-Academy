from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from . import content


class StaticSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return ["core:home", "core:pricing"] + [f"core:page-{key}" for key in content.PAGES]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "core:home" else 0.6


class DepartmentSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return content.DEPARTMENTS

    def location(self, item):
        return reverse("core:department", args=[item["slug"]])


class ToolSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4

    def items(self):
        return content.TOOLS

    def location(self, item):
        return reverse("core:tool", args=[item["slug"]])


sitemaps = {"static": StaticSitemap, "departments": DepartmentSitemap, "tools": ToolSitemap}
