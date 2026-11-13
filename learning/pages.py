from datetime import timedelta

from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from accounts.access import is_platform_admin
from labs.models import Lab
from labs.services import LabError, start_lab
from learning.access import can_author, can_edit_course, can_publish, can_read_submission
from learning.assess import grade_attempt, record_manual_mark, start_attempt
from learning.models import (
    AcademyDepartment,
    Announcement,
    Assessment,
    AssignmentSubmission,
    Attempt,
    AttemptAnswer,
    Bookmark,
    Course,
    CourseAssignment,
    CourseInstructor,
    CourseReview,
    CourseRevision,
    Enrolment,
    LearningPath,
    Lesson,
    LessonComment,
    LessonNote,
    LessonProgress,
    Module,
    Question,
    QuestionBank,
)
from learning.languages import WORLD_LANGUAGES, language_names
from learning.query import catalogue, catalogue_filters
from learning.services import LearningError, enrol, progress_breakdown
from learning.uploads import save_submission_file, submission_file
from workspace.guards import member_required

AUTHOR_WEIGHTS = {"weight_lesson": 25, "weight_quiz": 20, "weight_lab": 30, "weight_assignment": 15, "weight_final": 10}


def _snapshot(course):
    return {
        "title": course.title,
        "summary": course.summary,
        "status": course.status,
        "modules": [
            {"title": module.title, "position": module.position, "lessons": [
                {"title": lesson.title, "kind": lesson.kind, "position": lesson.position}
                for lesson in module.lessons.all()
            ]}
            for module in course.modules.all()
        ],
    }


def _save_revision(course, user):
    CourseRevision.objects.create(course=course, editor=user, snapshot=_snapshot(course))


def _visible_course(user, slug):
    course = get_object_or_404(Course.objects.prefetch_related("modules__lessons"), slug=slug)
    if course.status in {Course.Status.PREVIEW, Course.Status.PUBLISHED} or can_edit_course(user, course):
        return course
    raise Http404()


@member_required
@require_http_methods(["GET"])
def departments(request):
    return render(request, "app/departments.html", {"departments": AcademyDepartment.objects.all()})


@member_required
@require_http_methods(["GET"])
def department_detail(request, slug):
    department = get_object_or_404(AcademyDepartment, slug=slug)
    courses = department.courses.filter(status__in=[Course.Status.PREVIEW, Course.Status.PUBLISHED])
    paths = LearningPath.objects.filter(steps__course__academy_department=department).distinct()
    return render(request, "app/department.html", {"department": department, "courses": courses, "paths": paths})


