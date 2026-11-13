from django.db.models import Sum
from django.http import Http404

from accounts.models import User
from campus.models import (
    Batch,
    CampusAccount,
    CampusCompetition,
    CampusSeat,
    Classroom,
    Department,
    Institution,
    LabControl,
    PracticalExam,
)
from labs.models import VirtualMachine
from labs.services import LabError, start_lab
from memberships.billing import audit
from memberships.models import UsageRecord

MANAGE = {CampusAccount.Role.OWNER, CampusAccount.Role.ADMINISTRATOR}
TEACH = MANAGE | {CampusAccount.Role.INSTRUCTOR}


class CampusError(Exception):
    def __init__(self, message, status=403):
        super().__init__(message)
        self.message = message
        self.status = status


def account_for(user, slug):
    row = (
        CampusAccount.objects.select_related("institution", "institution__plan", "institution__subscription")
        .filter(user=user, institution__slug=slug, active=True)
        .first()
    )
    if row is None:
        raise Http404()
    if row.institution.status != Institution.Status.ACTIVE:
        raise CampusError("This campus subscription is not active.", status=403)
    return row


def visible_institutions(user):
    return (
        Institution.objects.filter(accounts__user=user, accounts__active=True, status=Institution.Status.ACTIVE)
        .distinct()
        .order_by("name")
    )


def _plan(institution):
    if institution.plan_id is None:
        raise CampusError("No campus plan is attached.", status=409)
    return institution.plan


def set_deployment(actor, institution, mode):
    _plan(institution)
    if not institution.plan.has_entitlement("deployment_choice"):
        raise CampusError("This campus plan does not include a deployment choice.", status=403)
    if mode not in dict(Institution.Deployment.choices):
        raise CampusError("Choose cloud, on-premises, or hybrid.", status=400)
    institution.deployment = mode
    institution.save(update_fields=["deployment"])
    audit("campus_deployment_set", user=actor, category="campus", detail={"institution": institution.pk, "deployment": mode})
    return institution


def add_department(actor, institution, name):
    _plan(institution)
    if not institution.plan.has_entitlement("departments"):
        raise CampusError("This campus plan does not include departments.", status=403)
    name = (name or "").strip()
    if not name:
        raise CampusError("Enter a department name.", status=400)
    row, created = Department.objects.get_or_create(institution=institution, name=name[:120])
    if not created:
        raise CampusError("That department already exists.", status=409)
    audit("campus_department_created", user=actor, category="campus", detail={"institution": institution.pk, "department": row.pk})
    return row


def add_batch(actor, institution, name, department):
    _plan(institution)
    if not institution.plan.has_entitlement("batches"):
        raise CampusError("This campus plan does not include batches.", status=403)
    name = (name or "").strip()
    if not name:
        raise CampusError("Enter a batch name.", status=400)
    if department and department.institution_id != institution.id:
        raise CampusError("That department is not part of this institution.", status=404)
    row, created = Batch.objects.get_or_create(institution=institution, name=name[:80], defaults={"department": department})
    if not created:
        raise CampusError("That batch already exists.", status=409)
    audit("campus_batch_created", user=actor, category="campus", detail={"institution": institution.pk, "batch": row.pk})
    return row


def add_classroom(actor, institution, name, kind, department, batch):
    _plan(institution)
    if kind == Classroom.Kind.SOC and not institution.plan.has_entitlement("soc_classrooms"):
        raise CampusError("This campus plan does not include SOC classrooms.", status=403)
    if kind == Classroom.Kind.FORENSICS and not institution.plan.has_entitlement("forensics_classrooms"):
        raise CampusError("This campus plan does not include forensics classrooms.", status=403)
    if not institution.plan.has_entitlement("classrooms"):
        raise CampusError("This campus plan does not include classrooms.", status=403)
    name = (name or "").strip()
    if not name:
        raise CampusError("Enter a classroom name.", status=400)
    if kind not in dict(Classroom.Kind.choices):
        raise CampusError("Choose a classroom type.", status=400)
    if department and department.institution_id != institution.id:
        raise CampusError("That department is not part of this institution.", status=404)
    if batch and batch.institution_id != institution.id:
        raise CampusError("That batch is not part of this institution.", status=404)
    row = Classroom.objects.create(
        institution=institution,
        name=name[:160],
        kind=kind,
        department=department,
        batch=batch,
    )
    audit("campus_classroom_created", user=actor, category="campus", detail={"institution": institution.pk, "classroom": row.pk, "kind": kind})
    return row


