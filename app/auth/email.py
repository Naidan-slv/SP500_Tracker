import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def build_verification_link(token: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/verify-email?token={token}"


def _smtp_configured() -> bool:
    return bool(
        settings.smtp_enabled
        and settings.smtp_host
        and settings.smtp_from_email
    )


def send_verification_email(recipient_email: str, verification_link: str) -> bool:
    if not _smtp_configured():
        logger.info(
            "SMTP not configured/enabled. Skipping verification email for %s. Link: %s",
            recipient_email,
            verification_link,
        )
        return False

    message = EmailMessage()
    message["Subject"] = "Verify your SP500 Tracker account"
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )
    message["To"] = recipient_email

    message.set_content(
        "Welcome to SP500 Tracker!\n\n"
        "Click the link below to verify your email address:\n"
        f"{verification_link}\n\n"
        "If you did not create this account, you can ignore this email."
    )

    if settings.smtp_use_ssl:
        smtp_client = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20)
    else:
        smtp_client = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)

    try:
        with smtp_client as server:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send verification email to %s", recipient_email)
        return False
