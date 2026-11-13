from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from labs.models import Lab, LabSession, VirtualMachine
from labs.services import LabError, start_lab
from learning.models import Course, Enrolment, LearningPath, Lesson
from learning.query import catalogue, catalogue_filters
from learning.services import (
    LearningError,
    complete_lesson,
    enrol,
    goal_for,
    learner_snapshot,
    learning_tab,
    next_lesson,
    progress_breakdown,
    progress_percent,
    recommendations,
    save_goal,
)
from learning.access import can_edit_course
from memberships.models import Invoice, Payment
from memberships.services import MembershipError, current_plan, ensure_subscription, individual_plans, request_plan_change, usage_summary
from notifications.models import ActivityEvent, Notification, PrivacyRequest, SupportRequest
from notifications.services import mark_read
from practice.models import Challenge, ForensicCase, ForensicTrack, Investigation, SocModule, Submission, Tool
from practice.services import PracticeError, launch_tool, submit_flag
from workspace.guards import member_required
from workspace.services import daily_message, dashboard_metrics, heatmap, week_bars


@member_required
@require_http_methods(["GET", "POST"])
def home(request):
    error = ""
    if request.method == "POST":
        try:
            save_goal(request.user, request.POST.get("daily_minutes"), request.POST.get("weekly_days"))
        except (LearningError, ValueError) as exc:
            error = getattr(exc, "message", "Choose a target from the list.")
    metrics = dashboard_metrics(request.user)
    enrolments = (
        Enrolment.objects.filter(user=request.user)
        .select_related("course")
        .order_by("-last_accessed_at", "-enrolled_at")[:4]
    )
    continue_rows = [
        {"enrolment": row, "percent": progress_percent(row), "next": next_lesson(row)}
        for row in enrolments
    ]
    first = (request.user.full_name or "there").split()[0]
    return render(request, "app/home.html", {
        "first_name": first,
        "metrics": metrics,
        "message": daily_message(request.user, metrics),
        "continue_rows": continue_rows,
        "recommended": recommendations(request.user),
        "goal": goal_for(request.user),
        "bars": week_bars(request.user),
        "error": error,
        "snapshot": learner_snapshot(request.user),
    })


@member_required
@require_http_methods(["GET"])
def learning(request):
    tab = request.GET.get("tab", "all")
    if tab not in {"all", "progress", "new", "completed", "saved"}:
        tab = "all"
    rows = []
    for enrolment in learning_tab(request.user, tab).select_related("course"):
        rows.append({"enrolment": enrolment, "percent": progress_percent(enrolment), "next": next_lesson(enrolment)})
    return render(request, "app/learning.html", {"tab": tab, "rows": rows})


@member_required
@require_http_methods(["GET"])
def courses(request):
    filters = catalogue_filters()
    return render(request, "app/courses.html", {
        "courses": catalogue(request.GET),
        "filters": filters,
        "params": request.GET,
    })


@member_required
@require_http_methods(["GET", "POST"])
def course_detail(request, slug):
    course = get_object_or_404(Course.objects.prefetch_related("modules__lessons"), slug=slug)
    if course.status not in {Course.Status.PREVIEW, Course.Status.PUBLISHED} and not can_edit_course(request.user, course):
        raise Http404()
    enrolment = Enrolment.objects.filter(user=request.user, course=course).first()
    notice = ""
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "enrol":
                enrolment = enrol(request.user, course)
                notice = "Enrolment saved."
            elif action == "save":
                enrolment = enrol(request.user, course)
                enrolment.saved = not enrolment.saved
                enrolment.save(update_fields=["saved"])
            elif action == "complete":
                lesson = get_object_or_404(Lesson, pk=request.POST.get("lesson"), module__course=course)
                enrolment = complete_lesson(request.user, lesson)
                notice = "Lesson recorded."
        except LearningError as exc:
            notice = exc.message
    breakdown = progress_breakdown(course, enrolment)
    done_lessons = []
    if enrolment:
        done_lessons = list(
            enrolment.lesson_progress.filter(completed_at__isnull=False).values_list("lesson_id", flat=True)
        )
    reviews = course.reviews.all()
    ratings = [row.rating for row in reviews]
    return render(request, "app/course.html", {
        "course": course,
        "enrolment": enrolment,
        "breakdown": breakdown,
        "notice": notice,
        "done_lessons": done_lessons,
        "reviews": reviews,
        "review_average": round(sum(ratings) / len(ratings), 1) if ratings else None,
        "assignments": course.course_assignments.all(),
        "assessments": course.assessments.filter(status="published"),
        "announcements": course.announcements.all()[:5],
    })


