"""Static content for the public site.

Everything here is plain Python data so templates stay presentation-only.
Each collection is shaped like the model it will become (Department, Tool,
LearningPath, Plan, ...) so moving to the database is a drop-in change in
`core/services.py`.

Honesty rules (see project spec section 25): tools are *proposed*, previews
are *illustrative*, sample data is labelled, and no adoption numbers exist.
"""

NAV = [
    {
        "label": "Academy",
        "url": "/academy/",
        "children": [
            {"label": "All Courses", "url": "/academy/courses/", "icon": "library", "desc": "Browse the full course catalogue"},
            {"label": "Learning Paths", "url": "/roadmaps/", "icon": "route", "desc": "Structured, role-based journeys"},
            {"label": "Ethical Hacking", "url": "/departments/ethical-hacking/", "icon": "bug", "desc": "Offensive security fundamentals"},
            {"label": "SOC Analyst", "url": "/soc/", "icon": "monitor-dot", "desc": "Alert triage to incident response"},
            {"label": "Digital Forensics", "url": "/forensics/", "icon": "fingerprint", "desc": "Evidence handling and analysis"},
            {"label": "Cloud Security", "url": "/departments/cloud-security/", "icon": "cloud-cog", "desc": "Secure cloud architectures"},
        ],
    },
    {"label": "Roadmaps", "url": "/roadmaps/"},
    {
        "label": "Cyber Range",
        "url": "/cyber-range/",
        "children": [
            {"label": "Virtual Labs", "url": "/cyber-range/virtual-labs/", "icon": "server", "desc": "Isolated Linux and Windows machines"},
            {"label": "CTF Arena", "url": "/ctf/", "icon": "flag", "desc": "Capture-the-flag challenges"},
            {"label": "Attack & Defence", "url": "/cyber-range/attack-defence/", "icon": "swords", "desc": "Red vs blue team exercises"},
            {"label": "SOC Simulation", "url": "/cyber-range/soc-simulation/", "icon": "activity", "desc": "Training telemetry and alerts"},
            {"label": "Forensic Investigations", "url": "/cyber-range/forensic-investigations/", "icon": "file-search", "desc": "Prepared cases and evidence"},
        ],
    },
    {
        "label": "Tools",
        "url": "/tools/",
        "children": [
            {"label": "All Tools", "url": "/tools/", "icon": "layout-grid", "desc": "The proposed ZeroTrace toolkit"},
            {"label": "Network Security", "url": "/tools/?category=network#tools", "icon": "network", "desc": "Discovery, mapping, packets"},
            {"label": "Web Security", "url": "/tools/?category=web#tools", "icon": "globe-lock", "desc": "Web application and API testing"},
            {"label": "SOC Tools", "url": "/tools/?category=blue#tools", "icon": "shield-check", "desc": "Monitoring, hunting, detection"},
            {"label": "Forensics Tools", "url": "/tools/?category=forensics#tools", "icon": "microscope", "desc": "Disk, memory and malware"},
            {"label": "Cloud Security", "url": "/tools/?category=cloud#tools", "icon": "cloud", "desc": "Cloud and container posture"},
        ],
    },
    {"label": "Research", "url": "/research/"},
    {"label": "Pricing", "url": "/pricing/"},
]

HIGHLIGHTS = [
    {"title": "Comprehensive Learning", "desc": "Structured courses and learning paths from fundamentals to specialist depth.", "icon": "graduation-cap", "url": "/academy/"},
    {"title": "Hands-on Cyber Range", "desc": "Isolated practical environments built for authorised, safe experimentation.", "icon": "terminal", "url": "/cyber-range/"},
    {"title": "Professional Tools", "desc": "A family of original ZeroTrace tools and integrations, in development.", "icon": "crosshair", "url": "/tools/"},
    {"title": "SOC & Forensics", "desc": "Investigate threats, triage alerts and analyse evidence like a professional.", "icon": "scan-search", "url": "/soc/"},
    {"title": "Career Development", "desc": "Portfolio projects, practical assessments and interview preparation.", "icon": "award", "url": "/career/"},
]

LEVEL_BEGINNER = "Beginner"
LEVEL_INTERMEDIATE = "Intermediate"
LEVEL_ADVANCED = "Advanced"

