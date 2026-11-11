"""Read access to site content.

Views and template tags call these functions rather than importing
`core.content` directly, so swapping to database-backed models later only
changes this module.
"""

from . import content


def departments():
    return content.DEPARTMENTS


def get_department(slug):
    return next((d for d in content.DEPARTMENTS if d["slug"] == slug), None)


def tool_filters():
    return content.TOOL_FILTERS


def valid_tool_filter(key):
    keys = {f["key"] for f in content.TOOL_FILTERS}
    return key if key in keys else "all"


def tools(category="all"):
    items = content.TOOLS
    if category and category != "all":
        items = [t for t in items if category in t["filters"]]
    return [{**t, "status": content.TOOL_STATUS} for t in items]


def get_tool(slug):
    tool = next((t for t in content.TOOLS if t["slug"] == slug), None)
    return {**tool, "status": content.TOOL_STATUS} if tool else None


def roadmaps():
    return content.ROADMAPS


def get_roadmap(slug):
    return next((r for r in content.ROADMAPS if r["slug"] == slug), content.ROADMAPS[0])


def mentor_prompts():
    return content.AI_MENTOR_PROMPTS


def get_mentor_prompt(slug):
    return next((p for p in content.AI_MENTOR_PROMPTS if p["slug"] == slug), None)


def platform_stats():
    """Factual scope figures only; every value is derived from real content."""
    return [
        {"value": len(content.DEPARTMENTS), "label": "Cybersecurity departments", "note": "From fundamentals to AI security"},
        {"value": len(content.TOOLS), "label": "Proposed ZeroTrace tools", "note": "In planning and development"},
        {"value": len(content.RANGE_FEATURES), "label": "Practical lab categories", "note": "Planned for the Cyber Range"},
        {"value": len(content.ROADMAPS), "label": "Learning paths", "note": "Role-based career roadmaps"},
    ]
