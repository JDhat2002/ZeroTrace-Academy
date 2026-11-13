const header = document.querySelector(".site-header");
const toggle = document.querySelector(".nav-toggle");
const nav = document.querySelector("#site-nav");

const onScroll = () => {
  header?.classList.toggle("is-scrolled", window.scrollY > 8);
};

onScroll();
window.addEventListener("scroll", onScroll, { passive: true });

const closeNav = () => {
  nav?.classList.remove("is-open");
  header?.classList.remove("is-open");
  toggle?.setAttribute("aria-expanded", "false");
  const label = toggle?.querySelector(".sr-only");
  if (label) label.textContent = "Open menu";
  document.body.classList.remove("nav-lock");
};

toggle?.addEventListener("click", () => {
  const open = nav.classList.toggle("is-open");
  header?.classList.toggle("is-open", open);
  toggle.setAttribute("aria-expanded", String(open));
  const label = toggle.querySelector(".sr-only");
  if (label) label.textContent = open ? "Close menu" : "Open menu";
  document.body.classList.toggle("nav-lock", open);
});

document.querySelectorAll(".nav-drop").forEach((button) => {
  button.addEventListener("click", () => {
    const item = button.closest(".nav-item");
    const willOpen = !item.classList.contains("is-open");
    document.querySelectorAll(".nav-item.is-open").forEach((other) => {
      if (other === item) return;
      other.classList.remove("is-open");
      other.querySelector(".nav-drop")?.setAttribute("aria-expanded", "false");
    });
    item.classList.toggle("is-open", willOpen);
    button.setAttribute("aria-expanded", String(willOpen));
  });
});

document.addEventListener("click", (event) => {
  if (event.target.closest(".nav-item") || event.target.closest(".nav-toggle")) return;
  document.querySelectorAll(".nav-item.is-open").forEach((item) => {
    item.classList.remove("is-open");
    item.querySelector(".nav-drop")?.setAttribute("aria-expanded", "false");
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  closeNav();
  document.querySelectorAll(".nav-item.is-open").forEach((item) => {
    item.classList.remove("is-open");
    item.querySelector(".nav-drop")?.setAttribute("aria-expanded", "false");
  });
  toggle?.focus();
});

nav?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 1179px)").matches) closeNav();
  });
});

const file = (location.pathname.split("/").filter(Boolean).pop() || "index.html").toLowerCase();
document.querySelectorAll("[data-nav]").forEach((el) => {
  const targets = el.dataset.nav.toLowerCase().split(/\s+/);
  if (targets.includes(file)) el.setAttribute("aria-current", "page");
});

document.querySelectorAll(".faq-item button").forEach((button) => {
  button.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    const panel = document.getElementById(button.getAttribute("aria-controls"));
    document.querySelectorAll(".faq-item button").forEach((other) => {
      if (other === button) return;
      other.setAttribute("aria-expanded", "false");
      const otherPanel = document.getElementById(other.getAttribute("aria-controls"));
      if (otherPanel) otherPanel.hidden = true;
    });
    button.setAttribute("aria-expanded", String(!expanded));
    if (panel) panel.hidden = expanded;
  });
});

const filterButtons = document.querySelectorAll(".filters button");
const tools = document.querySelectorAll(".tool");
const count = document.querySelector("[data-count]");

const applyFilter = (key) => {
  let shown = 0;
  tools.forEach((tool) => {
    const tags = (tool.dataset.tags || "").split(/\s+/);
    const match = key === "all" || tags.includes(key);
    tool.hidden = !match;
    if (match) shown += 1;
  });
  if (count) count.textContent = `Showing ${shown} of ${tools.length} proposed tools`;
};

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((other) => {
      other.setAttribute("aria-pressed", String(other === button));
    });
    applyFilter(button.dataset.filter);
  });
});

if (tools.length) {
  const initial = new URLSearchParams(location.search).get("filter") || "all";
  const start = [...filterButtons].find((button) => button.dataset.filter === initial) || filterButtons[0];
  if (start) {
    filterButtons.forEach((other) => other.setAttribute("aria-pressed", String(other === start)));
    applyFilter(start.dataset.filter || "all");
  } else {
    applyFilter("all");
  }
}

document.querySelectorAll("[data-tabs]").forEach((widget) => {
  const tabs = [...widget.querySelectorAll("[data-tab]")];
  const panels = [...widget.querySelectorAll("[data-panel]")];
  const select = (name) => {
    tabs.forEach((tab) => tab.setAttribute("aria-selected", String(tab.dataset.tab === name)));
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.panel !== name;
    });
  };
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => select(tab.dataset.tab));
  });
});

