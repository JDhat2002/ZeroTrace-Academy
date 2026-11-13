from accounts.access import is_instructor, is_platform_admin
from campus.services import visible_institutions
from teams.models import TeamMember
from teams.services import visible_teams


NAV = [
    ("Overview", [
        ("Dashboard", "/dashboard/"),
        ("My Profile", "/account/profile/"),
        ("Notifications", "/app/notifications/"),
        ("Recent Activity", "/app/activity/"),
    ]),
    ("Learning", [
        ("My Learning", "/app/learning/"),
        ("Foundations", "/app/foundations/"),
        ("All Courses", "/app/courses/"),
        ("Departments", "/app/departments/"),
        ("Learning Paths", "/app/paths/"),
        ("Tutorials", "/tutorials.html"),
        ("Practical Labs", "/app/labs/"),
        ("Assignments", "/app/assignments/"),
        ("Assessments", "/app/assessments/"),
        ("Learning Calendar", "/app/calendar/"),
    ]),
    ("Practical environment", [
        ("Cyber Range", "/app/range/"),
        ("My Virtual Machines", "/app/machines/"),
        ("Lab History", "/app/lab-history/"),
        ("CTF Arena", "/app/ctf/"),
        ("Attack & Defence", "/app/arena/"),
    ]),
    ("ZeroTrace tools", [
        ("Tool Library", "/app/tools/"),
        ("Network Security", "/app/tools/?category=network"),
        ("Web & API Security", "/app/tools/?category=web"),
        ("Vulnerability Assessment", "/app/tools/?category=vuln"),
        ("SOC & Threat Hunting", "/app/tools/?category=soc"),
        ("Digital Forensics", "/app/tools/?category=forensics"),
        ("Malware Analysis", "/app/tools/?category=malware"),
        ("Cloud Security", "/app/tools/?category=cloud"),
        ("Mobile Security", "/app/tools/?category=mobile"),
        ("Wireless Security", "/app/tools/?category=wireless"),
    ]),
    ("Specialised centres", [
        ("SOC Centre", "/app/soc/"),
        ("Digital Forensics Centre", "/app/forensics/"),
        ("Malware Research Centre", "/app/malware/"),
        ("Threat Intelligence Centre", "/app/intel/"),
        ("Research Library", "/research.html"),
    ]),
    ("Career", [
        ("Career Dashboard", "/app/career/"),
        ("Projects & Portfolio", "/app/portfolio/"),
        ("Certifications", "/app/certifications/"),
        ("Career Roadmaps", "/app/paths/"),
        ("Job Preparation", "/app/jobs/"),
    ]),
    ("Account", [
        ("Membership Centre", "/app/membership/"),
        ("Billing & Payments", "/app/billing/"),
        ("Usage & Limits", "/app/usage/"),
        ("Account Security", "/account/security/"),
        ("Preferences", "/app/preferences/"),
        ("Support Centre", "/app/support/"),
    ]),
]


def navigation(request):
    path = request.path
    query = request.GET.get("category", "")
    sections = []
    for label, items in NAV:
        rendered = []
        for name, href in items:
            active = path == href.split("?")[0] and (f"category={query}" in href if "category=" in href else "category=" not in href or path != "/app/tools/")
            if href == "/app/tools/" and path == "/app/tools/" and not query:
                active = True
            if href.startswith("/app/tools/?") and path == "/app/tools/" and f"category={query}" in href and query:
                active = True
            rendered.append({"label": name, "href": href, "active": active})
        sections.append({"label": label, "items": rendered})
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        workspaces = []
        for team in visible_teams(user):
            role = TeamMember.objects.filter(team=team, user=user, active=True).values_list("role", flat=True).first()
            if role in {TeamMember.Role.OWNER, TeamMember.Role.ADMINISTRATOR, TeamMember.Role.INSTRUCTOR}:
                workspaces.append(("Team centre", f"/app/teams/{team.slug}/"))
            else:
                workspaces.append(("Team learning", f"/app/teams/{team.slug}/learn/"))
        for institution in visible_institutions(user):
            from campus.models import CampusAccount

            role = CampusAccount.objects.filter(institution=institution, user=user, active=True).values_list("role", flat=True).first()
            if role in {CampusAccount.Role.OWNER, CampusAccount.Role.ADMINISTRATOR, CampusAccount.Role.INSTRUCTOR}:
                workspaces.append(("Campus centre", f"/app/campus/{institution.slug}/"))
            else:
                workspaces.append(("Campus study", f"/app/campus/{institution.slug}/study/"))
        if workspaces:
            rendered = []
            for name, href in workspaces:
                rendered.append({"label": name, "href": href, "active": request.path == href.rstrip("/") or request.path == href})
            sections.append({"label": "Workspaces", "items": rendered})
        if is_instructor(user) or is_platform_admin(user):
            sections.append({
                "label": "Teaching",
                "items": [
                    {"label": "Instructor workspace", "href": "/app/instructor/", "active": path == "/app/instructor/"},
                    {"label": "Course studio", "href": "/app/studio/", "active": path.startswith("/app/studio/")},
                ],
            })
        if is_platform_admin(user):
            sections.append({
                "label": "Administration",
                "items": [
                    {"label": "Pricing", "href": "/app/admin/pricing/", "active": request.path == "/app/admin/pricing/"},
                    {"label": "Revenue", "href": "/app/admin/revenue/", "active": request.path == "/app/admin/revenue/"},
                ],
            })
    if path == "/dashboard/":
        sections[0]["items"][0]["active"] = True
    return sections
