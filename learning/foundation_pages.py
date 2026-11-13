from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from learning.foundation_content import DIAGNOSTIC, recommend_start
from learning.models import (
    AcademyDepartment,
    FoundationLevel,
    GlossaryBookmark,
    GlossaryTerm,
    LearnerPlacement,
    LessonProgress,
)
from learning.services import LearningError, enrol, maybe_issue_certificate
from workspace.guards import member_required


@member_required
@require_http_methods(["GET"])
def foundations_home(request):
    from learning.models import Course

    course = Course.objects.filter(slug="zerotrace-foundations").first()
    placement = LearnerPlacement.objects.filter(user=request.user).first()
    return render(request, "app/foundations.html", {
        "course": course,
        "levels": FoundationLevel.objects.all(),
        "placement": placement,
        "departments": AcademyDepartment.objects.all(),
    })


@member_required
@require_http_methods(["GET", "POST"])
def foundation_level(request, slug):
    level = get_object_or_404(FoundationLevel.objects.select_related("lesson__module__course"), slug=slug)
    notice = ""
    if request.method == "POST" and level.lesson_id:
        try:
            enrol(request.user, level.lesson.module.course)
            from learning.services import complete_lesson

            complete_lesson(request.user, level.lesson)
            notice = "Level recorded."
        except LearningError as exc:
            notice = exc.message
    done = False
    if level.lesson_id:
        done = LessonProgress.objects.filter(
            enrolment__user=request.user,
            lesson=level.lesson,
            completed_at__isnull=False,
        ).exists()
    return render(request, "app/foundation_level.html", {"level": level, "notice": notice, "done": done})


@member_required
@require_http_methods(["GET", "POST"])
def foundation_glossary(request):
    if request.method == "POST":
        term = get_object_or_404(GlossaryTerm, slug=request.POST.get("term"))
        mark = GlossaryBookmark.objects.filter(user=request.user, term=term).first()
        if mark:
            mark.delete()
        else:
            GlossaryBookmark.objects.create(user=request.user, term=term)
        return redirect(request.get_full_path())
    query = (request.GET.get("q") or "").strip()
    terms = GlossaryTerm.objects.all()
    if query:
        terms = terms.filter(Q(term__icontains=query) | Q(explanation__icontains=query))
    bookmarked = set(GlossaryBookmark.objects.filter(user=request.user).values_list("term_id", flat=True))
    return render(request, "app/glossary.html", {"terms": terms, "query": query, "bookmarked": bookmarked})


@member_required
@require_http_methods(["GET", "POST"])
def foundation_placement(request):
    placement = LearnerPlacement.objects.filter(user=request.user).first()
    notice = ""
    if request.method == "POST":
        computer = _familiar(request.POST.get("computer"))
        programming = _familiar(request.POST.get("programming"))
        networking = _familiar(request.POST.get("networking"))
        correct = 0
        for index, question in enumerate(DIAGNOSTIC):
            try:
                chosen = int(request.POST.get(f"q{index}", -1))
            except ValueError:
                chosen = -1
            if chosen == question["correct"]:
                correct += 1
        start = recommend_start(computer, programming, networking, correct, len(DIAGNOSTIC))
        placement, _created = LearnerPlacement.objects.update_or_create(
            user=request.user,
            defaults={
                "computer": computer,
                "programming": programming,
                "networking": networking,
                "diagnostic_score": correct,
                "diagnostic_total": len(DIAGNOSTIC),
                "start_level": start,
                "credited": False,
            },
        )
        if request.POST.get("apply") == "yes":
            _credit(request.user, start)
            placement.credited = True
            placement.save(update_fields=["credited"])
            notice = "Earlier levels were recorded as already understood. Ethics, terminology, labs, the capstone, and the exam remain."
        else:
            notice = "Starting point saved. You can still open every earlier level."
    return render(request, "app/placement.html", {
        "placement": placement,
        "questions": list(enumerate(DIAGNOSTIC)),
        "notice": notice,
    })


def _familiar(value):
    if value in {"none", "some", "comfortable"}:
        return value
    return "none"


def _credit(user, start_level):
    from learning.models import Course

    course = Course.objects.filter(slug="zerotrace-foundations").first()
    if course is None:
        return
    enrolment = enrol(user, course)
    limit = min(start_level, 6)
    from django.utils import timezone

    for level in FoundationLevel.objects.filter(number__lt=limit, lesson__isnull=False).select_related("lesson"):
        LessonProgress.objects.update_or_create(
            enrolment=enrolment,
            lesson=level.lesson,
            defaults={"completed_at": timezone.now()},
        )
    maybe_issue_certificate(enrolment)


@member_required
@require_http_methods(["GET", "POST"])
def grade_submission(request, submission_id):
    from learning.access import can_review_submission
    from learning.models import AssignmentSubmission

    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related("assignment__course", "assignment__lesson"),
        pk=submission_id,
    )
    if not can_review_submission(request.user, submission):
        return HttpResponseForbidden("You cannot grade this submission.")
    notice = ""
    if request.method == "POST":
        try:
            score = int(request.POST.get("score") or 0)
        except ValueError:
            score = -1
        if score < 0 or score > submission.assignment.max_marks:
            notice = "Enter a score inside the assignment total."
        else:
            submission.score = score
            submission.feedback = (request.POST.get("feedback") or "")[:4000]
            submission.status = AssignmentSubmission.Status.GRADED
            submission.reviewer = request.user
            submission.save(update_fields=["score", "feedback", "status", "reviewer"])
            notice = "Grade saved. The learner can then mark the assignment lesson complete."
    return render(request, "app/grade_submission.html", {"submission": submission, "notice": notice})
