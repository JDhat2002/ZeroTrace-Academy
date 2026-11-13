from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from labs.models import VirtualMachine
from learning.models import Course, Lesson, Module
from learning.services import complete_lesson, enrol, progress_percent
from workspace.catalogue import ensure_catalogue


def member(email="ada@example.com", username="ada"):
    user = User.objects.create_user(
        email=email,
        username=username,
        password="Correct-Horse-1",
        full_name="Ada Lovelace",
        country="IN",
        learning_interest="soc",
        is_active=True,
    )
    user.email_verified_at = timezone.now()
    user.onboarding_completed_at = timezone.now()
    user.save()
    user.preference.interests = ["soc"]
    user.preference.objective = "soc"
    user.preference.save()
    return user


class WorkspaceTests(TestCase):
    def setUp(self):
        self.user = member()
        self.client.force_login(self.user)
        ensure_catalogue()

    def test_dashboard_uses_recorded_zeros(self):
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Welcome back, Ada")
        self.assertContains(response, "Courses enrolled")
        self.assertContains(response, ">0<")
        self.assertNotContains(response, "AI")
        metrics = response.context["metrics"]
        self.assertEqual(metrics["courses_enrolled"], 0)
        self.assertEqual(metrics["labs_completed"], 0)
        self.assertEqual(metrics["certificates"], 0)
        self.assertEqual(metrics["ctf_solved"], 0)
        self.assertEqual(metrics["range_minutes"], 0)

    def test_progress_weights_and_preview_certificate(self):
        course = Course.objects.create(
            slug="weights",
            title="Weights",
            department="SOC",
            department_key="soc",
            summary="Outline",
            certificate_eligible=False,
            status=Course.Status.PREVIEW,
        )
        module = Module.objects.create(course=course, title="Core", position=1)
        lesson = Lesson.objects.create(module=module, title="Read", kind=Lesson.Kind.READING, position=1)
        quiz = Lesson.objects.create(module=module, title="Check", kind=Lesson.Kind.QUIZ, position=2)
        enrolment = enrol(self.user, course)
        complete_lesson(self.user, lesson)
        enrolment.refresh_from_db()
        self.assertEqual(progress_percent(enrolment), 67)
        self.assertIsNone(enrolment.completed_at)
        complete_lesson(self.user, quiz)
        enrolment.refresh_from_db()
        self.assertEqual(progress_percent(enrolment), 100)
        self.assertIsNotNone(enrolment.completed_at)
        self.assertEqual(self.user.certificates.count(), 0)

    def test_paid_plan_and_lab_cannot_be_activated_from_the_browser(self):
        api = APIClient()
        api.force_login(self.user)
        denied = api.post("/api/dashboard/membership/", {"plan": "elite"}, format="json")
        self.assertEqual(denied.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.membership, "free")
        lab = api.post("/api/dashboard/labs/start/", {"lab": "red-team"}, format="json")
        self.assertEqual(lab.status_code, 409)
        self.assertIn("not provisioned", lab.data["detail"])
        self.assertEqual(VirtualMachine.objects.count(), 0)
        tool = api.post("/api/dashboard/tools/launch/", {"tool": "tracescan"}, format="json")
        self.assertEqual(tool.status_code, 409)
