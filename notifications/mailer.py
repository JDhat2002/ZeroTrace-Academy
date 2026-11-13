from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send_branded(to, subject, text, html):
    if not to:
        return
    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    message.attach_alternative(html, "text/html")
    message.send(fail_silently=False)


def _wrap(heading, paragraphs, link=None, link_label=None):
    body = "\n\n".join(paragraphs)
    if link:
        body = f"{body}\n\n{link_label or 'Open'}: {link}"
    body += "\n\nZeroTrace Academy\nFrom learner to cybersecurity professional.\n"
    html_parts = "".join(f"<p style=\"margin:0 0 12px;color:#d7ddd8;line-height:1.5\">{paragraph}</p>" for paragraph in paragraphs)
    button = ""
    if link:
        button = (
            f"<p style=\"margin:20px 0\"><a href=\"{link}\" "
            "style=\"background:#00ff75;color:#04140c;text-decoration:none;"
            "padding:12px 16px;border-radius:10px;font-weight:700\">"
            f"{link_label or 'Continue'}</a></p>"
        )
    html = f"""<!DOCTYPE html><html><body style="margin:0;background:#050807;font-family:Segoe UI,sans-serif">
      <div style="max-width:560px;margin:0 auto;padding:32px 20px">
        <p style="color:#00ff75;letter-spacing:.14em;font-size:12px">ZEROTRACE ACADEMY</p>
        <h1 style="color:#f5f7f5;font-size:24px">{heading}</h1>
        {html_parts}
        {button}
        <p style="color:#707a73;font-size:12px">This message does not contain your password.</p>
      </div>
    </body></html>"""
    return body, html


def send_verification(user, link):
    text, html = _wrap(
        "Verify your email address",
        [
            f"Hello {user.full_name},",
            "Confirm this address to activate your ZeroTrace account. The link expires in 24 hours and works once.",
            "If you did not create an account, you can ignore this message.",
        ],
        link,
        "Verify email",
    )
    send_branded(user.email, "Verify your ZeroTrace email", text, html)


def send_existing_account(user):
    text, html = _wrap(
        "A registration was attempted",
        [
            f"Hello {user.full_name},",
            "Someone tried to create a ZeroTrace account with this email address. The existing account was left unchanged.",
            "If this was not you, you can reset your password from the sign-in page.",
        ],
    )
    send_branded(user.email, "ZeroTrace account notice", text, html)


def send_welcome(user):
    text, html = _wrap(
        "Welcome to ZeroTrace",
        [
            f"Hello {user.full_name},",
            "Your email is verified. Your membership is Free until a paid plan exists. Labs and tools stay labelled as previews until they launch.",
        ],
    )
    send_branded(user.email, "Welcome to ZeroTrace Academy", text, html)


def send_password_reset(user, link):
    text, html = _wrap(
        "Reset your password",
        [
            f"Hello {user.full_name},",
            "This reset link expires in 30 minutes and works once. If you did not ask for it, ignore this message.",
        ],
        link,
        "Choose a new password",
    )
    send_branded(user.email, "Reset your ZeroTrace password", text, html)


def send_password_changed(user):
    text, html = _wrap(
        "Your password was changed",
        [
            f"Hello {user.full_name},",
            "The password on your ZeroTrace account was just changed. If you did not do this, reset it and review your sessions.",
        ],
    )
    send_branded(user.email, "Your ZeroTrace password changed", text, html)


def send_new_login(user, ip_address):
    where = ip_address or "an unknown address"
    text, html = _wrap(
        "New sign-in",
        [
            f"Hello {user.full_name},",
            f"Your account was used from {where}. If this was not you, change your password and sign out of other sessions.",
        ],
    )
    send_branded(user.email, "New sign-in to ZeroTrace", text, html)


def send_mfa_enabled(user):
    text, html = _wrap(
        "Two-factor authentication is on",
        [
            f"Hello {user.full_name},",
            "An authenticator app is now required at sign-in. Recovery codes were shown once in your account and are not included here.",
        ],
    )
    send_branded(user.email, "Two-factor authentication enabled", text, html)


def send_mfa_disabled(user):
    text, html = _wrap(
        "Two-factor authentication is off",
        [
            f"Hello {user.full_name},",
            "Two-factor authentication was turned off. If you did not do this, reset your password.",
        ],
    )
    send_branded(user.email, "Two-factor authentication disabled", text, html)


def send_security_alert(user, summary):
    text, html = _wrap(
        "Account security alert",
        [f"Hello {user.full_name},", summary],
    )
    send_branded(user.email, "ZeroTrace security alert", text, html)