@member_required
@require_http_methods(["GET"])
def paths(request):
    return render(request, "app/paths.html", {"paths": LearningPath.objects.prefetch_related("steps__course")})


@member_required
@require_http_methods(["GET"])
def path_detail(request, slug):
    path = get_object_or_404(LearningPath.objects.prefetch_related("steps__course"), slug=slug)
    return render(request, "app/path.html", {"path": path})


@member_required
@require_http_methods(["GET", "POST"])
def labs(request):
    notice = ""
    if request.method == "POST":
        lab = get_object_or_404(Lab, slug=request.POST.get("lab"))
        try:
            start_lab(request.user, lab)
        except LabError as exc:
            notice = exc.message
    return render(request, "app/labs.html", {"labs": Lab.objects.all(), "notice": notice})


@member_required
@require_http_methods(["GET"])
def lab_history(request):
    return render(request, "app/list.html", {
        "title": "Lab history",
        "intro": "Only sessions this server actually recorded are listed. A refused start is not a running machine.",
        "rows": [
            {"title": row.lab.name, "meta": row.get_status_display(), "detail": row.detail}
            for row in LabSession.objects.filter(user=request.user).select_related("lab")
        ],
        "empty": "No lab session has been recorded.",
    })


@member_required
@require_http_methods(["GET"])
def machines(request):
    rows = VirtualMachine.objects.filter(session__user=request.user).select_related("session__lab")
    return render(request, "app/list.html", {
        "title": "My virtual machines",
        "intro": "The hypervisor is not connected. This list stays empty until a machine is created by the server.",
        "rows": [{"title": row.name, "meta": row.get_status_display(), "detail": row.operating_system} for row in rows],
        "empty": "No virtual machine is assigned.",
    })


@member_required
@require_http_methods(["GET"])
def range_page(request):
    metrics = dashboard_metrics(request.user)
    return render(request, "app/range.html", {"metrics": metrics, "sessions": LabSession.objects.filter(user=request.user)[:8]})


@member_required
@require_http_methods(["GET", "POST"])
def tools(request):
    from django.db.models import Q

    category = request.GET.get("category", "")
    query = (request.GET.get("q") or "").strip()
    rows = Tool.objects.all()
    if category:
        rows = rows.filter(category_key=category)
    if query:
        rows = rows.filter(Q(name__icontains=query) | Q(summary__icontains=query))
    notice = ""
    if request.method == "POST":
        tool = get_object_or_404(Tool, slug=request.POST.get("tool"))
        try:
            launch_tool(request.user, tool)
        except PracticeError as exc:
            notice = exc.message
    return render(request, "app/tools.html", {"tools": rows, "category": category, "notice": notice})


@member_required
@require_http_methods(["GET"])
def tool_detail(request, slug):
    return render(request, "app/tool.html", {"tool": get_object_or_404(Tool, slug=slug)})


@member_required
@require_http_methods(["GET"])
def soc(request):
    return render(request, "app/centre.html", {
        "title": "SOC Centre",
        "intro": "These are training outlines. No live security alerts are loaded.",
        "items": SocModule.objects.all(),
        "cases": Investigation.objects.filter(user=request.user),
        "case_empty": "No investigation is assigned.",
        "stats": {
            "Investigations": Investigation.objects.filter(user=request.user).count(),
            "Resolved": Investigation.objects.filter(user=request.user, status=Investigation.Status.RESOLVED).count(),
        },
    })


@member_required
@require_http_methods(["GET"])
def forensics(request):
    return render(request, "app/centre.html", {
        "title": "Digital Forensics Centre",
        "intro": "Categories are listed for the curriculum. No evidence image is stored, and nothing here is a live case.",
        "items": ForensicTrack.objects.all(),
        "cases": ForensicCase.objects.filter(user=request.user),
        "case_empty": "No forensic case is assigned.",
        "stats": {"Cases": ForensicCase.objects.filter(user=request.user).count()},
    })