@member_required
@require_http_methods(["GET", "POST"])
def lesson_page(request, slug, lesson_id):
    course = _visible_course(request.user, slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    enrolment = Enrolment.objects.filter(user=request.user, course=course).first()
    if enrolment is None and not can_edit_course(request.user, course):
        return HttpResponseForbidden("Enrol before opening this lesson.")
    notice = ""
    if request.method == "POST" and enrolment is not None:
        action = request.POST.get("action")
        try:
            if action == "note":
                LessonNote.objects.update_or_create(
                    user=request.user,
                    lesson=lesson,
                    defaults={"body": (request.POST.get("body") or "")[:4000]},
                )
                notice = "Note saved."
            elif action == "bookmark":
                mark = Bookmark.objects.filter(user=request.user, lesson=lesson).first()
                if mark:
                    mark.delete()
                    notice = "Bookmark removed."
                else:
                    Bookmark.objects.create(user=request.user, lesson=lesson)
                    notice = "Bookmark saved."
            elif action == "comment":
                body = (request.POST.get("body") or "").strip()
                if body:
                    LessonComment.objects.create(lesson=lesson, user=request.user, body=body[:2000])
                    notice = "Comment saved."
            elif action == "video":
                if lesson.kind != Lesson.Kind.VIDEO:
                    raise LearningError("This lesson has no video.")
                ratio = max(0, min(100, int(request.POST.get("ratio") or 0)))
                row, _created = LessonProgress.objects.get_or_create(enrolment=enrolment, lesson=lesson)
                row.video_ratio = max(row.video_ratio, ratio)
                row.save(update_fields=["video_ratio"])
                notice = "Playback position saved. The video itself does not complete the course."
            elif action == "lab":
                if lesson.lab_id is None:
                    raise LearningError("No approved lab is attached to this lesson.")
                from accounts.access import has_membership

                required = course.membership_code or lesson.lab.required_plan
                if required and required != "free" and not has_membership(request.user, required):
                    raise LearningError("Your membership does not include this lab.", status=403)
                try:
                    start_lab(request.user, lesson.lab)
                except LabError as exc:
                    raise LearningError(exc.message, status=exc.status) from exc
        except (LearningError, ValueError) as exc:
            notice = getattr(exc, "message", "That action was not saved.")
    lessons = list(Lesson.objects.filter(module__course=course).order_by("module__position", "position"))
    index = next((position for position, row in enumerate(lessons) if row.pk == lesson.pk), 0)
    video_ok = lesson.video_reference.startswith("https://") and "@" not in lesson.video_reference.split("/")[2]
    return render(request, "app/lesson.html", {
        "course": course,
        "lesson": lesson,
        "enrolment": enrolment,
        "notice": notice,
        "modules": course.modules.all(),
        "previous": lessons[index - 1] if index else None,
        "next": lessons[index + 1] if index + 1 < len(lessons) else None,
        "note": LessonNote.objects.filter(user=request.user, lesson=lesson).first(),
        "bookmarked": Bookmark.objects.filter(user=request.user, lesson=lesson).exists(),
        "comments": lesson.comments.select_related("user")[:30],
        "video_ok": video_ok,
        "progress": LessonProgress.objects.filter(enrolment=enrolment, lesson=lesson).first() if enrolment else None,
    })


@member_required
@require_http_methods(["GET"])
def instructor_home(request):
    if not can_author(request.user):
        raise Http404()
    courses = Course.objects.filter(created_by=request.user) | Course.objects.filter(instructors__user=request.user)
    if is_platform_admin(request.user):
        courses = Course.objects.all()
    courses = courses.distinct()
    return render(request, "app/instructor.html", {
        "courses": courses.order_by("title"),
        "pending": AssignmentSubmission.objects.filter(assignment__course__in=courses, status=AssignmentSubmission.Status.SUBMITTED).select_related("assignment", "user")[:20],
        "ungraded": Attempt.objects.filter(assessment__course__in=courses, status=Attempt.Status.SUBMITTED).select_related("assessment", "user")[:20],
        "questions": LessonComment.objects.filter(lesson__module__course__in=courses).select_related("user", "lesson")[:12],
    })


@member_required
@require_http_methods(["GET", "POST"])
def studio_list(request):
    if not can_author(request.user):
        raise Http404()
    notice = ""
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        department = get_object_or_404(AcademyDepartment, slug=request.POST.get("department"))
        if not title:
            notice = "Enter a course title."
        else:
            base = slugify(title)[:60] or "course"
            slug = base
            number = 2
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base}-{number}"
                number += 1
            course = Course.objects.create(
                slug=slug,
                title=title[:160],
                summary="Draft outline.",
                department=department.name,
                department_key=department.slug,
                academy_department=department,
                status=Course.Status.DRAFT,
                created_by=request.user,
                instructor=request.user.full_name,
                **AUTHOR_WEIGHTS,
            )
            CourseInstructor.objects.get_or_create(course=course, user=request.user)
            _save_revision(course, request.user)
            return redirect("studio-course", slug=course.slug)
    return render(request, "app/studio_list.html", {
        "notice": notice,
        "departments": AcademyDepartment.objects.all(),
        "courses": Course.objects.filter(created_by=request.user).order_by("-id"),
    })


@member_required
@require_http_methods(["GET", "POST"])
def studio_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if not can_edit_course(request.user, course):
        raise Http404()
    notice = ""
    if request.method == "POST":
        action = request.POST.get("action") or "save"
        try:
            notice = _studio_action(request, course, action)
        except LearningError as exc:
            notice = exc.message
        course.refresh_from_db()
    return render(request, "app/studio_course.html", {
        "course": course,
        "notice": notice,
        "departments": AcademyDepartment.objects.all(),
        "levels": Course.Level.choices,
        "languages": WORLD_LANGUAGES,
        "language_names": language_names(),
        "labs": Lab.objects.all(),
        "banks": course.question_banks.all(),
        "revisions": course.revisions.all()[:8],
        "can_publish": can_publish(request.user),
        "weights": AUTHOR_WEIGHTS,
    })