DEPARTMENTS = [
    {"slug": "cs-it-fundamentals", "title": "CS & IT Fundamentals", "icon": "cpu", "level": LEVEL_BEGINNER, "group": "Foundations",
     "desc": "How computers, operating systems and data actually work, the base every security skill builds on."},
    {"slug": "networking", "title": "Networking", "icon": "network", "level": LEVEL_BEGINNER, "group": "Foundations",
     "desc": "TCP/IP, routing, DNS and protocols, read traffic the way attackers and defenders do."},
    {"slug": "linux-security", "title": "Linux Security", "icon": "square-terminal", "level": LEVEL_BEGINNER, "group": "Foundations",
     "desc": "Command line fluency, permissions, services and hardening on Linux systems."},
    {"slug": "windows-security", "title": "Windows Security", "icon": "app-window", "level": LEVEL_BEGINNER, "group": "Foundations",
     "desc": "Windows internals, event logs, PowerShell and endpoint hardening."},
    {"slug": "programming-scripting", "title": "Programming & Scripting", "icon": "code-xml", "level": LEVEL_BEGINNER, "group": "Foundations",
     "desc": "Python, Bash and PowerShell for automating recon, analysis and defence."},
    {"slug": "cryptography", "title": "Cryptography", "icon": "key-round", "level": LEVEL_INTERMEDIATE, "group": "Foundations",
     "desc": "Hashing, symmetric and public-key crypto, and the mistakes that break them."},
    {"slug": "ethical-hacking", "title": "Ethical Hacking", "icon": "bug", "level": LEVEL_BEGINNER, "group": "Offensive",
     "desc": "The attacker mindset and methodology, applied only to systems you are authorised to test."},
    {"slug": "web-application-security", "title": "Web Application Security", "icon": "globe", "level": LEVEL_INTERMEDIATE, "group": "Offensive",
     "desc": "OWASP Top 10, authentication flaws, injection and secure web design."},
    {"slug": "api-security", "title": "API Security", "icon": "webhook", "level": LEVEL_INTERMEDIATE, "group": "Offensive",
     "desc": "REST and GraphQL attack surfaces, broken object authorisation and API hardening."},
    {"slug": "network-penetration-testing", "title": "Network Penetration Testing", "icon": "radar", "level": LEVEL_INTERMEDIATE, "group": "Offensive",
     "desc": "Scoping, enumeration, exploitation and reporting against internal networks."},
    {"slug": "wireless-security", "title": "Wireless Security", "icon": "wifi", "level": LEVEL_INTERMEDIATE, "group": "Offensive",
     "desc": "Wi-Fi protocols, WPA2/WPA3 weaknesses and secure wireless deployment."},
    {"slug": "active-directory-security", "title": "Active Directory Security", "icon": "folder-tree", "level": LEVEL_ADVANCED, "group": "Offensive",
     "desc": "Kerberos, delegation, attack paths and defending enterprise identity."},
    {"slug": "red-team-operations", "title": "Red Team Operations", "icon": "swords", "level": LEVEL_ADVANCED, "group": "Offensive",
     "desc": "Adversary emulation, operational planning and objective-based engagements."},
    {"slug": "blue-team-operations", "title": "Blue Team Operations", "icon": "shield-check", "level": LEVEL_INTERMEDIATE, "group": "Defensive",
     "desc": "Monitoring, hardening and response, keeping real environments resilient."},
    {"slug": "purple-team-operations", "title": "Purple Team Operations", "icon": "shield-half", "level": LEVEL_ADVANCED, "group": "Defensive",
     "desc": "Red and blue collaboration to validate and improve detections."},
    {"slug": "soc-operations", "title": "SOC Operations", "icon": "monitor-dot", "level": LEVEL_BEGINNER, "group": "Defensive",
     "desc": "SIEM workflows, alert triage, escalation and shift-ready analyst skills."},
    {"slug": "digital-forensics", "title": "Digital Forensics", "icon": "fingerprint", "level": LEVEL_INTERMEDIATE, "group": "Defensive",
     "desc": "Acquire, preserve and analyse evidence with a defensible chain of custody."},
    {"slug": "malware-analysis", "title": "Malware Analysis", "icon": "biohazard", "level": LEVEL_ADVANCED, "group": "Defensive",
     "desc": "Static and dynamic analysis of malicious code in isolated sandboxes."},
    {"slug": "threat-intelligence", "title": "Threat Intelligence", "icon": "scan-eye", "level": LEVEL_INTERMEDIATE, "group": "Defensive",
     "desc": "Collect, enrich and apply intelligence on adversaries and their TTPs."},
    {"slug": "incident-response", "title": "Incident Response", "icon": "siren", "level": LEVEL_INTERMEDIATE, "group": "Defensive",
     "desc": "Contain, eradicate and recover, then learn from every incident."},
    {"slug": "cloud-security", "title": "Cloud Security", "icon": "cloud-cog", "level": LEVEL_INTERMEDIATE, "group": "Cloud & Engineering",
     "desc": "IAM, network controls, logging and misconfiguration risks across major clouds."},
    {"slug": "devsecops", "title": "DevSecOps", "icon": "git-branch", "level": LEVEL_INTERMEDIATE, "group": "Cloud & Engineering",
     "desc": "Security built into CI/CD, from code scanning to secrets management."},
    {"slug": "container-kubernetes-security", "title": "Container & Kubernetes Security", "icon": "container", "level": LEVEL_ADVANCED, "group": "Cloud & Engineering",
     "desc": "Image hardening, runtime security and Kubernetes cluster defence."},
    {"slug": "mobile-security", "title": "Mobile Security", "icon": "smartphone", "level": LEVEL_INTERMEDIATE, "group": "Specialist",
     "desc": "Android and iOS application security testing and secure mobile design."},
    {"slug": "iot-hardware-security", "title": "IoT & Hardware Security", "icon": "circuit-board", "level": LEVEL_ADVANCED, "group": "Specialist",
     "desc": "Firmware, embedded interfaces and the security of connected devices."},
    {"slug": "ot-ics-security", "title": "OT / ICS Security", "icon": "factory", "level": LEVEL_ADVANCED, "group": "Specialist",
     "desc": "Industrial protocols, safety constraints and defending critical infrastructure."},
    {"slug": "database-security", "title": "Database Security", "icon": "database", "level": LEVEL_INTERMEDIATE, "group": "Specialist",
     "desc": "Access control, injection defence, encryption and database auditing."},
    {"slug": "ai-security", "title": "AI Security", "icon": "brain-circuit", "level": LEVEL_ADVANCED, "group": "Specialist",
     "desc": "Prompt injection, model abuse and securing machine-learning systems."},
    {"slug": "blockchain-security", "title": "Blockchain Security", "icon": "blocks", "level": LEVEL_ADVANCED, "group": "Specialist",
     "desc": "Smart-contract vulnerabilities, auditing practice and wallet security."},
    {"slug": "grc", "title": "Governance, Risk & Compliance", "icon": "scale", "level": LEVEL_INTERMEDIATE, "group": "Governance",
     "desc": "Risk assessment, policy, frameworks such as ISO 27001 and NIST CSF, and audit."},
    {"slug": "security-architecture", "title": "Security Architecture", "icon": "layers", "level": LEVEL_ADVANCED, "group": "Governance",
     "desc": "Designing zero-trust, defence-in-depth systems that hold up under pressure."},
]