@member_required
@require_http_methods(["GET", "POST"])
def ctf(request):
    notice = ""
    if request.method == "POST":
        challenge = get_object_or_404(Challenge, slug=request.POST.get("challenge"))
        try:
            correct = submit_flag(request.user, challenge, request.POST.get("flag"))
            notice = "Flag accepted." if correct else "That flag was not accepted."
        except PracticeError as exc:
            notice = exc.message
    solved = Submission.objects.filter(user=request.user, correct=True).count()
    return render(request, "app/ctf.html", {
        "challenges": Challenge.objects.all(),
        "solved": solved,
        "notice": notice,
    })


@member_required
@require_http_methods(["GET"])
def membership(request):
    subscription = ensure_subscription(request.user)
    return render(request, "app/membership.html", {
        "plans": individual_plans(),
        "current": current_plan(request.user),
        "subscription": subscription,
        "notice": "",
    })


@member_required
@require_http_methods(["POST"])
def membership_select(request):
    try:
        request_plan_change(request.user, request.POST.get("plan"))
        notice = "Plan updated."
    except MembershipError as exc:
        notice = exc.message
    return render(request, "app/membership.html", {
        "plans": individual_plans(),
        "current": current_plan(request.user),
        "subscription": ensure_subscription(request.user),
        "notice": notice,
    })


@member_required
@require_http_methods(["GET"])
def billing(request):
    subscription = ensure_subscription(request.user)
    payments = Payment.objects.filter(
        user=request.user,
        category=Payment.Category.INDIVIDUAL,
        team__isnull=True,
        institution__isnull=True,
    )
    renewal = "No paid renewal is scheduled."
    if subscription and subscription.contracted_price_inr is not None and subscription.plan.price_inr:
        from memberships.money import format_inr

        renewal = (
            f"Renewal uses the contracted {subscription.get_billing_interval_display().lower()} price of "
            f"{format_inr(subscription.contracted_price_inr)}."
        )
    return render(request, "app/list.html", {
        "title": "Billing and payments",
        "intro": "This list is your individual membership only. Team and campus invoices stay in those workspaces. A payment appears here only after the server confirms it.",
        "rows": [
            {"title": row.provider_reference or f"Payment {row.pk}", "meta": row.get_status_display(), "detail": f"₹{row.amount_inr}"}
            for row in payments
        ],
        "empty": "No individual payment has been recorded.",
        "extra": f"Individual invoices on file: {Invoice.objects.filter(payment__in=payments).count()}. {renewal}",
    })


@member_required
@require_http_methods(["GET"])
def usage(request):
    return render(request, "app/usage.html", {"rows": usage_summary(request.user), "plan": current_plan(request.user)})


@member_required
@require_http_methods(["GET", "POST"])
def notifications(request):
    if request.method == "POST":
        mark_read(request.user, request.POST.get("id") or None)
    category = request.GET.get("category", "")
    rows = Notification.objects.filter(user=request.user)
    if category:
        rows = rows.filter(category=category)
    return render(request, "app/notifications.html", {"rows": rows[:50], "category": category})


@member_required
@require_http_methods(["GET"])
def activity(request):
    category = request.GET.get("category", "")
    rows = ActivityEvent.objects.filter(user=request.user)
    if category:
        rows = rows.filter(category=category)
    return render(request, "app/activity.html", {"rows": rows[:80], "category": category})


@member_required
@require_http_methods(["GET"])
def calendar(request):
    return render(request, "app/calendar.html", {"cells": heatmap(request.user), "bars": week_bars(request.user), "metrics": dashboard_metrics(request.user)})


@member_required
@require_http_methods(["GET"])
def career(request):
    metrics = dashboard_metrics(request.user)
    return render(request, "app/career.html", {
        "metrics": metrics,
        "paths": LearningPath.objects.all(),
        "certificates": request.user.certificates.select_related("course"),
    })


@member_required
@require_http_methods(["GET"])
def certifications(request):
    return render(request, "app/list.html", {
        "title": "Certifications",
        "intro": "A certificate is created only after a published course reaches the documented completion rule. Preview outlines do not qualify.",
        "rows": [
            {"title": row.course.title, "meta": row.issued_at.date().isoformat(), "detail": row.credential_id}
            for row in request.user.certificates.select_related("course")
        ],
        "empty": "No certificate has been issued.",
    })