const mentorReplies = {
  ask: "Preview only. No model is connected. A future mentor can explain a concept, name the skill it belongs to, and point you at a learning path. It will not give steps for attacking a system you do not own.",
  vuln: "A vulnerability is a weakness that could be misused. In training you describe the weakness, who it affects, and what a defender would change. That work happens on lab systems provided for the exercise.",
  lab: "Lab results, once the range exists, should be read as evidence: what you observed, what it implies, and what you would report. This preview cannot see a live machine.",
  rule: "A detection rule is a hypothesis about attacker behaviour, written so an analyst can test it against authorised telemetry. This box cannot evaluate a rule yet.",
  report: "An investigation report states scope, evidence, timeline, and what remains uncertain. This preview cannot review a document you paste in.",
  path: "Pick a role, then follow the published roadmap: foundations first, then the specialist modules. Progress tracking appears after accounts exist. Accounts are not open."
};

document.querySelectorAll("[data-mentor]").forEach((button) => {
  button.addEventListener("click", () => {
    const reply = document.querySelector("[data-mentor-reply]");
    const text = document.querySelector("[data-mentor-text]");
    document.querySelectorAll("[data-mentor]").forEach((other) => {
      other.setAttribute("aria-pressed", String(other === button));
    });
    if (text) text.textContent = mentorReplies[button.dataset.mentor] || mentorReplies.ask;
    if (reply) reply.hidden = false;
  });
});

const mentorForm = document.querySelector("#mentor-form");
mentorForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  const reply = document.querySelector("[data-mentor-reply]");
  const text = document.querySelector("[data-mentor-text]");
  if (text) {
    text.textContent = "Preview reply. No question left this browser, and no model answered it. ZeroTrace will not provide attack steps for systems outside an authorised lab. Use the learning paths while the mentor is still a design preview.";
  }
  if (reply) reply.hidden = false;
});