def _studio_action(request, course, action):
    if action == "save":
        department = get_object_or_404(AcademyDepartment, slug=request.POST.get("department"))
        course.title = (request.POST.get("title") or course.title).strip()[:160]
        course.summary = (request.POST.get("summary") or "").strip()
        course.academy_department = department
        course.department = department.name
        course.department_key = department.slug
        course.level = request.POST.get("level") if request.POST.get("level") in dict(Course.Level.choices) else course.level
        course.prerequisites = (request.POST.get("prerequisites") or "")[:4000]
        course.outcomes = [line.strip() for line in (request.POST.get("outcomes") or "").splitlines() if line.strip()][:20]
        course.duration_minutes = int(request.POST.get("duration") or 0)
        posted_language = (request.POST.get("language") or "English")[:40]
        if posted_language in language_names() or posted_language == course.language:
            course.language = posted_language
        course.membership_code = (request.POST.get("membership") or "free")[:40]
        course.practical_requirements = (request.POST.get("practical") or "")[:4000]
        course.assessment_summary = (request.POST.get("assessment") or "")[:4000]
        course.certificate_rule = (request.POST.get("certificate_rule") or "")[:4000]
        course.certificate_eligible = request.POST.get("certificate") == "on"
        for key in AUTHOR_WEIGHTS:
            posted = request.POST.get(key)
            if posted is not None and posted != "":
                setattr(course, key, int(posted))
        upload = request.FILES.get("thumbnail")
        if upload:
            suffix = upload.name.lower().rsplit(".", 1)[-1]
            if suffix not in {"png", "jpg", "jpeg", "webp"}:
                raise LearningError("Use a PNG, JPG, or WebP thumbnail.")
            course.thumbnail = upload
        course.save()
        _save_revision(course, request.user)
        return "Draft saved. A revision was stored."
    if action == "module":
        title = (request.POST.get("title") or "").strip()
        if not title:
            raise LearningError("Enter a module title.")
        position = course.modules.count() + 1
        Module.objects.create(course=course, title=title[:160], position=position)
        _save_revision(course, request.user)
        return "Module added."
    if action == "lesson":
        module = get_object_or_404(Module, pk=request.POST.get("module"), course=course)
        kind = request.POST.get("kind")
        if kind not in dict(Lesson.Kind.choices):
            kind = Lesson.Kind.READING
        Lesson.objects.create(
            module=module,
            title=(request.POST.get("title") or "Untitled lesson")[:160],
            kind=kind,
            body=(request.POST.get("body") or "")[:8000],
            position=module.lessons.count() + 1,
        )
        _save_revision(course, request.user)
        return "Lesson added."
    if action == "move":
        _move(course, request.POST.get("target"), request.POST.get("direction"))
        _save_revision(course, request.user)
        return "Order saved."
    if action == "attach-lab":
        lesson = get_object_or_404(Lesson, pk=request.POST.get("lesson"), module__course=course)
        from labs.models import Lab

        lab = get_object_or_404(Lab, slug=request.POST.get("lab"))
        lesson.lab = lab
        lesson.kind = Lesson.Kind.LAB
        lesson.save(update_fields=["lab", "kind"])
        return "Lab attached. Launch still depends on enrolment, entitlement, and a connected environment."
    if action == "question":
        bank, _created = QuestionBank.objects.get_or_create(
            course=course,
            title=f"{course.title} bank",
            defaults={"department": course.academy_department, "created_by": request.user, "topic": course.department},
        )
        kind = request.POST.get("kind") if request.POST.get("kind") in dict(Question.Kind.choices) else Question.Kind.MCQ
        options = []
        if kind in {Question.Kind.MCQ, Question.Kind.MULTI}:
            correct = request.POST.get("correct") or "0"
            for index, text in enumerate(request.POST.getlist("option")):
                if text.strip():
                    options.append({"text": text.strip()[:240], "correct": str(index) == correct or (kind == Question.Kind.MULTI and str(index) in request.POST.getlist("correct"))})
        Question.objects.create(
            bank=bank,
            kind=kind,
            prompt=(request.POST.get("prompt") or "").strip()[:4000],
            marks=int(request.POST.get("marks") or 1),
            options=options,
            answer_key=(request.POST.get("answer_key") or "")[:400],
            difficulty=course.level,
        )
        return "Question saved in this course bank."
    if action == "assessment":
        bank = course.question_banks.first()
        Assessment.objects.create(
            course=course,
            bank=bank,
            title=(request.POST.get("title") or "Assessment")[:160],
            instructions=(request.POST.get("instructions") or "")[:4000],
            pass_percent=int(request.POST.get("pass_percent") or 70),
            attempt_limit=int(request.POST.get("attempt_limit") or 1),
            time_limit_minutes=int(request.POST.get("time_limit") or 0) or None,
            randomise=request.POST.get("randomise") == "on",
            negative_marking=request.POST.get("negative") == "on",
            is_final=request.POST.get("final") == "on",
            total_marks=int(request.POST.get("total_marks") or 0),
            status=Assessment.Status.DRAFT,
            created_by=request.user,
        )
        return "Assessment saved as a draft."
    if action == "assignment":
        CourseAssignment.objects.create(
            course=course,
            title=(request.POST.get("title") or "Assignment")[:160],
            instructions=(request.POST.get("instructions") or "")[:4000],
            rubric=(request.POST.get("rubric") or "")[:4000],
            max_marks=int(request.POST.get("max_marks") or 100),
            allowed_extensions=(request.POST.get("extensions") or "pdf,txt,md,png,jpg,jpeg,docx")[:120],
            allow_late=request.POST.get("allow_late") == "on",
            allow_resubmit=request.POST.get("allow_resubmit") == "on",
            created_by=request.user,
        )
        return "Assignment saved."
    if action == "submit-review":
        if course.status not in {Course.Status.DRAFT, Course.Status.REJECTED}:
            raise LearningError("Only a draft or rejected course can be submitted for review.")
        course.status = Course.Status.IN_REVIEW
        course.save(update_fields=["status"])
        _save_revision(course, request.user)
        return "Submitted for review."
    if action == "approve" and can_publish(request.user):
        course.status = Course.Status.APPROVED
        course.review_note = (request.POST.get("note") or "")[:2000]
        course.save(update_fields=["status", "review_note"])
        return "Course approved. It is not published yet."
    if action == "reject" and can_publish(request.user):
        course.status = Course.Status.REJECTED
        course.review_note = (request.POST.get("note") or "")[:2000]
        course.save(update_fields=["status", "review_note"])
        return "Course returned to the author."
    if action == "publish" and can_publish(request.user):
        if course.status not in {Course.Status.APPROVED, Course.Status.PUBLISHED}:
            raise LearningError("Approve the course before publishing it.")
        course.status = Course.Status.PUBLISHED
        course.published_at = timezone.now()
        course.save(update_fields=["status", "published_at"])
        _save_revision(course, request.user)
        return "Course published."
    if action == "archive" and can_publish(request.user):
        course.status = Course.Status.ARCHIVED
        course.save(update_fields=["status"])
        return "Course archived."
    if action == "announcement":
        body = (request.POST.get("body") or "").strip()
        if body:
            Announcement.objects.create(course=course, author=request.user, body=body[:2000])
            for row in Enrolment.objects.filter(course=course).select_related("user"):
                from notifications.services import record_activity

                record_activity(row.user, "announcement", f"{course.title}: {body[:120]}")
        return "Announcement saved."
    raise LearningError("That studio action is not available.")