TOOL_FILTERS = [
    {"key": "all", "label": "All"},
    {"key": "network", "label": "Network"},
    {"key": "web", "label": "Web & API"},
    {"key": "red", "label": "Red Team"},
    {"key": "blue", "label": "Blue Team"},
    {"key": "forensics", "label": "Forensics"},
    {"key": "cloud", "label": "Cloud"},
    {"key": "research", "label": "Research"},
]

TOOL_STATUS = "Proposed"

TOOLS = [
    {"slug": "tracescan", "name": "TraceScan", "category": "Network Discovery", "icon": "radar", "filters": ["network", "red"],
     "desc": "Host and service discovery for networks you are authorised to assess."},
    {"slug": "tracemap", "name": "TraceMap", "category": "Network Visualisation", "icon": "waypoints", "filters": ["network", "blue"],
     "desc": "Turn discovery results into an interactive, explorable network topology."},
    {"slug": "webprobe", "name": "WebProbe", "category": "Web App Testing", "icon": "globe-lock", "filters": ["web", "red"],
     "desc": "Guided web application testing workflow mapped to the OWASP Top 10."},
    {"slug": "api-sentinel", "name": "API Sentinel", "category": "API Security", "icon": "webhook", "filters": ["web"],
     "desc": "Inspect API specifications and traffic for authorisation and data-exposure flaws."},
    {"slug": "vulnmatrix", "name": "VulnMatrix", "category": "Vulnerability Management", "icon": "grid-3x3", "filters": ["blue", "research"],
     "desc": "Track, prioritise and report findings with severity and remediation context."},
    {"slug": "advision", "name": "ADVision", "category": "Active Directory Analysis", "icon": "folder-tree", "filters": ["red", "blue"],
     "desc": "Visualise Active Directory relationships and risky privilege paths."},
    {"slug": "packetscope", "name": "PacketScope", "category": "Packet Analysis", "icon": "audio-waveform", "filters": ["network", "forensics"],
     "desc": "Browser-friendly packet capture inspection for training captures."},
    {"slug": "tracesiem", "name": "TraceSIEM", "category": "Security Monitoring", "icon": "monitor-dot", "filters": ["blue"],
     "desc": "A training SIEM for searching logs, building dashboards and triaging alerts."},
    {"slug": "threathunter", "name": "ThreatHunter", "category": "Threat Hunting", "icon": "crosshair", "filters": ["blue"],
     "desc": "Hypothesis-driven hunting notebooks over prepared telemetry."},
    {"slug": "ruleforge", "name": "RuleForge", "category": "Detection Engineering", "icon": "anvil", "filters": ["blue", "research"],
     "desc": "Write, test and tune detection rules against sample event data."},
    {"slug": "forensight", "name": "ForenSight", "category": "Digital Forensics", "icon": "fingerprint", "filters": ["forensics"],
     "desc": "Case-based disk image examination with timeline and artefact views."},
    {"slug": "memoryscope", "name": "MemoryScope", "category": "Memory Forensics", "icon": "memory-stick", "filters": ["forensics"],
     "desc": "Explore memory images for processes, network connections and injected code."},
    {"slug": "malwarelab", "name": "MalwareLab", "category": "Malware Analysis", "icon": "flask-conical", "filters": ["forensics", "research"],
     "desc": "Isolated workflow for static and behavioural analysis of samples."},
    {"slug": "cloudsentinel", "name": "CloudSentinel", "category": "Cloud Security", "icon": "cloud", "filters": ["cloud", "blue"],
     "desc": "Review cloud configurations for identity, storage and logging risks."},
    {"slug": "containerguard", "name": "ContainerGuard", "category": "Container Security", "icon": "container", "filters": ["cloud"],
     "desc": "Scan images and manifests for vulnerable packages and unsafe settings."},
    {"slug": "mobiletrace", "name": "MobileTrace", "category": "Mobile Security", "icon": "smartphone", "filters": ["red", "forensics"],
     "desc": "Inspect mobile app packages for permissions, secrets and insecure storage."},
    {"slug": "codeshield", "name": "CodeShield", "category": "Code Security", "icon": "file-code", "filters": ["web", "research"],
     "desc": "Static analysis that explains insecure code patterns as you learn."},
    {"slug": "cryptoscope", "name": "CryptoScope", "category": "Cryptographic Analysis", "icon": "key-round", "filters": ["research"],
     "desc": "Identify encodings, hashes and weak cryptographic constructions."},
    {"slug": "osint-navigator", "name": "OSINT Navigator", "category": "OSINT", "icon": "compass", "filters": ["red", "research"],
     "desc": "Structured, ethical open-source intelligence investigation workspace."},
    {"slug": "rangecontrol", "name": "RangeControl", "category": "Lab Orchestration", "icon": "server-cog", "filters": ["research"],
     "desc": "Provision and reset isolated cyber-range environments per learner."},
    {"slug": "incidentdesk", "name": "IncidentDesk", "category": "Incident Response", "icon": "siren", "filters": ["blue", "forensics"],
     "desc": "Case management for incident timelines, tasks and evidence."},
    {"slug": "attacksim", "name": "AttackSim", "category": "Controlled Attack Simulation", "icon": "target", "filters": ["red", "blue"],
     "desc": "Replay scripted adversary techniques inside isolated lab networks only."},
    {"slug": "wirelessscope", "name": "WirelessScope", "category": "Wireless Security", "icon": "wifi", "filters": ["network", "red"],
     "desc": "Analyse wireless captures and configurations in training scenarios."},
    {"slug": "threatintel-hub", "name": "ThreatIntel Hub", "category": "Threat Intelligence", "icon": "satellite-dish", "filters": ["blue", "research"],
     "desc": "Aggregate and enrich indicators, mapped to MITRE ATT&CK techniques."},
]