const homeSearch = document.querySelector("#home-search");
const homeResults = document.querySelector("#home-search-results");
const homeIndex = [
  ["Course", "CS & IT Fundamentals", "catalog.html#cs-it-fundamentals", "computers operating systems"],
  ["Course", "Networking", "catalog.html#networking", "tcp dns routing"],
  ["Course", "Linux Security", "catalog.html#linux-security", "command line permissions"],
  ["Course", "Windows Security", "catalog.html#windows-security", "event logs powershell"],
  ["Course", "Programming & Scripting", "catalog.html#programming-scripting", "python bash"],
  ["Course", "Cryptography", "catalog.html#cryptography", "hashing encryption"],
  ["Course", "Ethical Hacking", "catalog.html#ethical-hacking", "authorised testing"],
  ["Course", "Web Application Security", "catalog.html#web-application-security", "owasp"],
  ["Course", "API Security", "catalog.html#api-security", "rest graphql"],
  ["Course", "Network Penetration Testing", "catalog.html#network-penetration-testing", "authorised assessment"],
  ["Course", "Wireless Security", "catalog.html#wireless-security", "wifi"],
  ["Course", "Active Directory Security", "catalog.html#active-directory-security", "identity kerberos"],
  ["Course", "Red Team Operations", "catalog.html#red-team-operations", "adversary emulation"],
  ["Course", "Blue Team Operations", "catalog.html#blue-team-operations", "monitoring defence"],
  ["Course", "Purple Team Operations", "catalog.html#purple-team-operations", "detection validation"],
  ["Course", "SOC Operations", "catalog.html#soc-operations", "siem triage alerts"],
  ["Course", "Digital Forensics", "catalog.html#digital-forensics", "evidence"],
  ["Course", "Malware Analysis", "catalog.html#malware-analysis", "sandbox"],
  ["Course", "Threat Intelligence", "catalog.html#threat-intelligence", "adversaries"],
  ["Course", "Incident Response", "catalog.html#incident-response", "contain recover"],
  ["Course", "Cloud Security", "catalog.html#cloud-security", "iam logging"],
  ["Course", "DevSecOps", "catalog.html#devsecops", "pipeline"],
  ["Course", "Container & Kubernetes Security", "catalog.html#container-kubernetes-security", "kubernetes"],
  ["Course", "Mobile Security", "catalog.html#mobile-security", "android ios"],
  ["Course", "IoT & Hardware Security", "catalog.html#iot-hardware-security", "firmware"],
  ["Course", "OT / ICS Security", "catalog.html#ot-ics-security", "industrial"],
  ["Course", "Database Security", "catalog.html#database-security", "access control"],
  ["Course", "AI Security", "catalog.html#ai-security", "models"],
  ["Course", "Blockchain Security", "catalog.html#blockchain-security", "smart contracts"],
  ["Course", "Governance, Risk & Compliance", "catalog.html#grc", "iso nist policy"],
  ["Course", "Security Architecture", "catalog.html#security-architecture", "zero trust"],
  ["Path", "ZeroTrace Foundations", "paths.html#foundations", "beginner digital literacy"],
  ["Path", "Ethical Hacker", "paths.html#ethical-hacker", "roadmap"],
  ["Path", "SOC Analyst", "paths.html#soc-analyst", "triage detection"],
  ["Path", "Digital Forensics Investigator", "paths.html#forensics-investigator", "evidence"],
  ["Path", "Cloud Security Engineer", "paths.html#cloud-security-engineer", "cloud"],
  ["Path", "Malware Analyst", "paths.html#malware-analyst", "analysis"],
  ["Path", "Security Engineer", "paths.html#security-engineer", "devsecops architecture"],
  ["Tool", "TraceScan", "tools.html#tracescan", "network"],
  ["Tool", "TraceMap", "tools.html#tracemap", "network"],
  ["Tool", "WebProbe", "tools.html#webprobe", "web"],
  ["Tool", "API Sentinel", "tools.html#api-sentinel", "api"],
  ["Tool", "VulnMatrix", "tools.html#vulnmatrix", "vulnerabilities"],
  ["Tool", "ADVision", "tools.html#advision", "active directory"],
  ["Tool", "PacketScope", "tools.html#packetscope", "packets"],
  ["Tool", "TraceSIEM", "tools.html#tracesiem", "siem logs"],
  ["Tool", "ThreatHunter", "tools.html#threathunter", "hunting"],
  ["Tool", "RuleForge", "tools.html#ruleforge", "detection rules"],
  ["Tool", "ForenSight", "tools.html#forensight", "forensics"],
  ["Tool", "MemoryScope", "tools.html#memoryscope", "memory"],
  ["Tool", "MalwareLab", "tools.html#malwarelab", "malware"],
  ["Tool", "CloudSentinel", "tools.html#cloudsentinel", "cloud"],
  ["Tool", "ContainerGuard", "tools.html#containerguard", "containers"],
  ["Tool", "MobileTrace", "tools.html#mobiletrace", "mobile"],
  ["Tool", "CodeShield", "tools.html#codeshield", "code"],
  ["Tool", "CryptoScope", "tools.html#cryptoscope", "cryptography"],
  ["Tool", "OSINT Navigator", "tools.html#osint-navigator", "open source"],
  ["Tool", "RangeControl", "tools.html#rangecontrol", "labs"],
  ["Tool", "IncidentDesk", "tools.html#incidentdesk", "incident response"],
  ["Tool", "AttackSim", "tools.html#attacksim", "simulation"],
  ["Tool", "WirelessScope", "tools.html#wirelessscope", "wireless"],
  ["Tool", "ThreatIntel Hub", "tools.html#threatintel-hub", "intelligence"],
  ["Range", "SOC tracks", "range.html#soc", "triage siem hunting edr detection"],
  ["Range", "Cyber range", "range.html", "labs virtual machines"],
  ["Range", "CTF arena", "range.html#ctf", "challenges"],
  ["Range", "Forensic investigations", "range.html#forensics", "evidence"],
  ["Page", "Pricing", "pricing.html", "plans membership"],
  ["Language", "English", "lang:en", "english"],
  ["Language", "Mandarin Chinese", "lang:zh", "中文 chinese mandarin"],
  ["Language", "Hindi", "lang:hi", "हिन्दी hindi"],
  ["Language", "Spanish", "lang:es", "español spanish"],
  ["Language", "French", "lang:fr", "français french"],
  ["Language", "Arabic", "lang:ar", "العربية arabic"],
  ["Language", "Bengali", "lang:bn", "বাংলা bengali bangla"],
  ["Language", "Portuguese", "lang:pt", "português portuguese"],
  ["Language", "Russian", "lang:ru", "русский russian"],
  ["Language", "Urdu", "lang:ur", "اردو urdu"],
  ["Language", "Indonesian", "lang:id", "bahasa indonesia indonesian"],
  ["Language", "German", "lang:de", "deutsch german"],
  ["Language", "Japanese", "lang:ja", "日本語 japanese"],
  ["Language", "Nigerian Pidgin", "lang:pcm", "naijá pidgin"],
  ["Language", "Marathi", "lang:mr", "मराठी marathi"],
  ["Language", "Telugu", "lang:te", "తెలుగు telugu"],
  ["Language", "Turkish", "lang:tr", "türkçe turkish"],
  ["Language", "Tamil", "lang:ta", "தமிழ் tamil"],
  ["Language", "Yue Chinese", "lang:yue", "粵語 cantonese yue"],
  ["Language", "Vietnamese", "lang:vi", "tiếng việt vietnamese"]
];

const languageButtons = [...document.querySelectorAll(".lang-option")];
const languageToggle = document.querySelector(".lang-toggle");
const languageMenu = document.querySelector("#lang-menu");
const languageLabel = document.querySelector("[data-lang-label]");

