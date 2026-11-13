"""Department and learning-path structure.

Topics name what a department will teach. They are not published courses.
"""

DEPARTMENTS = [
    (1, "computer-science", "Computer Science and IT Fundamentals", "How computers, operating systems, and networks are organised.", ["Computer fundamentals", "Operating systems", "Hardware architecture", "Computer networks introduction", "Filesystems", "Processes and memory", "Command-line fundamentals", "Virtualisation"]),
    (2, "networking", "Networking and Network Engineering", "How traffic is addressed, forwarded, and observed.", ["TCP/IP", "OSI model", "Routing and switching", "Subnetting", "DNS", "DHCP", "VLAN", "Firewalls", "VPN", "Network troubleshooting", "Network monitoring"]),
    (3, "linux-security", "Linux Security", "Linux administration and host hardening.", ["Linux fundamentals", "Shell commands", "Users and groups", "Permissions", "Processes", "Services", "Linux hardening", "SSH security", "Logs", "Privilege concepts in isolated labs"]),
    (4, "windows-security", "Windows Security", "Windows administration and endpoint security.", ["Windows architecture", "Windows administration", "PowerShell", "Registry", "Windows Event Logs", "Active Directory fundamentals", "Windows hardening", "Endpoint security"]),
    (5, "programming", "Programming and Scripting", "Programming used to automate and review security work.", ["Python", "Bash", "PowerShell", "JavaScript", "C fundamentals", "Secure programming", "Automation", "Security scripting"]),
    (6, "cryptography", "Cryptography and PKI", "How confidentiality, integrity, and trust are constructed.", ["Cryptographic fundamentals", "Symmetric encryption", "Asymmetric encryption", "Hashing", "Digital signatures", "Certificates", "TLS", "PKI", "Key management"]),
    (7, "ethical-hacking", "Ethical Hacking", "Authorised testing methodology and professional reporting.", ["Methodology", "Reconnaissance", "Enumeration", "Vulnerability assessment", "Exploitation fundamentals", "Privilege escalation", "Reporting", "Remediation", "Professional ethics and authorisation"]),
    (8, "web-application-security", "Web Application Security", "How web applications fail and how those failures are reported.", ["HTTP and HTTPS", "Authentication", "Session security", "Access control", "SQL injection", "Cross-site scripting", "CSRF", "SSRF", "XXE", "File upload security", "Business logic testing", "Secure development"]),
    (9, "api-security", "API Security", "How APIs authenticate callers and limit access.", ["REST APIs", "GraphQL", "Authentication and authorisation", "API tokens", "Rate limiting", "BOLA and IDOR", "API testing", "API gateway security"]),
    (10, "network-penetration-testing", "Network Penetration Testing", "Authorised network testing and reporting.", ["Network discovery", "Port scanning", "Service enumeration", "Vulnerability analysis", "Network exploitation concepts", "Segmentation testing", "Network security reporting"]),
    (11, "wireless-security", "Wireless and Radio Security", "Wireless systems and authorised audits.", ["Wireless fundamentals", "Wi-Fi architecture", "WPA2 and WPA3", "Wireless audits", "Bluetooth security", "Wireless monitoring", "Radio-frequency security fundamentals"]),
    (12, "active-directory", "Active Directory and Identity Security", "Identity, directory services, and privileged access.", ["Active Directory", "Kerberos", "LDAP", "Group Policy", "Identity management", "Privileged access", "AD security assessment", "Identity threat detection"]),
    (13, "red-team", "Red Team Operations", "Authorised adversary exercises and reporting.", ["Red-team methodology", "Rules of engagement", "Attack-path analysis", "Controlled adversary simulation", "Security validation", "Reporting", "MITRE ATT&CK mapping"]),
    (14, "blue-team", "Blue Team Operations", "Defensive monitoring and detection.", ["Defensive security", "Endpoint monitoring", "Network monitoring", "Detection engineering", "Threat analysis", "Defensive hardening", "Security operations"]),
    (15, "purple-team", "Purple Team Operations", "How attack and defence exercises improve detection.", ["Attack and defence collaboration", "Detection validation", "Adversary emulation", "Detection improvement", "Security control assessment"]),
    (16, "soc-operations", "SOC Operations", "Alert triage and security operations.", ["SOC L1, L2 and L3", "SIEM", "Log analysis", "Alert triage", "Incident classification", "EDR and XDR", "Threat hunting", "Detection rules", "Case management"]),
    (17, "digital-forensics", "Digital and Cyber Forensics", "Evidence handling and forensic reporting.", ["Computer forensics", "Disk forensics", "Memory forensics", "Mobile forensics", "Network forensics", "Email forensics", "Windows artefacts", "Linux artefacts", "Cloud forensics", "Evidence preservation", "Chain of custody", "Forensic reporting"]),
    (18, "malware-analysis", "Malware Analysis and Reverse Engineering", "Contained sample analysis. No live samples are stored with the department.", ["Malware fundamentals", "Static analysis", "Dynamic analysis", "PE and ELF analysis", "Strings and imports", "Behavioural analysis", "Reverse engineering", "YARA rules", "Malware containment"]),
    (19, "threat-intelligence", "Threat Intelligence and Threat Hunting", "Intelligence notes and hunting method.", ["OSINT", "IOC analysis", "Threat intelligence", "Threat actor tracking", "MITRE ATT&CK", "Threat hunting", "Intelligence reporting"]),
    (20, "incident-response", "Incident Response", "How an incident is handled from identification to review.", ["Incident identification", "Triage", "Containment", "Eradication", "Recovery", "Post-incident review", "Evidence preservation", "Incident reporting"]),
    (21, "cloud-security", "Cloud Security", "Identity, logging, and posture in cloud accounts.", ["AWS", "Microsoft Azure", "Google Cloud", "IAM", "Storage security", "Network security", "Cloud logging", "Cloud threat detection", "Cloud posture assessment"]),
    (22, "devsecops", "DevSecOps and Application Security", "Security in the software lifecycle.", ["Secure SDLC", "CI/CD security", "SAST", "DAST", "SCA", "Secret scanning", "Dependency security", "Secure deployment"]),
    (23, "container-security", "Container and Kubernetes Security", "Image, cluster, and runtime controls.", ["Docker", "Container hardening", "Image security", "Kubernetes architecture", "RBAC", "Network policies", "Runtime security", "Container vulnerability management"]),
    (24, "mobile-security", "Mobile Application Security", "Mobile application structure and testing scope.", ["Android security", "iOS security", "Mobile application architecture", "Secure storage", "API communication", "Application testing", "Mobile malware fundamentals"]),
    (25, "iot-security", "IoT and Embedded Security", "Device and firmware security at a curriculum level.", ["IoT architecture", "Firmware analysis", "Device security", "Embedded systems", "Hardware interfaces", "IoT communication", "Secure firmware"]),
    (26, "hardware-security", "Hardware Security", "Hardware trust and device interfaces.", ["Hardware fundamentals", "Secure boot", "Firmware security", "Side-channel concepts", "Hardware interfaces", "Device testing"]),
    (27, "ot-security", "OT/ICS/SCADA Security", "Industrial systems, with safety kept ahead of simulation.", ["Industrial control systems", "SCADA architecture", "OT networking", "Industrial protocols", "Asset visibility", "Segmentation", "Defensive monitoring", "Safety-focused simulation"]),
    (28, "database-security", "Database and Data Security", "Access, encryption, and auditing for data stores.", ["Database security", "SQL fundamentals", "Access control", "Encryption", "Backup security", "Data protection", "Database auditing"]),
    (29, "ai-security", "AI, ML and LLM Security", "How AI systems fail and how those risks are described.", ["AI security fundamentals", "Machine learning security", "Prompt injection", "LLM application security", "Data leakage", "Model security", "AI threat modelling", "Secure AI development"]),
    (30, "blockchain-security", "Blockchain and Smart Contract Security", "Contracts, wallets, and audit reporting.", ["Blockchain fundamentals", "Smart contracts", "Solidity security", "Common contract weaknesses", "Wallet security", "Blockchain forensics", "Contract auditing"]),
    (31, "governance", "Governance, Risk and Compliance", "Policy, risk, and audit practice.", ["Information security governance", "Risk assessment", "ISO 27001", "NIST frameworks", "Security policies", "Compliance", "Audit management", "Privacy fundamentals"]),
    (32, "security-architecture", "Security Architecture and Engineering", "How security is designed into systems.", ["Security architecture", "Zero Trust", "Identity architecture", "Network architecture", "Secure systems engineering", "Threat modelling", "Security design reviews"]),
]