RANGE_FEATURES = [
    {"title": "Virtual Machines", "icon": "server", "desc": "Isolated Linux and Windows machines provisioned for your session only."},
    {"title": "Penetration Testing Labs", "icon": "bug", "desc": "Intentionally vulnerable systems, built to be attacked legally and safely."},
    {"title": "SOC Simulation", "icon": "activity", "desc": "Training telemetry and generated alerts to triage like a real shift."},
    {"title": "Forensic Investigations", "icon": "hard-drive", "desc": "Prepared disk images, memory dumps and packet captures to examine."},
    {"title": "CTF Arena", "icon": "flag", "desc": "Category-based challenges from beginner to advanced difficulty."},
    {"title": "Red vs Blue", "icon": "swords", "desc": "Team exercises where attackers and defenders learn from each other."},
]

FORENSIC_CATEGORIES = [
    {"title": "Computer & Disk", "icon": "hard-drive", "desc": "File systems, deleted data, artefacts and timelines."},
    {"title": "Memory", "icon": "memory-stick", "desc": "Processes, injected code and volatile evidence."},
    {"title": "Mobile", "icon": "smartphone", "desc": "Device extractions, app data and communications."},
    {"title": "Network", "icon": "audio-waveform", "desc": "Packet captures, flows and lateral movement."},
    {"title": "Email & Phishing", "icon": "mail-warning", "desc": "Headers, attachments and campaign analysis."},
    {"title": "Malware & Cloud", "icon": "cloud-alert", "desc": "Malicious artefacts and cloud audit trails."},
]

