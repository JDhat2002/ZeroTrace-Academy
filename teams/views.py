from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from learning.models import Course, LearningPath
from memberships.models import Invoice, Payment, UsageRecord
from teams.models import GroupPath, TeamAssignment, TeamCompetition, TeamCourse, TeamMember
from teams.services import (
    MANAGE,
    TEACH,
    TeamError,
    add_assignment,
    add_competition,
    allocate_member,
    assign_path,
    membership_for,
    release_member,
    visible_teams,
)
from workspace.guards import member_required


def _usage(team):
    user_ids = team.members.filter(active=True).values_list("user_id", flat=True)
    totals = {
        row["metric"]: row["total"]
        for row in UsageRecord.objects.filter(user_id__in=user_ids).values("metric").annotate(total=Sum("amount"))
    }
    return {
        "lab_minutes": totals.get("lab_minutes", 0) or 0,
        "vm_hours": totals.get(UsageRecord.Metric.VM_HOURS, 0) or 0,
        "vm_hour_cap": team.vm_hour_cap(),
        "vm_cap": team.vm_cap(),
        "learners": team.members.filter(role=TeamMember.Role.LEARNER, active=True).count(),
        "learner_cap": team.learner_cap(),
        "instructors": team.members.filter(role=TeamMember.Role.INSTRUCTOR, active=True).count(),
        "instructor_cap": team.instructor_cap(),
    }


def _centre_context(row):
    team = row.team
    can_manage = row.role in MANAGE
    return {
        "team": team,
        "role": row.role,
        "can_manage": can_manage,
        "can_teach": row.role in TEACH,
        "can_bill": can_manage and team.plan_id and team.plan.has_entitlement("team_billing"),
        "members": team.members.filter(active=True).select_related("user"),
        "paths": GroupPath.objects.filter(team=team).select_related("path"),
        "path_choices": LearningPath.objects.all(),
        "assignments": TeamAssignment.objects.filter(team=team),
        "competitions": TeamCompetition.objects.filter(team=team),
        "usage": _usage(team),
        "payments": Payment.objects.filter(team=team).order_by("-created_at"),
        "invoices": Invoice.objects.filter(team=team).order_by("-issued_at"),
        "subscription": team.subscription,
        "notice": "",
    }


@member_required
@require_http_methods(["GET"])
def team_list(request):
    return render(request, "app/team_list.html", {"teams": visible_teams(request.user)})


@member_required
@require_http_methods(["GET", "POST"])
def team_centre(request, slug):
    try:
        row = membership_for(request.user, slug)
    except TeamError as exc:
        return HttpResponseForbidden(exc.message)
    if row.role not in TEACH:
        return redirect("team-learn", slug=slug)
    notice = ""
    if request.method == "POST":
        if row.role not in TEACH:
            return HttpResponseForbidden("You cannot change this team.")
        action = request.POST.get("action")
        try:
            if action in {"allocate", "release"} and row.role not in MANAGE:
                raise TeamError("Only an owner or administrator can change seats.", status=403)
            if action == "allocate":
                allocate_member(request.user, row.team, request.POST.get("username"), request.POST.get("role"))
                notice = "Seat saved."
            elif action == "release":
                release_member(request.user, row.team, request.POST.get("member"))
                notice = "Seat released."
            elif action == "path":
                path = get_object_or_404(LearningPath, slug=request.POST.get("path"))
                assign_path(request.user, row.team, path)
                notice = "Learning path assigned to the team."
            elif action == "assignment":
                add_assignment(request.user, row.team, request.POST.get("title"), request.POST.get("brief"))
                notice = "Assignment saved."
            elif action == "competition":
                add_competition(request.user, row.team, request.POST.get("name"))
                notice = "Competition saved."
            elif action == "course":
                if row.role not in MANAGE:
                    raise TeamError("Only an owner or administrator can assign a team course.", status=403)
                course = get_object_or_404(
                    Course,
                    slug=request.POST.get("course"),
                    status__in=[Course.Status.PREVIEW, Course.Status.PUBLISHED],
                )
                TeamCourse.objects.get_or_create(
                    team=row.team,
                    course=course,
                    defaults={"assigned_by": request.user, "mandatory": request.POST.get("mandatory") == "on"},
                )
                notice = "Course assigned to this team. Billing for the team is unchanged."
            else:
                notice = "That action is not available."
        except TeamError as exc:
            notice = exc.message
    context = _centre_context(row)
    context["notice"] = notice
    context["assigned_courses"] = row.team.assigned_courses.select_related("course")
    context["course_choices"] = Course.objects.filter(status__in=[Course.Status.PREVIEW, Course.Status.PUBLISHED]).order_by("title")
    return render(request, "app/team_centre.html", context)


@member_required
@require_http_methods(["GET"])
def team_learn(request, slug):
    try:
        row = membership_for(request.user, slug)
    except TeamError as exc:
        return HttpResponseForbidden(exc.message)
    team = row.team
    return render(request, "app/team_learn.html", {
        "team": team,
        "paths": GroupPath.objects.filter(team=team).select_related("path"),
        "assignments": TeamAssignment.objects.filter(team=team),
        "competitions": TeamCompetition.objects.filter(team=team),
        "assigned_courses": team.assigned_courses.select_related("course"),
    })
