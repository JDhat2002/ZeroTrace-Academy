from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.countries import COUNTRIES
from authentication.exceptions import AuthError
from profiles.services import onboarding_payload, save_onboarding, update_profile

COUNTRY_NAMES = dict(COUNTRIES)


def _profile_payload(user):
    preference = user.preference
    avatar = ""
    if user.profile.avatar:
        avatar = user.profile.avatar.url
    return {
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "email_verified": bool(user.email_verified_at),
        "country": user.country,
        "country_name": COUNTRY_NAMES.get(user.country, user.country),
        "learning_interest": user.learning_interest,
        "experience_level": preference.experience_level,
        "interests": preference.interests,
        "objective": preference.objective,
        "daily_minutes": preference.daily_minutes,
        "membership": user.membership,
        "role": user.role,
        "date_joined": user.date_joined,
        "avatar": avatar,
    }


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def profile_api(request):
    if request.method == "GET":
        return Response(_profile_payload(request.user))
    try:
        notice = update_profile(request, request.data, request.FILES.get("avatar"))
    except AuthError as exc:
        body = {"detail": exc.message, "code": exc.code}
        if exc.field:
            body["field"] = exc.field
        return Response(body, status=exc.status)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)
    payload = _profile_payload(request.user)
    if notice:
        payload["detail"] = notice
    return Response(payload)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def onboarding_api(request):
    if request.method == "GET":
        return Response(onboarding_payload(request.user))
    try:
        save_onboarding(
            request.user,
            request.data,
            complete=bool(request.data.get("complete")),
            skip=bool(request.data.get("skip")),
        )
    except (ValueError, TypeError) as exc:
        return Response({"detail": str(exc)}, status=400)
    return Response(onboarding_payload(request.user))
