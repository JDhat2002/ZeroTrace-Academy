from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import User
from learning.assess import grade_attempt, start_attempt
from learning.foundation_content import DIAGNOSTIC
from learning.models import (
    AcademyDepartment,
    Assessment,
    AssignmentSubmission,
    Course,
    CourseAssignment,
    FoundationLevel,
    GlossaryBookmark,
    GlossaryTerm,
    LearnerPlacement,
    Lesson,
    LessonProgress,
    Module,
    Question,
    QuestionBank,
)
from learning.services import LearningError, complete_lesson, enrol
from learning.uploads import save_submission_file
from workspace.catalogue import ensure_catalogue
from workspace.tests import member


class LmsTests(TestCase):
    def setUp(self):
        self.user = member()
        self.client.force_login(self.user)
        ensure_catalogue()

    def test_departments_exist_without_a_generated_catalogue(self):
        self.assertEqual(AcademyDepartment.objects.count(), 32)
        self.assertLess(Course.objects.count(), 20)
        self.assertFalse(Course.objects.filter(academy_department__slug="ai-security").exists())
        response = self.client.get("/app/departments/")
        self.assertContains(response, "Computer Science and IT Fundamentals")
        detail = self.client.get("/app/departments/hardware-security/")
        self.assertContains(detail, "No course is published in this department yet")
        self.assertContains(detail, "Start here")
        page = self.client.get("/dashboard/")
        self.assertNotContains(page, "AI")

    def test_drafts_stay_out_of_the_catalogue(self):
        Course.objects.create(
            slug="hidden-draft",
            title="Hidden Draft Course",
            department="SOC",
            department_key="soc",
            summary="Not published",
            status=Course.Status.DRAFT,
        )
        catalogue = self.client.get("/app/courses/")
        self.assertNotContains(catalogue, "Hidden Draft Course")
        self.assertContains(catalogue, "No reviews yet")
        missing = self.client.get("/app/courses/hidden-draft/")
        self.assertEqual(missing.status_code, 404)

    def test_instructor_cannot_publish(self):
        self.user.role = User.Role.INSTRUCTOR
        self.user.save(update_fields=["role"])
        department = AcademyDepartment.objects.get(slug="soc-operations")
        course = Course.objects.create(
            slug="author-draft",
            title="Author draft",
            department=department.name,
            department_key=department.slug,
            academy_department=department,
            summary="Draft",
            status=Course.Status.DRAFT,
            created_by=self.user,
        )
        response = self.client.post(
            f"/app/studio/courses/{course.slug}/",
            {"action": "publish"},
        )
        self.assertEqual(response.status_code, 200)
        course.refresh_from_db()
        self.assertEqual(course.status, Course.Status.DRAFT)

    def test_objective_question_is_graded(self):
        course = Course.objects.create(
            slug="graded-course",
            title="Graded course",
            department="SOC",
            department_key="soc",
            summary="Outline",
            status=Course.Status.PREVIEW,
        )
        bank = QuestionBank.objects.create(course=course, title="Bank")
        question = Question.objects.create(
            bank=bank,
            kind=Question.Kind.MCQ,
            prompt="Which control records access?",
            marks=2,
            options=[{"text": "Logging", "correct": True}, {"text": "Guessing", "correct": False}],
        )
        assessment = Assessment.objects.create(
            course=course,
            bank=bank,
            title="Check",
            total_marks=2,
            pass_percent=70,
            status=Assessment.Status.PUBLISHED,
        )
        enrol(self.user, course)
        attempt = start_attempt(self.user, assessment)
        graded = grade_attempt(attempt, {str(question.pk): "0"})
        self.assertEqual(graded.score, 2)
        self.assertTrue(graded.passed)

    def test_video_and_bad_upload_are_refused(self):
        course = Course.objects.create(
            slug="practical-course",
            title="Practical course",
            department="SOC",
            department_key="soc",
            summary="Outline",
            status=Course.Status.PREVIEW,
        )
        module = Module.objects.create(course=course, title="Core", position=1)
        video = Lesson.objects.create(module=module, title="Watch", kind=Lesson.Kind.VIDEO, position=1)
        enrol(self.user, course)
        with self.assertRaises(LearningError):
            complete_lesson(self.user, video)
        assignment = CourseAssignment.objects.create(course=course, title="Report", allowed_extensions="pdf,txt")
        upload = SimpleUploadedFile("notes.py", b"print(1)", content_type="text/plain")
        with self.assertRaises(LearningError):
            save_submission_file(upload, assignment)

    def test_submission_file_is_private(self):
        other = member(email="other@example.com", username="other")
        course = Course.objects.create(
            slug="private-course",
            title="Private course",
            department="SOC",
            department_key="soc",
            summary="Outline",
            status=Course.Status.PREVIEW,
        )
        assignment = CourseAssignment.objects.create(course=course, title="Notes", allowed_extensions="txt")
        stored, original = save_submission_file(SimpleUploadedFile("notes.txt", b"evidence"), assignment)
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            user=self.user,
            stored_name=stored,
            original_name=original,
        )
        owner = self.client.get(f"/app/assignments/submissions/{submission.pk}/")
        self.assertEqual(owner.status_code, 200)
        self.client.force_login(other)
        denied = self.client.get(f"/app/assignments/submissions/{submission.pk}/")
        self.assertEqual(denied.status_code, 404)


