import secrets

from django.db.models import Q
from django.utils import timezone

from learning.models import Certificate, Course, Enrolment, LearningGoal, Lesson, LessonProgress

# Published outline weights. A missing component type is left out and the
# remaining weights are scaled to 100. Watching one video does not finish a
# course that still has a quiz, assignment, or available lab.
WEIGHTS = {"lesson": 40, "quiz": 20, "lab": 25, "assignment": 15}


class LearningError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def goal_for(user):
    preference = getattr(user, "preference", None)
    daily = preference.daily_minutes if preference and preference.daily_minutes else 30
    goal, _created = LearningGoal.objects.get_or_create(user=user, defaults={"daily_minutes": daily})
    return goal


def save_goal(user, daily_minutes, weekly_days):
    daily = int(daily_minutes)
    days = int(weekly_days)
    if daily not in {15, 30, 45, 60, 90, 120} or days not in {3, 4, 5, 6, 7}:
        raise LearningError("Choose a daily time and a weekly target from the list.")
    goal = goal_for(user)
    goal.daily_minutes = daily
    goal.weekly_days = days
    goal.save(update_fields=["daily_minutes", "weekly_days", "updated_at"])
    if user.preference.daily_minutes != daily:
        user.preference.daily_minutes = daily
        user.preference.save(update_fields=["daily_minutes"])
    return goal


def course_weights(course):
    custom = (
        course.weight_lesson,
        course.weight_quiz,
        course.weight_lab,
        course.weight_assignment,
        course.weight_final,
    )
    if all(value is None for value in custom):
        return dict(WEIGHTS)
    return {
        "lesson": course.weight_lesson or 0,
        "quiz": course.weight_quiz or 0,
        "lab": course.weight_lab or 0,
        "assignment": course.weight_assignment or 0,
        "final": course.weight_final or 0,
    }


def _groups(course):
    from labs.models import Lab

    from learning.models import Assessment

    lessons = Lesson.objects.filter(module__course=course)
    return {
        "lesson": lessons.filter(kind__in=[Lesson.Kind.READING, Lesson.Kind.VIDEO, Lesson.Kind.INTERACTIVE, Lesson.Kind.CODE, Lesson.Kind.CASE, Lesson.Kind.DOWNLOAD, Lesson.Kind.EXTERNAL]),
        "quiz": lessons.filter(kind=Lesson.Kind.QUIZ),
        "assignment": lessons.filter(kind=Lesson.Kind.ASSIGNMENT),
        "lab": Lab.objects.filter(course=course, status=Lab.Status.AVAILABLE),
        "final": Assessment.objects.filter(course=course, is_final=True, status=Assessment.Status.PUBLISHED),
    }


def progress_breakdown(course, enrolment=None):
    done_ids = set()
    if enrolment is not None:
        done_ids = set(
            enrolment.lesson_progress.filter(completed_at__isnull=False).values_list("lesson_id", flat=True)
        )
    parts = []
    active_weight = 0
    earned = 0
    weights = course_weights(course)
    for key, queryset in _groups(course).items():
        weight = weights.get(key) or 0
        total = queryset.count()
        if not total or not weight:
            continue
        active_weight += weight
        if key == "lab":
            completed = 0
        elif key == "final":
            completed = 0
            if enrolment is not None:
                from learning.models import Attempt

                completed = queryset.filter(
                    attempts__user=enrolment.user,
                    attempts__passed=True,
                    attempts__status=Attempt.Status.GRADED,
                ).distinct().count()
        else:
            completed = queryset.filter(pk__in=done_ids).count() if enrolment else 0
        ratio = completed / total
        earned += weight * ratio
        parts.append({"key": key, "weight": weight, "completed": completed, "total": total})
    percent = 0 if not active_weight else round(earned / active_weight * 100)
    return {"percent": percent, "parts": parts}


def progress_percent(enrolment):
    return progress_breakdown(enrolment.course, enrolment)["percent"]


def enrol(user, course):
    open_statuses = {Course.Status.PREVIEW, Course.Status.PUBLISHED}
    if course.status not in open_statuses:
        from learning.access import can_edit_course

        if not can_edit_course(user, course):
            raise LearningError("This course is not open for enrolment.", status=403)
    enrolment, created = Enrolment.objects.get_or_create(user=user, course=course)
    if created:
        from notifications.services import record_activity

        record_activity(user, "learning", f"Enrolled in {course.title}.")
    return enrolment