SOC_TRACKS = [
    {"title": "SOC L1 / L2 / L3 Training", "icon": "layers", "desc": "Progress from triage to escalation to advanced investigation."},
    {"title": "SIEM Investigation", "icon": "monitor-dot", "desc": "Query logs, pivot on fields and build investigations."},
    {"title": "Threat Hunting", "icon": "crosshair", "desc": "Form hypotheses and hunt for what the alerts missed."},
    {"title": "Incident Response", "icon": "siren", "desc": "Run the response lifecycle from detection to lessons learned."},
    {"title": "EDR & XDR", "icon": "shield-check", "desc": "Endpoint telemetry, process trees and response actions."},
    {"title": "Detection Engineering", "icon": "anvil", "desc": "Write, test and tune rules mapped to MITRE ATT&CK."},
]

ROADMAPS = [
    {
        "slug": "ethical-hacker", "title": "Ethical Hacker", "icon": "bug", "difficulty": "Beginner → Advanced", "duration": "6–9 months",
        "summary": "Learn to think like an attacker and test systems legally, methodically and professionally.",
        "modules": ["Foundations", "Networking", "Linux", "Reconnaissance", "Web Security", "Penetration Testing", "Reporting"],
        "skills": ["Recon methodology", "Web exploitation", "Privilege escalation", "Professional reporting"],
    },
    {
        "slug": "soc-analyst", "title": "SOC Analyst", "icon": "monitor-dot", "difficulty": "Beginner → Intermediate", "duration": "5–7 months",
        "summary": "Build the defensive skills a security operations centre expects from day one.",
        "modules": ["IT Fundamentals", "Networking", "Windows & Linux Logs", "SIEM", "Alert Triage", "Threat Hunting", "Incident Response"],
        "skills": ["Log analysis", "SIEM querying", "Alert triage", "Escalation & reporting"],
    },
    {
        "slug": "forensics-investigator", "title": "Digital Forensics Investigator", "icon": "fingerprint", "difficulty": "Intermediate", "duration": "6–8 months",
        "summary": "Preserve and analyse digital evidence so your findings hold up to scrutiny.",
        "modules": ["Foundations", "Evidence Preservation", "Disk Forensics", "Memory Forensics", "Network Forensics", "Case Reporting"],
        "skills": ["Chain of custody", "Timeline analysis", "Memory analysis", "Case documentation"],
    },
    {
        "slug": "cloud-security-engineer", "title": "Cloud Security Engineer", "icon": "cloud-cog", "difficulty": "Intermediate → Advanced", "duration": "6–9 months",
        "summary": "Design, secure and monitor cloud workloads across identity, network and data.",
        "modules": ["Cloud Fundamentals", "IAM", "Network Security", "Storage Security", "Logging & Monitoring", "Container Security", "Cloud Incident Response"],
        "skills": ["Least-privilege IAM", "Cloud logging", "Posture review", "Cloud IR"],
    },
    {
        "slug": "malware-analyst", "title": "Malware Analyst", "icon": "biohazard", "difficulty": "Advanced", "duration": "8–12 months",
        "summary": "Take malicious code apart safely and turn findings into detections.",
        "modules": ["Programming", "Operating Systems", "Binary Fundamentals", "Static Analysis", "Dynamic Analysis", "Reverse Engineering"],
        "skills": ["Assembly reading", "Sandbox analysis", "IOC extraction", "YARA rules"],
    },
    {
        "slug": "security-engineer", "title": "Security Engineer", "icon": "layers", "difficulty": "Intermediate → Advanced", "duration": "8–12 months",
        "summary": "Build secure systems and pipelines instead of only finding what's broken.",
        "modules": ["Programming", "Networking", "Linux", "Secure Development", "DevSecOps", "Cloud Security", "Security Architecture"],
        "skills": ["Secure code review", "CI/CD security", "Threat modelling", "Architecture design"],
    },
]

