import re

from django.contrib.auth.password_validation import CommonPasswordValidator, NumericPasswordValidator
from django.core.exceptions import ValidationError

USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,29}$")


def username_problems(username):
    if not USERNAME_RE.fullmatch(username or ""):
        return "Use 3–30 characters: a letter first, then letters, numbers, or underscores."
    return ""


def password_problems(password, *, username="", email="", full_name=""):
    problems = []
    password = password or ""
    if len(password) < 12:
        problems.append("Use at least 12 characters.")
    if not any(character.islower() for character in password):
        problems.append("Add a lowercase letter.")
    if not any(character.isupper() for character in password):
        problems.append("Add an uppercase letter.")
    if not any(character.isdigit() for character in password):
        problems.append("Add a number.")
    if not any(not character.isalnum() for character in password):
        problems.append("Add a symbol.")
    lowered = password.lower()
    fragments = [username, full_name]
    if email and "@" in email:
        fragments.append(email.split("@", 1)[0])
    for fragment in fragments:
        piece = (fragment or "").strip().lower()
        if len(piece) >= 3 and piece in lowered:
            problems.append("Don't include your name, username, or email.")
            break
    for validator in (CommonPasswordValidator(), NumericPasswordValidator()):
        try:
            validator.validate(password)
        except ValidationError as exc:
            for message in exc.messages:
                if message not in problems:
                    problems.append(message)
    return problems


def password_score(password):
    if not password:
        return 0
    score = 0
    if len(password) >= 12:
        score += 1
    if any(character.islower() for character in password) and any(character.isupper() for character in password):
        score += 1
    if any(character.isdigit() for character in password) and any(not character.isalnum() for character in password):
        score += 1
    if len(password) >= 16:
        score += 1
    return score


class ZeroTracePasswordValidator:
    def validate(self, password, user=None):
        username = getattr(user, "username", "") if user else ""
        email = getattr(user, "email", "") if user else ""
        full_name = getattr(user, "full_name", "") if user else ""
        problems = password_problems(password, username=username, email=email, full_name=full_name)
        if problems:
            raise ValidationError(problems)

    def get_help_text(self):
        return "Use at least 12 characters with upper and lower case letters, a number, and a symbol."
