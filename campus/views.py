from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from campus.models import AcademicProgramme, Batch, Classroom, Department
from campus.services import (
    MANAGE,
    TEACH,
    CampusError,
    account_for,
    add_batch,
    add_classroom,
    add_competition,
    add_department,
    add_exam,
    allocate_account,
    instructor_lab_control,
    running_vm_count,
    set_deployment,
    used_vm_hours,
    visible_institutions,
)
from labs.models import Lab
from memberships.models import Invoice, Payment
from workspace.guards import member_required


def _context(row):
    institution = row.institution
    can_manage = row.role in MANAGE
    return {
        "institution": institution,
        "role": row.role,
        "can_manage": can_manage,
        "can_teach": row.role in TEACH,
        "can_bill": can_manage and institution.plan_id and institution.plan.has_entitlement("campus_billing"),
        "departments": institution.departments.all(),
        "batches": institution.batches.all(),
        "classrooms": institution.classrooms.select_related("department", "batch"),
        "accounts": institution.accounts.filter(active=True).select_related("user", "department"),
        "exams": institution.classrooms.prefetch_related("exams"),
        "competitions": institution.competitions.all(),
        "lab_controls": institution.lab_controls.select_related("lab")[:12],
        "labs": Lab.objects.all(),
        "vm_running": running_vm_count(institution),
        "vm_cap": institution.vm_cap(),
        "vm_hours_used": used_vm_hours(institution),
        "vm_hours_cap": institution.vm_hour_cap(),
        "seat_cap": institution.learner_cap(),
        "students": institution.accounts.filter(role="student", active=True).count(),
        "instructors": institution.accounts.filter(role="instructor", active=True).count(),
        "payments": Payment.objects.filter(institution=institution).order_by("-created_at"),
        "invoices": Invoice.objects.filter(institution=institution).order_by("-issued_at"),
        "subscription": institution.subscription,
        "programmes": institution.programmes.all(),
        "notice": "",
    }


@member_required
@require_http_methods(["GET"])
def campus_list(request):
    return render(request, "app/campus_list.html", {"institutions": visible_institutions(request.user)})


@member_required
@require_http_methods(["GET", "POST"])
def campus_centre(request, slug):
    try:
        row = account_for(request.user, slug)
    except CampusError as exc:
        return HttpResponseForbidden(exc.message)
    if row.role not in TEACH:
        return redirect("campus-study", slug=slug)
    notice = ""
    institution = row.institution
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action in {"department", "batch", "allocate", "deployment"} and row.role not in MANAGE:
                raise CampusError("Only an owner or administrator can change the institution.", status=403)
            if action == "deployment":
                set_deployment(request.user, institution, request.POST.get("deployment"))
                notice = "Deployment preference saved. No environment was provisioned."
            elif action == "programme":
                if row.role not in MANAGE:
                    raise CampusError("Only an owner or administrator can add a programme.", status=403)
                name = (request.POST.get("name") or "").strip()
                if not name:
                    raise CampusError("Enter a programme name.", status=400)
                AcademicProgramme.objects.get_or_create(
                    institution=institution,
                    name=name[:160],
                    defaults={"summary": (request.POST.get("summary") or "")[:2000]},
                )
                notice = "Academic programme saved."
            elif action == "department":
                add_department(request.user, institution, request.POST.get("name"))
                notice = "Department saved."
            elif action == "batch":
                department = None
                if request.POST.get("department"):
                    department = get_object_or_404(Department, pk=request.POST.get("department"), institution=institution)
                add_batch(request.user, institution, request.POST.get("name"), department)
                notice = "Batch saved."
            elif action == "classroom":
                department = batch = None
                if request.POST.get("department"):
                    department = get_object_or_404(Department, pk=request.POST.get("department"), institution=institution)
                if request.POST.get("batch"):
                    batch = get_object_or_404(Batch, pk=request.POST.get("batch"), institution=institution)
                add_classroom(request.user, institution, request.POST.get("name"), request.POST.get("kind"), department, batch)
                notice = "Classroom saved."
            elif action == "allocate":
                department = None
                if request.POST.get("department"):
                    department = get_object_or_404(Department, pk=request.POST.get("department"), institution=institution)
                allocate_account(request.user, institution, request.POST.get("username"), request.POST.get("role"), department)
                notice = "Account saved."
            elif action == "exam":
                classroom = get_object_or_404(Classroom, pk=request.POST.get("classroom"), institution=institution)
                add_exam(request.user, classroom, request.POST.get("title"))
                notice = "Examination saved."
            elif action == "competition":
                add_competition(request.user, institution, request.POST.get("name"), request.POST.get("kind"))
                notice = "Competition saved."
            elif action == "lab":
                if row.role not in TEACH:
                    raise CampusError("You cannot control labs for this campus.", status=403)
                lab = get_object_or_404(Lab, slug=request.POST.get("lab"))
                classroom = None
                if request.POST.get("classroom"):
                    classroom = get_object_or_404(Classroom, pk=request.POST.get("classroom"), institution=institution)
                instructor_lab_control(request.user, institution, lab, classroom)
                notice = "Lab control recorded."
            else:
                notice = "That action is not available."
        except CampusError as exc:
            notice = exc.message
    context = _context(row)
    context["notice"] = notice
    return render(request, "app/campus_centre.html", context)


@member_required
@require_http_methods(["GET"])
def campus_study(request, slug):
    try:
        row = account_for(request.user, slug)
    except CampusError as exc:
        return HttpResponseForbidden(exc.message)
    institution = row.institution
    return render(request, "app/campus_study.html", {
        "institution": institution,
        "classrooms": institution.classrooms.all(),
        "competitions": institution.competitions.all(),
    })