def complete_lesson(user, lesson):
    enrolment = Enrolment.objects.filter(user=user, course=lesson.module.course).first()
    if enrolment is None:
        raise LearningError("Enrol in the course before marking a lesson complete.", status=403)
    if lesson.kind == Lesson.Kind.VIDEO:
        raise LearningError("Video progress is recorded from playback. Watching a video does not complete a practical requirement.")
    if lesson.kind == Lesson.Kind.LAB:
        raise LearningError("A practical lesson is completed from the lab record, not by opening the page.", status=403)
    linked = lesson.course_assignments.first()
    if linked is not None:
        from learning.models import AssignmentSubmission

        graded = AssignmentSubmission.objects.filter(
            assignment=linked,
            user=user,
            status=AssignmentSubmission.Status.GRADED,
        ).exists()
        if not graded:
            raise LearningError("Submit the assignment and wait for a grade before this lesson can be completed.", status=403)
    row, _created = LessonProgress.objects.get_or_create(enrolment=enrolment, lesson=lesson)
    if row.completed_at is None:
        row.completed_at = timezone.now()
        row.save(update_fields=["completed_at"])
        from notifications.services import record_activity

        record_activity(user, "learning", f"Completed {lesson.title}.", minutes=lesson.duration_minutes)
    enrolment.last_accessed_at = timezone.now()
    percent = progress_percent(enrolment)
    if percent >= 100 and enrolment.completed_at is None:
        enrolment.completed_at = timezone.now()
    enrolment.save(update_fields=["last_accessed_at", "completed_at"])
    maybe_issue_certificate(enrolment)
    return enrolment


def maybe_issue_certificate(enrolment):
    course = enrolment.course
    if not course.certificate_eligible or course.status != Course.Status.PUBLISHED:
        return None
    if progress_percent(enrolment) < 100 or enrolment.completed_at is None:
        return None
    certificate, created = Certificate.objects.get_or_create(
        user=enrolment.user,
        course=course,
        defaults={"credential_id": secrets.token_hex(8)},
    )
    if created:
        from notifications.services import record_activity

        record_activity(enrolment.user, "certificate", f"Certificate issued for {course.title}.")
    return certificate


def next_lesson(enrolment):
    done = enrolment.lesson_progress.filter(completed_at__isnull=False).values_list("lesson_id", flat=True)
    return (
        Lesson.objects.filter(module__course=enrolment.course)
        .exclude(pk__in=done)
        .order_by("module__position", "position")
        .first()
    )


def recommendations(user, limit=4):
    interests = set(getattr(user.preference, "interests", None) or [])
    if user.learning_interest:
        interests.add(user.learning_interest)
    objective = getattr(user.preference, "objective", "") or ""
    enrolled = Enrolment.objects.filter(user=user).values_list("course_id", flat=True)
    courses = list(
        Course.objects.filter(status__in=[Course.Status.PREVIEW, Course.Status.PUBLISHED]).exclude(pk__in=enrolled)
    )

    def score(course):
        value = 0
        if course.department_key in interests:
            value += 3
        if objective and course.objective == objective:
            value += 2
        if course.level == Course.Level.BEGINNER and getattr(user.preference, "experience_level", "") in {"", "complete-beginner", "beginner"}:
            value += 1
        return value

    courses.sort(key=lambda course: (-score(course), course.title))
    return courses[:limit]


def learning_tab(user, tab):
    rows = Enrolment.objects.filter(user=user).select_related("course")
    if tab == "saved":
        return rows.filter(saved=True)
    if tab == "completed":
        return rows.filter(completed_at__isnull=False)
    if tab == "progress":
        return rows.filter(completed_at__isnull=True, lesson_progress__completed_at__isnull=False).distinct()
    if tab == "new":
        return rows.filter(completed_at__isnull=True).filter(Q(lesson_progress__isnull=True))
    return rows


def learner_snapshot(user):
    from learning.models import Assessment, AssignmentSubmission, Attempt, CourseAssignment

    enrolled_ids = Enrolment.objects.filter(user=user).values_list("course_id", flat=True)
    assignments = CourseAssignment.objects.filter(course_id__in=enrolled_ids).select_related("course")
    submitted = set(AssignmentSubmission.objects.filter(user=user).values_list("assignment_id", flat=True))
    pending = [row for row in assignments if row.pk not in submitted]
    upcoming = Assessment.objects.filter(course_id__in=enrolled_ids, status=Assessment.Status.PUBLISHED).select_related("course")[:6]
    grades = Attempt.objects.filter(user=user, status=Attempt.Status.GRADED).select_related("assessment")[:5]
    return {"pending_assignments": pending[:6], "upcoming_assessments": list(upcoming), "recent_grades": list(grades)}