OBJECTIVES = [
    "Describe the subject in accurate terms.",
    "Recognise the defensive or authorised-testing context.",
    "Record findings without treating a preview as a completed qualification.",
]

SKILLS = ["Foundations", "Guided practice when a course is published", "Assessment when an instructor publishes one"]

PATHS = [
    ("cybersecurity-fundamentals", "Cybersecurity Fundamentals", "Foundations before a specialist path."),
    ("ethical-hacker-path", "Ethical Hacker", "Authorised testing from scope to a written report."),
    ("penetration-tester-path", "Penetration Tester", "Scoped testing and evidence-backed reporting."),
    ("soc-analyst-l1", "SOC Analyst L1", "Alert triage and escalation."),
    ("soc-analyst-l2", "SOC Analyst L2", "Deeper investigation after triage."),
    ("forensics-investigator-path", "Digital Forensics Investigator", "Evidence handling and timelines."),
    ("malware-analyst-path", "Malware Analyst", "Contained analysis once a lab exists."),
    ("network-security-engineer-path", "Network Security Engineer", "Traffic, segmentation, and detection."),
    ("cloud-security-engineer-path", "Cloud Security Engineer", "Identity and logging in cloud accounts."),
    ("web-security-specialist", "Web Application Security Specialist", "Web flaws classified and reported."),
    ("red-team-specialist", "Red Team Specialist", "Authorised adversary exercises inside an isolated range."),
    ("blue-team-specialist", "Blue Team Specialist", "Detection and response."),
    ("incident-responder-path", "Incident Responder", "Identification through post-incident review."),
    ("threat-intelligence-analyst", "Threat Intelligence Analyst", "Intelligence notes and hunting."),
    ("application-security-engineer", "Application Security Engineer", "Reviewing software and reporting defects."),
    ("security-architect-path", "Security Architect", "Security design and review."),
]