def _move(course, target, direction):
    kind, _, raw = (target or "").partition("-")
    delta = -1 if direction == "up" else 1
    if kind == "module":
        rows = list(course.modules.order_by("position"))
    else:
        module_id, lesson_id = raw.split(":")
        module = get_object_or_404(Module, pk=module_id, course=course)
        rows = list(module.lessons.order_by("position"))
        raw = lesson_id
    index = next((position for position, row in enumerate(rows) if str(row.pk) == raw), None)
    if index is None:
        return
    swap = index + delta
    if swap < 0 or swap >= len(rows):
        return
    rows[index], rows[swap] = rows[swap], rows[index]
    for position, row in enumerate(rows, start=1000):
        row.position = position
        row.save(update_fields=["position"])
    for position, row in enumerate(rows, start=1):
        row.position = position
        row.save(update_fields=["position"])


@member_required
@require_http_methods(["GET", "POST"])
def take_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment.objects.select_related("course"), pk=assessment_id)
    if not Enrolment.objects.filter(user=request.user, course=assessment.course).exists() and not can_edit_course(request.user, assessment.course):
        return HttpResponseForbidden("Enrol before opening this assessment.")
    notice = ""
    try:
        attempt = start_attempt(request.user, assessment)
    except LearningError as exc:
        return render(request, "app/assessment.html", {"assessment": assessment, "notice": exc.message, "attempt": None, "questions": []})
    if request.method == "POST" and attempt.status == Attempt.Status.STARTED:
        responses = {key.replace("q-", ""): value for key, value in request.POST.items() if key.startswith("q-")}
        try:
            attempt = grade_attempt(attempt, responses)
            notice = "Attempt submitted."
        except LearningError as exc:
            notice = exc.message
    questions = list(Question.objects.filter(pk__in=attempt.question_ids))
    order = {pk: index for index, pk in enumerate(attempt.question_ids)}
    questions.sort(key=lambda row: order.get(row.pk, 0))
    deadline = None
    if assessment.time_limit_minutes and attempt.status == Attempt.Status.STARTED:
        deadline = attempt.started_at + timedelta(minutes=assessment.time_limit_minutes)
    return render(request, "app/assessment.html", {
        "assessment": assessment,
        "attempt": attempt,
        "questions": questions,
        "notice": notice,
        "deadline": deadline,
        "answers": {row.question_id: row for row in attempt.answers.all()},
    })