AI_MENTOR_PROMPTS = [
    {
        "slug": "ask", "label": "Ask a question", "icon": "message-circle-question",
        "question": "What's the difference between a vulnerability, a threat and a risk?",
        "answer": [
            "A <strong>vulnerability</strong> is a weakness, such as an unpatched service.",
            "A <strong>threat</strong> is something that could exploit it, such as an attacker or a piece of malware.",
            "<strong>Risk</strong> combines the two: how likely exploitation is and how much damage it would do.",
        ],
        "followup": "Want a short quiz on this to check your understanding?",
    },
    {
        "slug": "explain", "label": "Explain a vulnerability", "icon": "bug",
        "question": "Explain SQL injection like I'm new to web security.",
        "answer": [
            "SQL injection happens when user input is pasted straight into a database query.",
            "If the input contains SQL syntax, the database runs it as part of the query.",
            "The fix is <strong>parameterised queries</strong>, which keep data and code separate.",
        ],
        "followup": "I can point you to the matching lab in Web Application Security.",
    },
    {
        "slug": "lab", "label": "Help with a lab result", "icon": "terminal",
        "question": "My scan shows port 445 open on the lab host. What should I check next?",
        "answer": [
            "Port 445 is SMB. Inside your <strong>authorised lab</strong>, enumerate the SMB version and signing settings first.",
            "Then list shares that allow anonymous access and note any readable files.",
            "Record each finding with evidence so it is ready for your lab report.",
        ],
        "followup": "Shall I explain why SMB signing matters?",
    },
    {
        "slug": "rule", "label": "Review a detection rule", "icon": "anvil",
        "question": "Can you review my rule that alerts on every PowerShell execution?",
        "answer": [
            "Alerting on every PowerShell run will flood analysts with false positives.",
            "Narrow it to suspicious traits such as <code>-EncodedCommand</code>, download cradles or unusual parent processes.",
            "Then test it against benign admin activity to measure the noise before you deploy it.",
        ],
        "followup": "I can map this rule to the matching MITRE ATT&CK technique.",
    },
    {
        "slug": "report", "label": "Improve a report", "icon": "file-pen-line",
        "question": "How can I make my investigation summary clearer?",
        "answer": [
            "Lead with the conclusion: what happened, the impact and your confidence level.",
            "Follow it with a timestamped timeline and the evidence behind each step.",
            "Finish with recommendations, ordered by priority.",
        ],
        "followup": "Paste a paragraph and I'll suggest a tighter version.",
    },
    {
        "slug": "path", "label": "Recommend a path", "icon": "route",
        "question": "I know basic networking. Which path should I take for a SOC role?",
        "answer": [
            "With networking covered, start the <strong>SOC Analyst</strong> path from Windows & Linux Logs.",
            "Practise SIEM queries in the SOC Simulation once you reach the SIEM module.",
            "Add the Incident Response department after Alert Triage to round out your skills.",
        ],
        "followup": "I can build you a weekly study plan around your schedule.",
    },
]

CTF_CATEGORIES = ["Web Exploitation", "Cryptography", "Reverse Engineering", "Forensics", "Network", "Linux", "Binary Exploitation"]

CTF_SAMPLE_CHALLENGES = [
    {"name": "Cookie Monster", "category": "Web Exploitation", "difficulty": LEVEL_BEGINNER, "points": 100, "status": "solved"},
    {"name": "Broken Cipher", "category": "Cryptography", "difficulty": LEVEL_INTERMEDIATE, "points": 250, "status": "in-progress"},
    {"name": "Hidden in Plain Sight", "category": "Forensics", "difficulty": LEVEL_BEGINNER, "points": 150, "status": "solved"},
    {"name": "Packet Whisperer", "category": "Network", "difficulty": LEVEL_INTERMEDIATE, "points": 300, "status": "open"},
    {"name": "Root of All Evil", "category": "Linux", "difficulty": LEVEL_INTERMEDIATE, "points": 300, "status": "open"},
    {"name": "Unpack Me", "category": "Reverse Engineering", "difficulty": LEVEL_ADVANCED, "points": 450, "status": "locked"},
    {"name": "Stack Smasher", "category": "Binary Exploitation", "difficulty": LEVEL_ADVANCED, "points": 500, "status": "locked"},
]

CTF_SAMPLE_LEADERBOARD = [
    {"rank": 1, "handle": "sample_player_01", "points": 4250, "solves": 18},
    {"rank": 2, "handle": "sample_player_02", "points": 3900, "solves": 16},
    {"rank": 3, "handle": "sample_player_03", "points": 3475, "solves": 15},
    {"rank": 4, "handle": "sample_player_04", "points": 2980, "solves": 13},
    {"rank": 5, "handle": "you (example)", "points": 1150, "solves": 6},
]

CAREER_FEATURES = [
    {"title": "Career Roadmaps", "icon": "route"},
    {"title": "Resume Preparation", "icon": "file-user"},
    {"title": "Interview Preparation", "icon": "messages-square"},
    {"title": "Practical Assessments", "icon": "clipboard-check"},
    {"title": "Portfolio Projects", "icon": "folder-git-2"},
    {"title": "Technical Interview Questions", "icon": "message-circle-question"},
    {"title": "Professional Development", "icon": "trending-up"},
    {"title": "Skill Tracking", "icon": "chart-no-axes-combined"},
]

CAREER_TRACKS = [
    {"title": "SOC Analyst", "icon": "monitor-dot"},
    {"title": "Penetration Tester", "icon": "bug"},
    {"title": "Digital Forensic Investigator", "icon": "fingerprint"},
    {"title": "Cloud Security Engineer", "icon": "cloud-cog"},
    {"title": "Security Researcher", "icon": "microscope"},
    {"title": "Security Engineer", "icon": "layers"},
]

