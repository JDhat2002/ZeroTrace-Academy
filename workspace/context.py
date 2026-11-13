from campus.models import CampusAccount
from campus.services import visible_institutions
from memberships.services import current_plan
from notifications.services import unread_count
from teams.models import TeamMember
from teams.services import visible_teams
from workspace.catalogue import ensure_catalogue
from workspace.navigation import navigation


def _team_href(user, team):
    role = TeamMember.objects.filter(team=team, user=user, active=True).values_list("role", flat=True).first()
    if role in {TeamMember.Role.OWNER, TeamMember.Role.ADMINISTRATOR, TeamMember.Role.INSTRUCTOR}:
        return f"/app/teams/{team.slug}/"
    return f"/app/teams/{team.slug}/learn/"


def _campus_href(user, institution):
    role = CampusAccount.objects.filter(institution=institution, user=user, active=True).values_list("role", flat=True).first()
    if role in {CampusAccount.Role.OWNER, CampusAccount.Role.ADMINISTRATOR, CampusAccount.Role.INSTRUCTOR}:
        return f"/app/campus/{institution.slug}/"
    return f"/app/campus/{institution.slug}/study/"


def workspace(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"nav_sections": [], "plan_name": "", "unread_notifications": 0, "workspaces": []}
    ensure_catalogue()
    plan = current_plan(user)
    links = []
    for team in visible_teams(user):
        links.append({"label": team.name, "href": _team_href(user, team), "kind": "team"})
    for institution in visible_institutions(user):
        links.append({"label": institution.name, "href": _campus_href(user, institution), "kind": "campus"})
    return {
        "nav_sections": navigation(request),
        "plan_name": plan.name if plan else "Explorer",
        "unread_notifications": unread_count(user),
        "workspaces": links,
    }