COURSE_DEPARTMENTS = {
    "network-foundations": "networking",
    "linux-controls": "linux-security",
    "web-security": "web-application-security",
    "soc-fundamentals": "soc-operations",
    "forensics-intro": "digital-forensics",
    "ad-security": "active-directory",
}


def sync_curriculum():
    from learning.models import AcademyDepartment, Course, LearningPath

    for number, slug, name, overview, topics in DEPARTMENTS:
        AcademyDepartment.objects.update_or_create(
            slug=slug,
            defaults={
                "number": number,
                "name": name,
                "overview": overview,
                "description": "Courses in this department are published only when their lessons and assessments are ready.",
                "objectives": OBJECTIVES,
                "skills": SKILLS,
                "topics": topics,
            },
        )
    departments = {row.slug: row for row in AcademyDepartment.objects.all()}
    for course_slug, department_slug in COURSE_DEPARTMENTS.items():
        department = departments.get(department_slug)
        if department is None:
            continue
        Course.objects.filter(slug=course_slug, academy_department__isnull=True).update(
            academy_department=department,
            department=department.name,
            department_key=department.slug,
        )
    for index, (slug, title, summary) in enumerate(PATHS, start=1):
        LearningPath.objects.get_or_create(
            slug=slug,
            defaults={
                "title": title,
                "summary": summary,
                "skills": [],
                "duration_label": "Set when courses are attached",
                "sort_order": 100 + index,
                "certificate_eligible": False,
            },
        )
