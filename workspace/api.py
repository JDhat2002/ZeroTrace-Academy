from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from labs.models import Lab
from labs.services import LabError, start_lab
from learning.models import Course, Lesson
from learning.services import LearningError, complete_lesson, enrol
from memberships.services import MembershipError, current_plan, request_plan_change, usage_summary
from notifications.models import Notification
from notifications.services import mark_read
from practice.models import Tool
from practice.services import PracticeError, launch_tool
from workspace.services import dashboard_metrics


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    metrics = dashboard_metrics(request.user)
    plan = current_plan(request.user)
    return Response({"plan": plan.code if plan else "free", "metrics": metrics})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enrol_api(request):
    course = get_object_or_404(Course, slug=request.data.get("course"))
    enrolment = enrol(request.user, course)
    return Response({"enrolled": enrolment.course.slug})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def progress_api(request):
    lesson = get_object_or_404(Lesson, pk=request.data.get("lesson"))
    try:
        enrolment = complete_lesson(request.user, lesson)
    except LearningError as exc:
        return Response({"detail": exc.message}, status=exc.status)
    from learning.services import progress_percent

    return Response({"percent": progress_percent(enrolment)})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def membership_api(request):
    if request.method == "GET":
        plan = current_plan(request.user)
        return Response({"plan": plan.code if plan else None, "usage": usage_summary(request.user)})
    try:
        request_plan_change(request.user, request.data.get("plan"))
    except MembershipError as exc:
        return Response({"detail": exc.message}, status=exc.status)
    return Response({"detail": "Plan updated."})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def notifications_api(request):
    if request.method == "POST":
        mark_read(request.user, request.data.get("id"))
    rows = Notification.objects.filter(user=request.user)[:30]
    return Response([
        {"id": row.pk, "category": row.category, "summary": row.summary, "read": bool(row.read_at)}
        for row in rows
    ])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def lab_api(request):
    lab = get_object_or_404(Lab, slug=request.data.get("lab"))
    try:
        start_lab(request.user, lab)
    except LabError as exc:
        return Response({"detail": exc.message}, status=exc.status)
    return Response({"detail": "Started."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tool_api(request):
    tool = get_object_or_404(Tool, slug=request.data.get("tool"))
    try:
        launch_tool(request.user, tool)
    except PracticeError as exc:
        return Response({"detail": exc.message}, status=exc.status)
    return Response({"detail": "Launched."})
