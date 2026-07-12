import logging
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_html_email(subject, template, context, to, attachments=None):
    try:
        html_content = render_to_string(template, context)
        msg = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to,
        )
        msg.content_subtype = "html"
        if attachments:
            for filename, content, mimetype in attachments:
                msg.attach(filename, content, mimetype)
        msg.send()
        logger.info("Email sent: subject=%s to=%s", subject, to)
        return True
    except Exception as exc:
        logger.error("Email send failed: subject=%s to=%s error=%s", subject, to, exc)
        return False


def get_base_context():
    return {
        "frontend_url": settings.FRONTEND_URL,
        "support_email": "support@tcareer.com",
    }
