import hashlib

from practice.models import Challenge, Submission, Tool


class PracticeError(Exception):
    def __init__(self, message, status=403):
        super().__init__(message)
        self.message = message
        self.status = status


def launch_tool(user, tool):
    if tool.status != Tool.Status.AVAILABLE:
        raise PracticeError(f"{tool.name} is {tool.get_status_display().lower()}. It cannot be launched.", status=409)
    from accounts.access import has_membership

    if not has_membership(user, tool.required_plan):
        raise PracticeError("Your membership does not include this tool.")
    raise PracticeError("This tool has no connected engine on this server.", status=503)


def submit_flag(user, challenge, flag):
    if challenge.status != Challenge.Status.OPEN:
        raise PracticeError("That challenge is not open.", status=409)
    digest = hashlib.sha256((flag or "").strip().encode("utf-8")).hexdigest()
    correct = bool(challenge.flag_hash) and digest == challenge.flag_hash
    Submission.objects.create(user=user, challenge=challenge, correct=correct)
    if correct:
        from notifications.services import record_activity

        record_activity(user, "assessment", f"Solved {challenge.title}.")
    return correct
