from learning.models import Course, LearningPath, Lesson, Module, PathCourse
from labs.models import Lab
from learning.curriculum import sync_curriculum
from learning.foundation_sync import sync_foundations
from memberships.catalogue import sync_commercial_plans
from practice.models import ForensicTrack, SocModule, Tool


COURSES = [
    ("network-foundations", "Beginner Network Security", "Network Security", "network", "beginner", "fundamentals", "How packets, addressing, and defensive monitoring fit together."),
    ("linux-controls", "Linux Account and Privilege Controls", "Security Engineering", "engineering", "beginner", "fundamentals", "Accounts, permissions, and logging on a Linux host."),
    ("web-security", "Web Application Security", "Web Security", "web", "intermediate", "pentest", "How web flaws are classified and how findings are reported."),
    ("soc-fundamentals", "SOC Analyst Fundamentals", "SOC Operations", "soc", "beginner", "soc", "Alert triage, log sources, and investigation notes."),
    ("forensics-intro", "Digital Forensics Investigation", "Digital Forensics", "forensics", "intermediate", "forensics", "Evidence handling, hashes, and case notes."),
    ("ad-security", "Active Directory Security", "Security Engineering", "engineering", "advanced", "advance", "Identity, delegation, and detection in a Windows domain."),
]

PATHS = [
    ("ethical-hacker", "Beginner to Ethical Hacker", "Authorised testing, from foundations to a written report.", ["Networking", "Web reporting", "Lab discipline"], "6–9 months", ["network-foundations", "web-security"]),
    ("network-engineer", "Network Security Engineer", "Traffic, segmentation, and detection.", ["Packets", "Segmentation"], "5–7 months", ["network-foundations"]),
    ("penetration-tester", "Penetration Tester", "Scoped testing and evidence-backed reporting.", ["Web", "Reporting"], "6–9 months", ["web-security", "network-foundations"]),
    ("soc-analyst", "SOC Analyst", "Triage and escalation.", ["Logs", "Cases"], "5–7 months", ["soc-fundamentals"]),
    ("forensics-investigator", "Digital Forensics Investigator", "Evidence and timelines.", ["Hashes", "Notes"], "6–8 months", ["forensics-intro"]),
    ("malware-analyst", "Malware Analyst", "Isolated sample handling once a lab exists.", ["Isolation"], "8–12 months", ["forensics-intro"]),
    ("cloud-engineer", "Cloud Security Engineer", "Identity and logging in cloud accounts.", ["Identity"], "6–9 months", ["ad-security"]),
    ("appsec-engineer", "Application Security Engineer", "Reviewing software and reporting defects.", ["Web"], "6–9 months", ["web-security"]),
    ("red-team", "Red Team Specialist", "Authorised adversary exercises inside an isolated range.", ["Scope"], "8–12 months", ["web-security", "ad-security"]),
    ("blue-team", "Blue Team Specialist", "Detection and response.", ["SIEM"], "6–9 months", ["soc-fundamentals", "network-foundations"]),
]

LABS = [
    "Linux Security", "Windows Security", "Networking", "Ethical Hacking", "Web Application Security",
    "API Security", "Network Penetration Testing", "Active Directory Security", "Red Team", "Blue Team",
    "Purple Team", "SOC Operations", "Digital Forensics", "Malware Analysis", "Reverse Engineering",
    "Cloud Security", "Container Security", "Mobile Security", "Wireless Security", "Cryptography",
    "AI Security", "IoT Security",
]

TOOLS = [
    ("tracescan", "TraceScan", "Network Security", "network", "Network discovery and port analysis."),
    ("tracemap", "TraceMap", "Network Security", "network", "Network topology visualisation."),
    ("webprobe", "WebProbe", "Web & API Security", "web", "Web application security testing."),
    ("api-sentinel", "API Sentinel", "Web & API Security", "web", "API security testing."),
    ("vulnmatrix", "VulnMatrix", "Vulnerability Assessment", "vuln", "Vulnerability assessment."),
    ("advision", "ADVision", "Vulnerability Assessment", "vuln", "Active Directory security analysis."),
    ("packetscope", "PacketScope", "Network Security", "network", "Network packet analysis."),
    ("tracesiem", "TraceSIEM", "SOC & Threat Hunting", "soc", "Security event monitoring."),
    ("threathunter", "ThreatHunter", "SOC & Threat Hunting", "soc", "Threat hunting workspace."),
    ("ruleforge", "RuleForge", "SOC & Threat Hunting", "soc", "Detection rule development."),
    ("forensight", "ForenSight", "Digital Forensics", "forensics", "Digital forensics workspace."),
    ("memoryscope", "MemoryScope", "Digital Forensics", "forensics", "Memory forensics."),
    ("malwarelab", "MalwareLab", "Malware Analysis", "malware", "Isolated malware analysis."),
    ("cloudsentinel", "CloudSentinel", "Cloud Security", "cloud", "Cloud security assessment."),
    ("containerguard", "ContainerGuard", "Cloud Security", "cloud", "Container security."),
    ("mobiletrace", "MobileTrace", "Mobile Security", "mobile", "Mobile security analysis."),
    ("codeshield", "CodeShield", "Web & API Security", "web", "Secure code analysis."),
    ("cryptoscope", "CryptoScope", "Vulnerability Assessment", "vuln", "Cryptographic analysis."),
    ("osint-navigator", "OSINT Navigator", "Threat Intelligence", "intel", "Open-source intelligence notes."),
    ("rangecontrol", "RangeControl", "Cyber Range", "range", "Cyber range management."),
    ("incidentdesk", "IncidentDesk", "SOC & Threat Hunting", "soc", "Incident response management."),
    ("attacksim", "AttackSim", "Cyber Range", "range", "Controlled adversary simulation."),
    ("wirelessscope", "WirelessScope", "Wireless Security", "wireless", "Wireless security assessment."),
    ("threatintel-hub", "ThreatIntel Hub", "Threat Intelligence", "intel", "Threat intelligence management."),
]