def allocate_account(actor, institution, username, role, department=None):
    _plan(institution)
    if role not in {CampusAccount.Role.STUDENT, CampusAccount.Role.INSTRUCTOR}:
        raise CampusError("Choose a student or an instructor.", status=400)
    if not institution.plan.has_entitlement("campus_accounts"):
        raise CampusError("This campus plan does not include institutional accounts.", status=403)
    person = User.objects.filter(username__iexact=(username or "").strip()).first()
    if person is None:
        raise CampusError("No account uses that username.", status=404)
    if department and department.institution_id != institution.id:
        raise CampusError("That department is not part of this institution.", status=404)
    if CampusAccount.objects.filter(institution=institution, user=person, active=True).exists():
        raise CampusError("That account is already on this campus.", status=409)
    if role == CampusAccount.Role.STUDENT:
        cap = institution.learner_cap()
        used = CampusAccount.objects.filter(institution=institution, role=CampusAccount.Role.STUDENT, active=True).count()
        if cap is None or used >= cap:
            raise CampusError("Institutional seats for this campus are full.", status=409)
    else:
        cap = institution.instructor_cap()
        used = CampusAccount.objects.filter(institution=institution, role=CampusAccount.Role.INSTRUCTOR, active=True).count()
        if cap is None or used >= cap:
            raise CampusError("Instructor accounts for this campus are full.", status=409)
    row = CampusAccount.objects.create(institution=institution, user=person, role=role, department=department, active=True)
    if role == CampusAccount.Role.STUDENT:
        CampusSeat.objects.update_or_create(
            user=person,
            defaults={
                "institution": institution.name,
                "institution_link": institution,
                "department": department.name if department else "",
                "active": True,
            },
        )
    audit("campus_seat_allocated", user=actor, category="campus", detail={"institution": institution.pk, "account": person.pk, "role": role})
    return row


def add_exam(actor, classroom, title):
    institution = classroom.institution
    _plan(institution)
    if not institution.plan.has_entitlement("exams"):
        raise CampusError("This campus plan does not include practical examinations.", status=403)
    title = (title or "").strip()
    if not title:
        raise CampusError("Enter an examination title.", status=400)
    row = PracticalExam.objects.create(classroom=classroom, title=title[:160], created_by=actor)
    audit("campus_exam_created", user=actor, category="campus", detail={"institution": institution.pk, "exam": row.pk})
    return row


def add_competition(actor, institution, name, kind):
    _plan(institution)
    if not institution.plan.has_entitlement("campus_ctf"):
        raise CampusError("This campus plan does not include competitions.", status=403)
    name = (name or "").strip()
    if not name:
        raise CampusError("Enter a competition name.", status=400)
    if kind not in dict(CampusCompetition.Kind.choices):
        raise CampusError("Choose a competition type.", status=400)
    row = CampusCompetition.objects.create(institution=institution, name=name[:160], kind=kind, created_by=actor)
    audit("campus_competition_created", user=actor, category="campus", detail={"institution": institution.pk, "competition": row.pk})
    return row


def running_vm_count(institution):
    user_ids = institution.accounts.filter(active=True).values_list("user_id", flat=True)
    return VirtualMachine.objects.filter(
        session__user_id__in=user_ids,
        status=VirtualMachine.Status.RUNNING,
    ).count()


def used_vm_hours(institution):
    user_ids = institution.accounts.filter(active=True).values_list("user_id", flat=True)
    total = UsageRecord.objects.filter(user_id__in=user_ids, metric=UsageRecord.Metric.VM_HOURS).aggregate(total=Sum("amount"))
    return total["total"] or 0


def instructor_lab_control(actor, institution, lab, classroom=None):
    _plan(institution)
    if not institution.plan.has_entitlement("instructor_labs"):
        raise CampusError("This campus plan does not include instructor lab controls.", status=403)
    if not institution.plan.has_entitlement("vm_controls"):
        raise CampusError("This campus plan does not include VM controls.", status=403)
    if running_vm_count(institution) >= institution.vm_cap():
        LabControl.objects.create(
            institution=institution,
            classroom=classroom,
            instructor=actor,
            lab=lab,
            action="start",
            outcome="refused",
            detail="Concurrent VM limit reached.",
        )
        raise CampusError("The concurrent VM limit for this campus has been reached.", status=409)
    if used_vm_hours(institution) >= institution.vm_hour_cap():
        LabControl.objects.create(
            institution=institution,
            classroom=classroom,
            instructor=actor,
            lab=lab,
            action="start",
            outcome="refused",
            detail="VM-hour allowance reached.",
        )
        raise CampusError("The VM-hour allowance for this campus has been reached.", status=409)
    try:
        start_lab(actor, lab)
        outcome = "recorded"
        detail = "Start was accepted."
        error = None
    except LabError as exc:
        outcome = "refused"
        detail = exc.message
        error = exc
    LabControl.objects.create(
        institution=institution,
        classroom=classroom,
        instructor=actor,
        lab=lab,
        action="start",
        outcome=outcome,
        detail=detail[:200],
    )
    audit("campus_lab_control", user=actor, category="campus", detail={"institution": institution.pk, "lab": lab.slug, "outcome": outcome})
    if error:
        raise CampusError(error.message, status=error.status)