@member_required
@require_http_methods(["GET", "POST"])
def preferences(request):
    error = ""
    if request.method == "POST":
        try:
            save_goal(request.user, request.POST.get("daily_minutes"), request.POST.get("weekly_days"))
        except (LearningError, ValueError) as exc:
            error = getattr(exc, "message", "Choose a target from the list.")
    return render(request, "app/preferences.html", {"goal": goal_for(request.user), "error": error})


@member_required
@require_http_methods(["GET", "POST"])
def support(request):
    notice = ""
    if request.method == "POST":
        subject = (request.POST.get("subject") or "").strip()
        body = (request.POST.get("body") or "").strip()
        if subject and body:
            SupportRequest.objects.create(user=request.user, subject=subject[:120], body=body[:4000])
            notice = "Request saved. It is not sent to an outside desk yet."
        else:
            notice = "Enter a subject and a message."
    return render(request, "app/support.html", {
        "notice": notice,
        "rows": SupportRequest.objects.filter(user=request.user)[:10],
    })


@member_required
@require_http_methods(["POST"])
def privacy(request):
    kind = request.POST.get("kind")
    if kind not in {"export", "deletion"}:
        raise Http404()
    PrivacyRequest.objects.create(user=request.user, kind=kind)
    if kind == "deletion":
        return redirect("/app/support/")
    payload = {
        "email": request.user.email,
        "full_name": request.user.full_name,
        "membership": request.user.membership,
        "enrolments": list(Enrolment.objects.filter(user=request.user).values_list("course__title", flat=True)),
    }
    return JsonResponse(payload)


def verify_certificate(request, credential_id):
    from learning.models import Certificate

    certificate = Certificate.objects.select_related("course", "user").filter(credential_id=credential_id).first()
    return render(request, "app/verify.html", {"certificate": certificate})


@member_required
def panel(request, title, intro, rows, empty):
    return render(request, "app/list.html", {"title": title, "intro": intro, "rows": rows, "empty": empty})


@member_required
def assignments(request):
    lessons = Lesson.objects.filter(kind=Lesson.Kind.ASSIGNMENT)
    return panel(request, "Assignments", "Assignments appear when a published course includes them.", [
        {"title": lesson.title, "meta": lesson.module.course.title, "detail": "Not submitted"} for lesson in lessons
    ], "No assignment is published.")


@member_required
def assessments(request):
    lessons = Lesson.objects.filter(kind=Lesson.Kind.QUIZ)
    return panel(request, "Assessments", "Quiz scores are stored only after a quiz exists on a published course.", [
        {"title": lesson.title, "meta": lesson.module.course.title, "detail": "No attempt"} for lesson in lessons
    ], "No assessment is published.")


@member_required
def arena(request):
    return panel(request, "Attack and defence", "No isolated exercise is scheduled. This page does not simulate a live network.", [], "No exercise is available.")


@member_required
def malware(request):
    return panel(
        request,
        "Malware Research Centre",
        "Sample analysis stays closed until an isolated lab is connected. No sample is stored.",
        [{"title": row.name, "meta": row.get_status_display(), "detail": row.summary} for row in Tool.objects.filter(category_key="malware")],
        "No malware tool is available.",
    )


@member_required
def intel(request):
    return panel(
        request,
        "Threat Intelligence Centre",
        "No feed is connected. Tool entries below are catalogue records.",
        [{"title": row.name, "meta": row.get_status_display(), "detail": row.summary} for row in Tool.objects.filter(category_key="intel")],
        "No intelligence source is connected.",
    )


@member_required
def portfolio(request):
    return panel(request, "Projects and portfolio", "Completed published work will be listed here. Preview lessons are not portfolio evidence.", [], "No project is recorded.")


@member_required
def jobs(request):
    return panel(
        request,
        "Job preparation",
        "This is study planning only. ZeroTrace does not place candidates or guarantee employment.",
        [{"title": path.title, "meta": path.duration_label, "detail": path.summary, "href": f"/app/paths/{path.slug}/"} for path in LearningPath.objects.all()],
        "No roadmap is loaded.",
    )