@member_required
@require_http_methods(["POST"])
def mark_answer(request, answer_id):
    answer = get_object_or_404(AttemptAnswer.objects.select_related("attempt__assessment__course", "question"), pk=answer_id)
    if not can_edit_course(request.user, answer.attempt.assessment.course):
        raise Http404()
    try:
        record_manual_mark(request.user, answer, int(request.POST.get("awarded") or 0))
        notice = "Mark saved."
    except (LearningError, ValueError) as exc:
        notice = getattr(exc, "message", "Enter a whole number of marks.")
    return redirect(f"/app/assessments/{answer.attempt.assessment_id}/?notice={notice}")


@member_required
@require_http_methods(["POST"])
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment.objects.select_related("course"), pk=assignment_id)
    if not Enrolment.objects.filter(user=request.user, course=assignment.course).exists():
        return HttpResponseForbidden("Enrol before submitting this assignment.")
    existing = assignment.submissions.filter(user=request.user).first()
    if existing and not assignment.allow_resubmit:
        return HttpResponseForbidden("This assignment does not accept another submission.")
    late = bool(assignment.due_at and timezone.now() > assignment.due_at)
    if late and not assignment.allow_late:
        return HttpResponseForbidden("The due date has passed.")
    try:
        stored, original = save_submission_file(request.FILES.get("file"), assignment)
    except LearningError as exc:
        return HttpResponseForbidden(exc.message)
    if existing and assignment.allow_resubmit:
        existing.body = (request.POST.get("body") or "")[:8000]
        existing.stored_name = stored or existing.stored_name
        existing.original_name = original or existing.original_name
        existing.late = late
        existing.status = AssignmentSubmission.Status.SUBMITTED
        existing.score = None
        existing.feedback = ""
        existing.save()
    else:
        AssignmentSubmission.objects.create(
            assignment=assignment,
            user=request.user,
            body=(request.POST.get("body") or "")[:8000],
            stored_name=stored,
            original_name=original,
            late=late,
        )
    from notifications.services import record_activity

    record_activity(request.user, "assignment", f"Submitted {assignment.title}.")
    return redirect(f"/app/courses/{assignment.course.slug}/")


@member_required
@require_http_methods(["GET"])
def download_submission(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission.objects.select_related("assignment__course"), pk=submission_id)
    if not can_read_submission(request.user, submission) or not submission.stored_name:
        raise Http404()
    try:
        path = submission_file(submission.stored_name)
    except LearningError as exc:
        raise Http404() from exc
    return FileResponse(path.open("rb"), as_attachment=True, filename=submission.original_name or path.name)


@member_required
@require_http_methods(["POST"])
def review_course(request, slug):
    course = get_object_or_404(Course, slug=slug, status__in=[Course.Status.PREVIEW, Course.Status.PUBLISHED])
    if not Enrolment.objects.filter(user=request.user, course=course).exists():
        return HttpResponseForbidden("Enrol before reviewing this course.")
    try:
        rating = int(request.POST.get("rating") or 0)
    except ValueError:
        rating = 0
    if rating < 1 or rating > 5:
        return redirect(f"/app/courses/{slug}/")
    CourseReview.objects.update_or_create(
        course=course,
        user=request.user,
        defaults={"rating": rating, "body": (request.POST.get("body") or "")[:2000]},
    )
    return redirect(f"/app/courses/{slug}/")


@member_required
@require_http_methods(["POST"])
def create_path(request):
    if not is_platform_admin(request.user):
        raise Http404()
    title = (request.POST.get("title") or "").strip()
    if not title:
        return redirect("/app/paths/")
    base = slugify(title)[:60] or "path"
    slug = base
    number = 2
    while LearningPath.objects.filter(slug=slug).exists():
        slug = f"{base}-{number}"
        number += 1
    LearningPath.objects.create(
        slug=slug,
        title=title[:160],
        summary=(request.POST.get("summary") or "")[:2000],
        prerequisites=(request.POST.get("prerequisites") or "")[:2000],
        duration_label=(request.POST.get("duration") or "")[:40],
        certificate_eligible=request.POST.get("certificate") == "on",
        created_by=request.user,
        sort_order=500,
    )
    return redirect("/app/paths/")