class FoundationsTests(TestCase):
    def setUp(self):
        self.user = member(email="foundations@example.com", username="foundations")
        self.client.force_login(self.user)
        ensure_catalogue()

    def test_programme_is_one_course_with_levels_and_a_glossary(self):
        self.assertEqual(Course.objects.filter(slug="zerotrace-foundations").count(), 1)
        self.assertEqual(FoundationLevel.objects.count(), 11)
        self.assertGreaterEqual(GlossaryTerm.objects.count(), 40)
        page = self.client.get("/app/foundations/")
        self.assertContains(page, "Digital Literacy")
        self.assertContains(page, "Ethics, Law, and Professional Responsibility")
        department = AcademyDepartment.objects.get(slug="networking")
        self.assertIn("basics", department.curriculum)
        self.assertTrue(department.curriculum["prerequisites"])

    def test_placement_can_skip_early_levels_but_not_the_certificate(self):
        response = self.client.post("/app/foundations/placement/", {
            "computer": "comfortable",
            "programming": "comfortable",
            "networking": "comfortable",
            "apply": "yes",
            **{f"q{index}": question["correct"] for index, question in enumerate(DIAGNOSTIC)},
        })
        self.assertEqual(response.status_code, 200)
        placement = LearnerPlacement.objects.get(user=self.user)
        self.assertEqual(placement.start_level, 6)
        self.assertTrue(placement.credited)
        ethics = FoundationLevel.objects.get(number=9)
        self.assertFalse(
            LessonProgress.objects.filter(enrolment__user=self.user, lesson=ethics.lesson, completed_at__isnull=False).exists()
        )
        self.assertEqual(self.user.certificates.count(), 0)

    def test_a_beginner_with_no_experience_starts_at_zero(self):
        from learning.foundation_content import recommend_start

        self.assertEqual(recommend_start("none", "none", "none", 8, 8), 0)

    def test_glossary_search_and_bookmark(self):
        page = self.client.get("/app/foundations/glossary/?q=phishing")
        self.assertContains(page, "Phishing")
        self.assertNotContains(page, "Ransomware")
        term = GlossaryTerm.objects.get(slug="phishing")
        saved = self.client.post("/app/foundations/glossary/?q=phishing", {"term": term.slug})
        self.assertEqual(saved.status_code, 302)
        self.assertTrue(GlossaryBookmark.objects.filter(user=self.user, term=term).exists())

