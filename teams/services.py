from django.http import Http404

from accounts.models import User
from memberships.billing import audit
from teams.models import GroupPath, Team, TeamAssignment, TeamCompetition, TeamMember

MANAGE = {TeamMember.Role.OWNER, TeamMember.Role.ADMINISTRATOR}
TEACH = MANAGE | {TeamMember.Role.INSTRUCTOR}


class TeamError(Exception):
    def __init__(self, message, status=403):
        super().__init__(message)
        self.message = message
        self.status = status


def membership_for(user, slug):
    row = (
        TeamMember.objects.select_related("team", "team__plan", "team__subscription")
        .filter(user=user, team__slug=slug, active=True)
        .first()
    )
    if row is None:
        raise Http404()
    if row.team.status != Team.Status.ACTIVE:
        raise TeamError("This team subscription is not active.", status=403)
    return row


def visible_teams(user):
    return (
        Team.objects.filter(members__user=user, members__active=True, status=Team.Status.ACTIVE)
        .distinct()
        .order_by("name")
    )


def _require_plan(team):
    if team.plan_id is None:
        raise TeamError("No team plan is attached.", status=409)
    return team.plan


def allocate_member(actor, team, username, role):
    _require_plan(team)
    if role not in {TeamMember.Role.LEARNER, TeamMember.Role.INSTRUCTOR}:
        raise TeamError("Choose a learner or an instructor.", status=400)
    if role == TeamMember.Role.LEARNER and not team.plan.has_entitlement("seat_allocation"):
        raise TeamError("This team plan does not include seat allocation.", status=403)
    if role == TeamMember.Role.INSTRUCTOR and not team.plan.has_entitlement("team_roles"):
        raise TeamError("This team plan does not include instructor accounts.", status=403)
    person = User.objects.filter(username__iexact=username.strip()).first()
    if person is None:
        raise TeamError("No account uses that username.", status=404)
    if TeamMember.objects.filter(team=team, user=person, active=True).exists():
        raise TeamError("That account already has a seat on this team.", status=409)
    if role == TeamMember.Role.LEARNER:
        cap = team.learner_cap()
        used = TeamMember.objects.filter(team=team, role=TeamMember.Role.LEARNER, active=True).count()
        if cap is None:
            raise TeamError("A learner seat limit has not been set for this quotation.", status=409)
        if used >= cap:
            raise TeamError("Learner seats for this team are full.", status=409)
    else:
        cap = team.instructor_cap()
        used = TeamMember.objects.filter(team=team, role=TeamMember.Role.INSTRUCTOR, active=True).count()
        if cap is None or used >= cap:
            raise TeamError("Instructor accounts for this team are full.", status=409)
    row = TeamMember.objects.create(team=team, user=person, role=role, active=True)
    audit("team_seat_allocated", user=actor, category="team", plan_code=team.plan.code, detail={"team": team.pk, "member": person.pk, "role": role})
    return row


def release_member(actor, team, member_id):
    row = TeamMember.objects.filter(team=team, pk=member_id, active=True).first()
    if row is None:
        raise TeamError("That seat is not on this team.", status=404)
    if row.role == TeamMember.Role.OWNER:
        raise TeamError("The team owner seat cannot be released here.", status=403)
    row.active = False
    row.save(update_fields=["active"])
    audit("team_seat_released", user=actor, category="team", detail={"team": team.pk, "member": row.user_id})
    return row


def assign_path(actor, team, path):
    _require_plan(team)
    if not team.plan.has_entitlement("group_paths"):
        raise TeamError("This team plan does not include group learning paths.", status=403)
    row, created = GroupPath.objects.get_or_create(
        team=team,
        path=path,
        defaults={"assigned_by": actor},
    )
    if created:
        audit("team_path_assigned", user=actor, category="team", detail={"team": team.pk, "path": path.slug})
    return row


def add_assignment(actor, team, title, brief):
    _require_plan(team)
    if not team.plan.has_entitlement("team_assignments"):
        raise TeamError("This team plan does not include assignments.", status=403)
    title = (title or "").strip()
    if not title:
        raise TeamError("Enter an assignment title.", status=400)
    row = TeamAssignment.objects.create(team=team, title=title[:160], brief=(brief or "")[:4000], created_by=actor)
    audit("team_assignment_created", user=actor, category="team", detail={"team": team.pk, "assignment": row.pk})
    return row


def add_competition(actor, team, name):
    _require_plan(team)
    if not team.plan.has_entitlement("group_ctf"):
        raise TeamError("This team plan does not include group competitions.", status=403)
    name = (name or "").strip()
    if not name:
        raise TeamError("Enter a competition name.", status=400)
    row = TeamCompetition.objects.create(team=team, name=name[:160], created_by=actor)
    audit("team_competition_created", user=actor, category="team", detail={"team": team.pk, "competition": row.pk})
    return row