COMMUNITY_FEATURES = [
    {"title": "Discussions", "icon": "messages-square", "desc": "Ask questions, compare approaches and help others through labs.", "kind": "Community"},
    {"title": "Technical Articles", "icon": "newspaper", "desc": "In-depth explainers on techniques, tooling and defence.", "kind": "Editorial"},
    {"title": "Research Publications", "icon": "book-open-text", "desc": "Original security research, reviewed before publication.", "kind": "Research"},
    {"title": "Write-ups", "icon": "file-text", "desc": "Step-by-step solutions for retired challenges and labs.", "kind": "Editorial"},
    {"title": "Learning Communities", "icon": "users", "desc": "Study groups organised around paths and departments.", "kind": "Community"},
    {"title": "Project Showcases", "icon": "folder-git-2", "desc": "Share tools, detections and portfolio projects for feedback.", "kind": "Community"},
    {"title": "CTF Competitions", "icon": "trophy", "desc": "Scheduled competitions inside isolated, authorised environments.", "kind": "Events"},
    {"title": "Responsible Disclosure", "icon": "shield-alert", "desc": "How to report vulnerabilities ethically, legally and effectively.", "kind": "Education"},
]

PLANS = [
    {
        "slug": "free", "name": "Free", "price": 0, "period": "month", "tagline": "Start exploring cybersecurity fundamentals.",
        "features": ["Selected courses", "Beginner learning paths", "Selected tutorials", "Limited practice resources"],
        "cta": "Get started free", "highlight": False,
    },
    {
        "slug": "pro", "name": "Pro", "price": 199, "period": "month", "tagline": "Build practical skills with guided exercises.",
        "features": ["Expanded course library", "Guided practical exercises", "Selected security tools", "Progress tracking", "Additional resources"],
        "cta": "Choose Pro", "highlight": True,
    },
    {
        "slug": "elite", "name": "Elite", "price": 499, "period": "month", "tagline": "Go deep with advanced paths and labs.",
        "features": ["Advanced learning paths", "Eligible advanced labs", "Extended practical resources", "Advanced assessments", "Priority support"],
        "cta": "Choose Elite", "highlight": False,
    },
]

# Each row: feature, free, pro, elite. True/False render as icons, strings render as text.
PLAN_COMPARISON = [
    ("Courses", "Selected", "Expanded", "Expanded + advanced"),
    ("Learning paths", "Beginner", "Beginner + intermediate", "All, incl. advanced"),
    ("Tutorials", True, True, True),
    ("Practice resources", "Limited", "Guided exercises", "Extended"),
    ("Security tools access", False, "Selected", "Selected"),
    ("Practical labs", False, "Guided", "Eligible advanced labs"),
    ("Progress tracking", False, True, True),
    ("Assessments", False, "Standard", "Advanced"),
    ("Support", "Community", "Standard", "Priority"),
]

FAQS = [
    {"q": "Is ZeroTrace Academy available today?",
     "a": "ZeroTrace Academy is being built in stages. Parts of the platform shown on this page, including the cyber range, the tools and the AI mentor, are previews of what's planned. Each one is labelled as a preview or as in development until it launches."},
    {"q": "Are the ZeroTrace tools ready to use?",
     "a": "Not yet. The 24 tools listed here are proposed and in planning or development. We won't describe any of them as available until it is actually released."},
    {"q": "Is the offensive security training legal?",
     "a": "Yes. All offensive techniques are taught for use only on systems you own or are explicitly authorised to test. Practical work runs in isolated lab environments, never against real third-party systems."},
    {"q": "Do I need prior experience?",
     "a": "No. The Foundations departments and beginner learning paths assume no prior security knowledge. Each path lists its difficulty and suggested prerequisites."},
    {"q": "Do you offer certificates?",
     "a": "We plan to issue completion records for paths and assessments. These are not accredited professional certifications, and we'll always describe them accurately."},
    {"q": "What will the pricing be?",
     "a": "The plans shown are proposed and may change before launch. Lab access depends on plan eligibility and fair-use limits; we do not offer unlimited virtual machines."},
]

