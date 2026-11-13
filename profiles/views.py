from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accounts.countries import COUNTRIES
from accounts.models import User
from authentication.exceptions import AuthError
from profiles.models import UserPreference
from profiles.services import onboarding_payload, recommend, save_onboarding, update_profile

MINUTES = [15, 30, 45, 60, 90, 120]


def _blocked(request):
    if request.session.get("mfa_setup_required"):
        return redirect("mfa-manage")
    return None


@require_http_methods(["GET", "POST"])
def dashboard_page(request):
    from workspace.views import home

    return home(request)


@login_required
@require_http_methods(["GET", "POST"])
def profile_page(request):
    blocked = _blocked(request)
    if blocked:
        return blocked
    error = ""
    notice = ""
    if request.method == "POST":
        data = {
            "full_name": request.POST.get("full_name"),
            "username": request.POST.get("username"),
            "country": request.POST.get("country"),
            "learning_interest": request.POST.get("learning_interest"),
            "experience_level": request.POST.get("experience_level"),
            "objective": request.POST.get("objective"),
            "daily_minutes": request.POST.get("daily_minutes") or None,
            "interests": request.POST.getlist("interests"),
            "current_password": request.POST.get("current_password"),
            "phone": request.POST.get("phone"),
            "education": request.POST.get("education"),
        }
        if request.POST.get("email"):
            data["email"] = request.POST.get("email")
        try:
            notice = update_profile(request, data, request.FILES.get("avatar")) or "Profile saved."
        except AuthError as exc:
            error = exc.message
        except ValueError as exc:
            error = str(exc)
    payload = onboarding_payload(request.user)
    return render(
        request,
        "account/profile.html",
        {
            "error": error,
            "notice": notice,
            "countries": COUNTRIES,
            "interests": User.Interest.choices,
            "levels": UserPreference.Level.choices,
            "objectives": UserPreference.Objective.choices,
            "topic_choices": UserPreference.INTEREST_CHOICES,
            "minutes": MINUTES,
            "selected_topics": set(payload["interests"] or []),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def onboarding_page(request):
    blocked = _blocked(request)
    if blocked:
        return blocked
    error = ""
    step = 1
    if request.method == "POST":
        step = int(request.POST.get("step") or 1)
        if request.POST.get("skip_all"):
            save_onboarding(request.user, {}, skip=True)
            return redirect("dashboard")
        if request.POST.get("finish"):
            save_onboarding(request.user, {}, complete=True)
            return redirect("dashboard")
        data = {}
        skipped = bool(request.POST.get("skip"))
        if not skipped and step == 2:
            data["experience_level"] = request.POST.get("experience_level") or ""
            if not data["experience_level"]:
                error = "Choose an experience level, or skip this step."
        elif not skipped and step == 3:
            data["interests"] = request.POST.getlist("interests")
            if not data["interests"]:
                error = "Choose at least one interest, or skip this step."
        elif not skipped and step == 4:
            data["objective"] = request.POST.get("objective") or ""
            if not data["objective"]:
                error = "Choose an objective, or skip this step."
        elif not skipped and step == 5:
            data["daily_minutes"] = request.POST.get("daily_minutes") or ""
            if not data["daily_minutes"]:
                error = "Choose a daily time, or skip this step."
        if not error:
            try:
                if not skipped and data:
                    save_onboarding(request.user, data)
            except ValueError as exc:
                error = str(exc)
            else:
                return redirect(f"/onboarding/?step={min(step + 1, 7)}")
    else:
        try:
            step = int(request.GET.get("step") or 1)
        except ValueError:
            step = 1
    step = min(max(step, 1), 7)
    payload = onboarding_payload(request.user)
    return render(
        request,
        "account/onboarding.html",
        {
            "step": step,
            "error": error,
            "levels": UserPreference.Level.choices,
            "objectives": UserPreference.Objective.choices,
            "topic_choices": UserPreference.INTEREST_CHOICES,
            "minutes": MINUTES,
            "recommendation": payload["recommendation"],
            "selected_topics": set(payload["interests"] or []),
            "preference": request.user.preference,
        },
    )
