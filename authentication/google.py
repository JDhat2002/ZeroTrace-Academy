import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

from authentication.exceptions import AuthError

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def configured():
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def authorization_url(redirect_uri, state):
    query = urllib.parse.urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
            "access_type": "online",
        }
    )
    return f"{AUTH_URL}?{query}"


def fetch_google_identity(code, redirect_uri):
    token = _post_form(
        TOKEN_URL,
        {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    access_token = token.get("access_token")
    if not access_token:
        raise AuthError("Google sign-in could not be completed. Try again.", code="google_token")
    return _get_json(USERINFO_URL, {"Authorization": f"Bearer {access_token}"})


def _post_form(url, payload):
    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    return _read_json(request)


def _get_json(url, headers):
    request = urllib.request.Request(url, headers=headers, method="GET")
    return _read_json(request)


def _read_json(request):
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeError) as exc:
        raise AuthError("Google sign-in could not be completed. Try again.", code="google_unavailable") from exc