PAGES = {
    "academy": {"path": "academy/", "title": "Academy", "icon": "graduation-cap", "desc": "Structured courses across every major cybersecurity discipline."},
    "courses": {"path": "academy/courses/", "title": "All Courses", "icon": "library", "desc": "The full ZeroTrace course catalogue."},
    "roadmaps": {"path": "roadmaps/", "title": "Roadmaps", "icon": "route", "desc": "Role-based learning journeys from foundations to specialisation."},
    "cyber-range": {"path": "cyber-range/", "title": "Cyber Range", "icon": "server", "desc": "Private, isolated environments for authorised hands-on practice."},
    "virtual-labs": {"path": "cyber-range/virtual-labs/", "title": "Virtual Labs", "icon": "server", "desc": "Isolated Linux and Windows machines for practical exercises."},
    "attack-defence": {"path": "cyber-range/attack-defence/", "title": "Attack & Defence", "icon": "swords", "desc": "Red vs blue team exercises in isolated networks."},
    "soc-simulation": {"path": "cyber-range/soc-simulation/", "title": "SOC Simulation", "icon": "activity", "desc": "Triage generated alerts from training telemetry."},
    "forensic-investigations": {"path": "cyber-range/forensic-investigations/", "title": "Forensic Investigations", "icon": "file-search", "desc": "Prepared cases with disk images, memory dumps and captures."},
    "tools": {"path": "tools/", "title": "ZeroTrace Tools", "icon": "layout-grid", "desc": "The proposed family of ZeroTrace security tools."},
    "research": {"path": "research/", "title": "Research", "icon": "microscope", "desc": "Security research, publications and responsible disclosure."},
    "ctf": {"path": "ctf/", "title": "CTF Arena", "icon": "flag", "desc": "Capture-the-flag challenges in isolated environments."},
    "soc": {"path": "soc/", "title": "SOC Academy", "icon": "monitor-dot", "desc": "Defensive operations training from L1 to L3."},
    "forensics": {"path": "forensics/", "title": "Digital Forensics Centre", "icon": "fingerprint", "desc": "Evidence handling and investigation training."},
    "ai-learning": {"path": "ai-learning/", "title": "AI Learning", "icon": "sparkles", "desc": "An AI learning companion, planned for the platform."},
    "career": {"path": "career/", "title": "Career Academy", "icon": "briefcase", "desc": "Career roadmaps, assessments and interview preparation."},
    "community": {"path": "community/", "title": "Community", "icon": "users", "desc": "Discussions, study groups and project showcases."},
    "blog": {"path": "blog/", "title": "Blog", "icon": "newspaper", "desc": "News and articles from the ZeroTrace team."},
    "research-library": {"path": "research/library/", "title": "Research Library", "icon": "book-open-text", "desc": "Reviewed research publications."},
    "tutorials": {"path": "tutorials/", "title": "Tutorials", "icon": "book-open", "desc": "Short, focused technical tutorials."},
    "docs": {"path": "docs/", "title": "Documentation", "icon": "file-text", "desc": "Platform and tool documentation."},
    "about": {"path": "about/", "title": "About ZeroTrace", "icon": "info", "desc": "Who we are and what we're building."},
    "contact": {"path": "contact/", "title": "Contact", "icon": "mail", "desc": "Verified contact channels will be published here."},
    "careers": {"path": "careers/", "title": "Careers", "icon": "briefcase", "desc": "Work with the ZeroTrace team."},
    "privacy": {"path": "legal/privacy/", "title": "Privacy Policy", "icon": "lock", "desc": "How we handle personal data.", "legal": True},
    "terms": {"path": "legal/terms/", "title": "Terms and Conditions", "icon": "file-text", "desc": "The terms that govern use of the platform.", "legal": True},
    "acceptable-use": {"path": "legal/acceptable-use/", "title": "Acceptable Use Policy", "icon": "shield-check", "desc": "Rules for authorised, ethical use of labs and tools.", "legal": True},
    "responsible-disclosure": {"path": "legal/responsible-disclosure/", "title": "Responsible Disclosure", "icon": "shield-alert", "desc": "How to report a vulnerability in ZeroTrace.", "legal": True},
    "cookies": {"path": "legal/cookies/", "title": "Cookie Policy", "icon": "cookie", "desc": "How we use cookies.", "legal": True},
}

FOOTER = [
    {"title": "Platform", "links": [("Academy", "/academy/"), ("Courses", "/academy/courses/"), ("Roadmaps", "/roadmaps/"), ("Cyber Range", "/cyber-range/"), ("Tools", "/tools/"), ("CTF Arena", "/ctf/")]},
    {"title": "Departments", "links": [("Ethical Hacking", "/departments/ethical-hacking/"), ("SOC Operations", "/departments/soc-operations/"), ("Digital Forensics", "/departments/digital-forensics/"), ("Cloud Security", "/departments/cloud-security/"), ("Malware Research", "/departments/malware-analysis/"), ("AI Security", "/departments/ai-security/")]},
    {"title": "Resources", "links": [("Blog", "/blog/"), ("Research Library", "/research/library/"), ("Tutorials", "/tutorials/"), ("Documentation", "/docs/"), ("Community", "/community/")]},
    {"title": "Company", "links": [("About", "/about/"), ("Contact", "/contact/"), ("Careers", "/careers/"), ("Pricing", "/pricing/")]},
    {"title": "Legal", "links": [("Privacy Policy", "/legal/privacy/"), ("Terms and Conditions", "/legal/terms/"), ("Acceptable Use Policy", "/legal/acceptable-use/"), ("Responsible Disclosure", "/legal/responsible-disclosure/"), ("Cookie Policy", "/legal/cookies/")]},
]