SOC = [
    "SOC L1 operations", "SOC L2 investigations", "SOC L3 advanced analysis", "SIEM operations",
    "EDR and XDR fundamentals", "Network detection", "Log analysis", "Threat hunting",
    "Incident response", "Detection engineering",
]

FORENSICS = [
    "Computer Forensics", "Disk Forensics", "Memory Forensics", "Mobile Forensics", "Network Forensics",
    "Email Forensics", "Malware Forensics", "Windows Forensics", "Linux Forensics", "Cloud Forensics",
    "Browser Forensics", "Database Forensics", "IoT Forensics",
]

LESSON = (
    "This is a preview outline. It names what the lesson will cover when the course is published. "
    "It does not include procedures, exploits, or a graded assessment."
)


def ensure_catalogue():
    sync_commercial_plans()
    sync_curriculum()
    sync_foundations()
    if Course.objects.filter(slug="soc-fundamentals").exists():
        return
    course_rows = {}
    for slug, title, department, key, level, objective, summary in COURSES:
        course, _created = Course.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "department": department,
                "department_key": key,
                "level": level,
                "objective": objective,
                "summary": summary,
                "status": Course.Status.PREVIEW,
                "duration_minutes": 90,
                "instructor": "",
                "certificate_eligible": False,
            },
        )
        module, _created = Module.objects.get_or_create(course=course, position=1, defaults={"title": "Orientation"})
        for position, lesson_title in enumerate(("What this course will cover", "How progress will be recorded"), start=1):
            Lesson.objects.get_or_create(
                module=module,
                position=position,
                defaults={"title": lesson_title, "kind": Lesson.Kind.READING, "body": LESSON, "duration_minutes": 15},
            )
        course_rows[slug] = course
    for index, (slug, title, summary, skills, duration, course_slugs) in enumerate(PATHS, start=1):
        path, _created = LearningPath.objects.update_or_create(
            slug=slug,
            defaults={"title": title, "summary": summary, "skills": skills, "duration_label": duration, "sort_order": index},
        )
        for position, course_slug in enumerate(course_slugs, start=1):
            PathCourse.objects.get_or_create(path=path, course=course_rows[course_slug], defaults={"position": position})
    for name in LABS:
        slug = name.lower().replace(" ", "-").replace("&", "and")
        Lab.objects.get_or_create(
            slug=slug,
            defaults={
                "name": f"{name} orientation",
                "category": name,
                "summary": "Catalogue entry only. No machine is provisioned for this lab.",
                "required_plan": "core" if "Red" in name or "Malware" in name or "Penetration" in name else "free",
                "status": Lab.Status.COMING_SOON,
                "environment": "Not connected",
            },
        )
    for slug, name, category, key, summary in TOOLS:
        Tool.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "category": category,
                "category_key": key,
                "summary": summary,
                "capabilities": ["Catalogue entry"],
                "required_plan": "pro",
                "status": Tool.Status.COMING_SOON,
                "version": "",
                "documentation": "No engine is connected. Launch is refused by the server.",
            },
        )
    for title in SOC:
        SocModule.objects.get_or_create(
            slug=title.lower().replace(" ", "-").replace("/", "-"),
            defaults={"title": title, "summary": "Training module outline. No live alerts are attached.", "status": "preview"},
        )
    for title in FORENSICS:
        ForensicTrack.objects.get_or_create(
            slug=title.lower().replace(" ", "-"),
            defaults={"title": title, "summary": "Category outline. No evidence set is loaded."},
        )
