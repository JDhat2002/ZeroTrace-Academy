from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from . import content, services


@require_GET
def home(request):
    category = services.valid_tool_filter(request.GET.get("category", "all"))
    roadmap = services.get_roadmap(request.GET.get("path", ""))
    context = {
        "highlights": content.HIGHLIGHTS,
        "departments": services.departments(),
        "range_features": content.RANGE_FEATURES,
        "tool_filters": services.tool_filters(),
        "active_filter": category,
        "tools": services.tools(category),
        "forensic_categories": content.FORENSIC_CATEGORIES,
        "soc_tracks": content.SOC_TRACKS,
        "roadmaps": services.roadmaps(),
        "roadmap": roadmap,
        "mentor_prompts": services.mentor_prompts(),
        "mentor_prompt": services.mentor_prompts()[0],
        "ctf_categories": content.CTF_CATEGORIES,
        "ctf_challenges": content.CTF_SAMPLE_CHALLENGES,
        "ctf_leaderboard": content.CTF_SAMPLE_LEADERBOARD,
        "career_features": content.CAREER_FEATURES,
        "career_tracks": content.CAREER_TRACKS,
        "community_features": content.COMMUNITY_FEATURES,
        "stats": services.platform_stats(),
        "plans": content.PLANS,
        "plan_comparison": content.PLAN_COMPARISON,
        "faqs": content.FAQS,
    }
    return render(request, "pages/home.html", context)


@require_GET
def tools_partial(request):
    category = services.valid_tool_filter(request.GET.get("category", "all"))
    return render(request, "partials/tool_grid.html", {
        "tools": services.tools(category),
        "tool_filters": services.tool_filters(),
        "active_filter": category,
    })


@require_GET
def roadmap_partial(request, slug):
    return render(request, "partials/roadmap_panel.html", {
        "roadmap": services.get_roadmap(slug),
        "roadmaps": services.roadmaps(),
    })


@require_GET
def mentor_partial(request, slug):
    prompt = services.get_mentor_prompt(slug)
    if prompt is None:
        raise Http404
    return render(request, "partials/mentor_reply.html", {"mentor_prompt": prompt})


@require_GET
def info_page(request, key):
    page = content.PAGES[key]
    context = {"page": page}
    if key == "tools":
        category = services.valid_tool_filter(request.GET.get("category", "all"))
        context.update(tools=services.tools(category), tool_filters=services.tool_filters(), active_filter=category)
    elif key == "roadmaps":
        context.update(roadmaps=services.roadmaps())
    return render(request, "pages/info.html", context)


@require_GET
def pricing(request):
    return render(request, "pages/pricing.html", {
        "plans": content.PLANS,
        "plan_comparison": content.PLAN_COMPARISON,
        "faqs": content.FAQS,
    })


@require_GET
def department_detail(request, slug):
    department = services.get_department(slug)
    if department is None:
        raise Http404
    page = {"title": department["title"], "icon": department["icon"], "desc": department["desc"], "eyebrow": f"Department · {department['level']}"}
    return render(request, "pages/info.html", {"page": page, "department": department})


@require_GET
def tool_detail(request, slug):
    tool = services.get_tool(slug)
    if tool is None:
        raise Http404
    page = {"title": tool["name"], "icon": tool["icon"], "desc": tool["desc"], "eyebrow": f"Tool · {tool['category']}"}
    return render(request, "pages/info.html", {"page": page, "tool": tool})


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to ZeroTrace Academy. Your account is ready.")
        return redirect("core:home")
    return render(request, "registration/register.html", {"form": form})


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /partials/",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
