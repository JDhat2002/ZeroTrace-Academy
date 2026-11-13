from django.utils import timezone

from accounts.access import has_membership
from labs.models import Lab, LabSession


class LabError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.message = message
        self.status = status


def start_lab(user, lab, action="start"):
    if lab.status != Lab.Status.AVAILABLE:
        LabSession.objects.create(
            user=user,
            lab=lab,
            status=LabSession.Status.REJECTED,
            detail="No environment is connected.",
            ended_at=timezone.now(),
        )
        raise LabError("This lab is not provisioned. No machine was started.")
    if not has_membership(user, lab.required_plan):
        raise LabError("Your membership does not include this lab.", status=403)
    raise LabError("The lab is marked available, but no hypervisor is configured for this server.", status=503)


def control_session(user, session, action):
    if session.user_id != user.id:
        raise LabError("That session is not yours.", status=404)
    if action not in {"stop", "restart", "reset", "snapshot", "extend"}:
        raise LabError("That action is not recognised.")
    raise LabError("No machine is connected, so this control was not sent.")