const chooseLanguage = (code) => {
  const button = languageButtons.find((item) => item.dataset.lang === code);
  if (!button) return;
  languageButtons.forEach((item) => {
    const on = item === button;
    item.classList.toggle("is-on", on);
    item.setAttribute("aria-selected", String(on));
  });
  if (languageLabel) languageLabel.textContent = button.dataset.native || button.dataset.name;
  try { localStorage.setItem("zt-language", code); } catch (error) { /* private mode */ }
  document.documentElement.lang = code;
  if (languageMenu) languageMenu.hidden = true;
  languageToggle?.setAttribute("aria-expanded", "false");
};

languageToggle?.addEventListener("click", () => {
  const open = languageMenu.hidden;
  languageMenu.hidden = !open;
  languageToggle.setAttribute("aria-expanded", String(open));
});

languageButtons.forEach((button) => {
  button.addEventListener("click", () => chooseLanguage(button.dataset.lang));
});

document.addEventListener("click", (event) => {
  if (!languageMenu || event.target.closest(".lang-switch")) return;
  languageMenu.hidden = true;
  languageToggle?.setAttribute("aria-expanded", "false");
});

if (languageButtons.length) {
  let saved = "";
  try { saved = localStorage.getItem("zt-language") || ""; } catch (error) { saved = ""; }
  const initial = languageButtons.some((item) => item.dataset.lang === saved) ? saved : "en";
  chooseLanguage(initial);
}

if (homeSearch && homeResults) {
  let active = -1;
  const matchesFor = (query) => {
    const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (!words.length) return [];
    return homeIndex.filter((row) => {
      const haystack = `${row[0]} ${row[1]} ${row[3]}`.toLowerCase();
      return words.every((word) => haystack.includes(word));
    }).slice(0, 8);
  };
  const paint = (matches, query) => {
    homeResults.replaceChildren();
    active = -1;
    if (!query.trim()) {
      homeResults.hidden = true;
      homeSearch.setAttribute("aria-expanded", "false");
      return;
    }
    if (!matches.length) {
      const item = document.createElement("li");
      item.className = "home-search-empty";
      item.textContent = "No courses, paths, tools, or languages match that search.";
      homeResults.append(item);
    } else {
      matches.forEach((row, index) => {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = row[2].startsWith("lang:") ? "#study-languages" : row[2];
        if (row[2].startsWith("lang:")) link.dataset.lang = row[2].slice(5);
        link.id = `home-search-option-${index}`;
        link.setAttribute("role", "option");
        const kind = document.createElement("span");
        kind.className = "kind";
        kind.textContent = row[0];
        link.append(kind, document.createTextNode(row[1]));
        item.append(link);
        homeResults.append(item);
      });
    }
    homeResults.hidden = false;
    homeSearch.setAttribute("aria-expanded", "true");
  };
  const options = () => [...homeResults.querySelectorAll("a")];
  const mark = (index) => {
    const links = options();
    active = index;
    links.forEach((link, i) => link.classList.toggle("is-active", i === active));
    if (links[active]) homeSearch.setAttribute("aria-activedescendant", links[active].id);
    else homeSearch.removeAttribute("aria-activedescendant");
  };
  homeSearch.addEventListener("input", () => paint(matchesFor(homeSearch.value), homeSearch.value));
  homeSearch.form?.addEventListener("submit", (event) => {
    const links = options();
    const chosen = links[active] || links[0];
    if (chosen?.dataset.lang) {
      event.preventDefault();
      chooseLanguage(chosen.dataset.lang);
      homeResults.hidden = true;
      homeSearch.setAttribute("aria-expanded", "false");
      return;
    }
    if (chosen) {
      event.preventDefault();
      window.location.href = chosen.href;
      return;
    }
    if (!homeSearch.value.trim() || !links.length) event.preventDefault();
  });
  homeSearch.addEventListener("keydown", (event) => {
    const links = options();
    if (event.key === "ArrowDown" && links.length) {
      event.preventDefault();
      mark(Math.min(active + 1, links.length - 1));
    } else if (event.key === "ArrowUp" && links.length) {
      event.preventDefault();
      mark(Math.max(active - 1, 0));
    } else if (event.key === "Escape") {
      homeResults.hidden = true;
      homeSearch.setAttribute("aria-expanded", "false");
    }
  });
  homeResults.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-lang]");
    if (!link) return;
    event.preventDefault();
    chooseLanguage(link.dataset.lang);
    homeResults.hidden = true;
    homeSearch.setAttribute("aria-expanded", "false");
  });
  document.addEventListener("click", (event) => {
    if (event.target.closest(".home-search")) return;
    homeResults.hidden = true;
    homeSearch.setAttribute("aria-expanded", "false");
  });
}

const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!reduce && "IntersectionObserver" in window) {
  document.documentElement.classList.add("reveal-ready");
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-in");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
}
