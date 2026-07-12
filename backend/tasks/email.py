import logging
import urllib.request
from celery import shared_task
from django.conf import settings
from services.email import send_html_email, get_base_context

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 60}, name="tasks.email.send_welcome_email")
def send_welcome_email(self, user_id):
    from apps.users.models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("send_welcome_email: user %s not found", user_id)
        return
    context = {**get_base_context(), "user": user, "courses_url": f"{settings.FRONTEND_URL}/courses"}
    send_html_email("Welcome to T-Career", "emails/welcome.html", context, [user.email])


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 120}, name="tasks.email.send_certificate_email")
def send_certificate_email(self, certificate_id):
    from apps.certificates.models import Certificate
    try:
        cert = Certificate.objects.select_related("user", "course").get(id=certificate_id)
    except Certificate.DoesNotExist:
        logger.error("send_certificate_email: certificate %s not found", certificate_id)
        return
    context = {
        **get_base_context(),
        "user": cert.user,
        "course_title": cert.course.title,
        "cert_number": cert.cert_number,
        "verify_url": cert.verify_url,
        "pdf_url": cert.pdf_url,
    }
    attachments = []
    if cert.pdf_url and cert.pdf_url.startswith("https://"):
        try:
            with urllib.request.urlopen(cert.pdf_url, timeout=15) as r:
                pdf_data = r.read()
            attachments.append((f"certificate-{cert.cert_number}.pdf", pdf_data, "application/pdf"))
        except Exception as exc:
            logger.warning("Could not attach PDF for %s: %s", cert.cert_number, exc)
    send_html_email(f"Your certificate for {cert.course.title}", "emails/certificate.html", context, [cert.user.email], attachments or None)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 60}, name="tasks.email.send_password_reset_email")
def send_password_reset_email(self, user_id, reset_token):
    from apps.users.models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("send_password_reset_email: user %s not found", user_id)
        return
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    context = {**get_base_context(), "user": user, "reset_url": reset_url, "expiry_hours": 24}
    send_html_email("Reset your T-Career password", "emails/password_reset.html", context, [user.email])


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 60}, name="tasks.email.send_verification_email")
def send_verification_email(self, user_id, verification_token):
    from apps.users.models import User
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("send_verification_email: user %s not found", user_id)
        return
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    context = {**get_base_context(), "user": user, "verify_url": verify_url, "expiry_hours": 24}
    send_html_email("Verify your T-Career email address", "emails/verify_email.html", context, [user.email])
