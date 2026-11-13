import re

from django.utils import timezone

from accounts.models import User
from profiles.models import UserPreference

PATHS = {
    "soc": {
        "title": "SOC Analyst",
        "href": "/paths.html#soc-analyst",
        "duration": "5–7 months",
        "reason": "This path follows logs, triage, and incident response.",
    },
    "pentest": {
        "title": "Ethical Hacker",
        "href": "/paths.html#ethical-hacker",
        "duration": "6–9 months",
        "reason": "This path is for authorised testing and clear reporting.",
    },
    "forensics": {
        "title": "Digital Forensics Investigator",
        "href": "/paths.html#forensics-investigator",
        "duration": "6–8 months",
        "reason": "This path stays with evidence, timelines, and case notes.",
    },
    "cloud": {
        "title": "Cloud Security Engineer",
        "href": "/paths.html#cloud-security-engineer",
        "duration": "6–9 months",
        "reason": "This path covers identity, logging, and cloud response.",
    },
    "malware": {
        "title": "Malware Analyst",
        "href": "/paths.html#malware-analyst",
        "duration": "8–12 months",
        "reason": "This path is for isolated analysis of prepared samples.",
    },
    "engineering": {
        "title": "Security Engineer",
        "href": "/paths.html#security-engineer",
        "duration": "8–12 months",
        "reason": "This path is for building systems that are defensible.",
    },
    "fundamentals": {
        "title": "Foundations, then a role path",
        "href": "/catalog.html#cs-it-fundamentals",
        "duration": "Start here",
        "reason": "Begin with how computers, networks, and systems work, then pick a role.",
    },
}


def recommend(preference):
    interests = set(preference.interests or [])
    objective = preference.objective
    level = preference.experience_level
    if objective == UserPreference.Objective.SOC or "soc" in interests:
        key = "soc"
    elif objective == UserPreference.Objective.PENTEST or "ethical-hacking" in interests:
        key = "pentest"
    elif objective == UserPreference.Objective.FORENSICS or "forensics" in interests:
        key = "forensics"
    elif "cloud" in interests:
        key = "cloud"
    elif "malware" in interests:
        key = "malware"
    elif objective == UserPreference.Objective.ADVANCE or "engineering" in interests:
        key = "engineering"
    elif objective == UserPreference.Objective.EMPLOYMENT and level in {"advanced", "professional"}:
        key = "engineering" if "engineering" in interests else "soc"
    else:
        key = "fundamentals"
    return {"key": key, **PATHS[key]}


def save_onboarding(user, data, *, complete=False, skip=False):
    preference = user.preference
    if "experience_level" in data and data["experience_level"]:
        if data["experience_level"] not in UserPreference.Level.values:
            raise ValueError("Choose an experience level from the list.")
        preference.experience_level = data["experience_level"]
    if "interests" in data and data["interests"] is not None:
        unknown = set(data["interests"]) - UserPreference.INTEREST_KEYS
        if unknown:
            raise ValueError("One of the learning interests is not recognised.")
        preference.interests = list(dict.fromkeys(data["interests"]))
    if "objective" in data and data["objective"]:
        if data["objective"] not in UserPreference.Objective.values:
            raise ValueError("Choose a learning objective from the list.")
        preference.objective = data["objective"]
    if "daily_minutes" in data and data["daily_minutes"]:
        minutes = int(data["daily_minutes"])
        if minutes not in {15, 30, 45, 60, 90, 120}:
            raise ValueError("Choose a daily learning time from the list.")
        preference.daily_minutes = minutes
    preference.save()
    if skip or complete:
        if not user.onboarding_completed_at:
            user.onboarding_completed_at = timezone.now()
            user.save(update_fields=["onboarding_completed_at"])
    return preference


def onboarding_payload(user):
    preference = user.preference
    return {
        "completed": bool(user.onboarding_completed_at),
        "experience_level": preference.experience_level,
        "interests": preference.interests,
        "objective": preference.objective,
        "daily_minutes": preference.daily_minutes,
        "recommendation": recommend(preference),
    }


def registration_interest_is_valid(value):
    return value in User.Interest.values


def update_profile(request, data, avatar=None):
    from authentication.exceptions import AuthError
    from authentication.services import request_email_change, validate_avatar
    from accounts.countries import COUNTRY_CODES
    from accounts.validators import username_problems

    user = request.user
    forbidden = {"role", "membership", "is_staff", "is_superuser", "is_active", "password", "mfa_required"}
    if forbidden.intersection(data.keys()):
        raise AuthError("That field cannot be changed here.", status=403, code="forbidden")

    new_email = (data.get("email") or "").strip().lower() if "email" in data else user.email
    new_username = (data.get("username") or "").strip() if "username" in data else user.username
    needs_password = new_email != user.email or new_username != user.username
    if needs_password and not user.check_password(data.get("current_password") or ""):
        raise AuthError("Password confirmation did not match.", field="current_password", status=403)

    if "full_name" in data:
        full_name = (data.get("full_name") or "").strip()
        if not full_name or len(full_name) > 150:
            raise AuthError("Enter your full name.", field="full_name")
        user.full_name = full_name
    if "username" in data and new_username != user.username:
        problem = username_problems(new_username)
        if problem:
            raise AuthError(problem, field="username")
        if User.objects.filter(username__iexact=new_username).exclude(pk=user.pk).exists():
            raise AuthError("That username is taken. Choose another.", field="username")
        user.username = new_username
    if "country" in data:
        country = (data.get("country") or "").upper()
        if country and country not in COUNTRY_CODES:
            raise AuthError("Choose a country from the list.", field="country")
        user.country = country
    if "learning_interest" in data:
        interest = data.get("learning_interest") or ""
        if interest not in User.Interest.values:
            raise AuthError("Choose a learning interest.", field="learning_interest")
        user.learning_interest = interest
    user.save()

    preference_data = {}
    for key in ("experience_level", "interests", "objective", "daily_minutes"):
        if key in data:
            preference_data[key] = data.get(key)
    if preference_data:
        save_onboarding(user, preference_data)

    notice = ""
    if "email" in data and new_email != user.email:
        request_email_change(request, new_email)
        notice = "If that address can be used, a confirmation is on its way. Your sign-in email stays the same until you confirm it."

    profile = user.profile
    if "phone" in data:
        phone = (data.get("phone") or "").strip()
        if phone and not re.fullmatch(r"[0-9+() .-]{6,20}", phone):
            raise AuthError("Enter a phone number using digits and the usual symbols.", field="phone")
        profile.phone = phone
    if "education" in data:
        education = (data.get("education") or "").strip()
        if len(education) > 150:
            raise AuthError("Keep education to 150 characters.", field="education")
        profile.education = education
    if avatar:
        validate_avatar(avatar)
        profile.avatar = avatar
    if "phone" in data or "education" in data or avatar:
        profile.save()
    return notice
