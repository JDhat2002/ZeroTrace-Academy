from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from workspace.catalogue import ensure_catalogue


def member_required(view):
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.session.get("mfa_setup_required"):
            return redirect("mfa-manage")
        if not request.user.onboarding_completed_at:
            return redirect("onboarding")
        ensure_catalogue()
        return view(request, *args, **kwargs)

    return wrapped
