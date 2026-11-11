from django.test import TestCase
from django.urls import reverse

from . import content, services


class PublicPagesTests(TestCase):
    def test_homepage_renders_every_section(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        for anchor in ["departments", "cyber-range", "tools", "forensics", "soc", "roadmaps", "ai-mentor", "ctf", "career", "community", "pricing", "testimonials", "faq"]:
            self.assertContains(response, f'id="{anchor}"')

    def test_all_departments_and_tools_listed(self):
        response = self.client.get(reverse("core:home"))
        for d in content.DEPARTMENTS:
            self.assertContains(response, reverse("core:department", args=[d["slug"]]))
        for t in content.TOOLS:
            self.assertContains(response, reverse("core:tool", args=[t["slug"]]))

    def test_every_linked_page_resolves(self):
        urls = [page["path"] for page in content.PAGES.values()]
        urls += [link for col in content.FOOTER for _, link in col["links"]]
        urls += [child["url"].split("#")[0] for item in content.NAV for child in item.get("children", [])]
        for url in set(urls):
            path = "/" + url.lstrip("/")
            with self.subTest(url=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_tool_filter_partial(self):
        response = self.client.get(reverse("core:tools_partial"), {"category": "forensics"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tools"]), len(services.tools("forensics")))
        self.assertEqual(self.client.get(reverse("core:tools_partial"), {"category": "bogus"}).context["active_filter"], "all")

    def test_roadmap_and_mentor_partials(self):
        self.assertContains(self.client.get(reverse("core:roadmap_partial", args=["soc-analyst"])), "SIEM")
        self.assertContains(self.client.get(reverse("core:mentor_partial", args=["explain"])), "Sample response")
        self.assertEqual(self.client.get(reverse("core:mentor_partial", args=["nope"])).status_code, 404)

    def test_stats_are_derived_from_content(self):
        values = [s["value"] for s in services.platform_stats()]
        self.assertEqual(values, [31, 24, len(content.RANGE_FEATURES), 6])

    def test_tools_never_marked_available(self):
        self.assertTrue(all(t["status"] == "Proposed" for t in services.tools()))

    def test_seo_endpoints(self):
        self.assertContains(self.client.get("/robots.txt"), "Sitemap:")
        self.assertContains(self.client.get("/sitemap.xml"), "/departments/ai-security/")


class AuthTests(TestCase):
    def test_register_logs_user_in(self):
        response = self.client.post(reverse("register"), {
            "username": "learner", "password1": "Zt-test-pass-2026!", "password2": "Zt-test-pass-2026!",
        }, follow=True)
        self.assertTrue(response.context["user"].is_authenticated)

    def test_login_page(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
