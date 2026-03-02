"""
Utilities for sending emails.
"""

import importlib
import logging
import os

from fastapi import FastAPI
from fastapi_mail import MessageSchema, MessageType, FastMail
from pydantic import NameEmail

from piggy.core.config import config
from piggy.core.i18n import _

logger = logging.getLogger(__name__)

HTML_CONTENT = """
<h2>{title}</h2>
<p>{body_text}</p>
<div class="button-container">
    <a href="{url}" class="button">{button_text}</a>
</div>
<p style="font-size: 12px; color: #7A7A7A;">{link_not_working}:<br>{url}</p>
"""


def _render_template(html_content: str) -> str:
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "assets", "templates", "email.html"
    )
    try:
        with open(template_path, "r", encoding="utf-8") as template_file:
            template = template_file.read()
            return template.replace("{{content}}", html_content)
    except Exception as error:  # pylint: disable=broad-except
        logger.error("Error loading email template: %s", error)
        return html_content


async def _send_email(subject: str, recipient: NameEmail, body: str) -> None:
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "piggy.svg")
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.html,
        from_email=f"{config.MAIL_FROM_NAME} <{config.MAIL_FROM}>",
        attachments=[
            {
                "file": logo_path,
                "headers": {
                    "Content-ID": "<piggy_logo>",
                    "Content-Disposition": "inline",
                },
                "mime_type": "image",
                "mime_subtype": "svg+xml",
            }
        ],
    )
    await FastMail(config.MAIL_CONFIG).send_message(message)


async def send_verification_email(
    name: str, email: str, baseurl: str, token: str
) -> bool:
    """Send a verification email to the given email address."""
    app_module = importlib.import_module("piggy")  # or your main module
    app: FastAPI = getattr(app_module, "app")
    try:
        verification_url = baseurl + app.url_path_for("verify_email", token=token)
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error generating verification URL: %s", e)
        return False
    subject = _("email.verification.subject")

    body = HTML_CONTENT.format(
        title=_("email.verification.title"),
        body_text=_("email.verification.body"),
        button_text=_("email.verification.button"),
        link_not_working=_("email.link_not_working"),
        url=verification_url,
    )
    try:
        await _send_email(
            subject, NameEmail(email=email, name=name), _render_template(body)
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error sending verification email: %s", e)
        return False
    return True


async def user_activated_email(name: str, email: str, baseurl: str) -> None:
    """Send an email to the user when an admin activated their account."""
    subject = _("email.activated.subject")
    body = HTML_CONTENT.format(
        title=_("email.activated.title"),
        body_text=_("email.activated.body"),
        button_text=_("email.activated.button"),
        link_not_working=_("email.link_not_working"),
        url=f"{baseurl}/settings",
    )
    try:
        await _send_email(
            subject, NameEmail(email=email, name=name), _render_template(body)
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error sending activation email: %s", e)


async def admin_new_user_email(
    name: str, email: str, user_name: str, baseurl: str
) -> None:
    """Send an email to the admin when a new user signs up."""
    subject = _("email.new_user.subject")
    body = HTML_CONTENT.format(
        title=_("email.new_user.title"),
        body_text=_("email.new_user.body").format(user_name=user_name),
        button_text=_("email.new_user.button"),
        link_not_working=_("email.link_not_working"),
        url=f"{baseurl}/settings",
    )
    try:
        await _send_email(
            subject, NameEmail(email=email, name=name), _render_template(body)
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error sending activation email: %s", e)
