"""
Email notification Celery task.
"""
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.notifications.send_email", bind=True, max_retries=3)
def send_email(self, to_email: str, subject: str, body: str, html_body: str = None):
    """Send an email via SMTP (async Celery task)."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from app.core.config import settings

        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP not configured. Skipping email send.")
            return {"status": "skipped", "reason": "smtp_not_configured"}

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email

        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email}: {subject}")
        return {"status": "sent", "to": to_email, "subject": subject}
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="app.tasks.notifications.create_in_app_notification")
def create_in_app_notification(
    org_id: str, user_id: str, title: str, message: str,
    notif_type: str = "info", link: str = None
):
    """Create an in-app notification for a user."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.models.models import Notification

    engine = create_engine(settings.DATABASE_URL_SYNC)
    with Session(engine) as session:
        notif = Notification(
            organization_id=org_id,
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            link=link,
        )
        session.add(notif)
        session.commit()
    return {"status": "created", "user_id": user_id}
