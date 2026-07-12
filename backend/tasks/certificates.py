import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    name="tasks.certificates.generate_certificate",
)
def generate_certificate(self, enrollment_id: str) -> None:
    """
    Generate a PDF certificate for a completed enrollment.
    Triggered automatically when a student passes the course quiz.
    """
    from apps.courses.models import Enrollment
    from apps.certificates.services import CertificateService
    from common.exceptions import ConflictError

    try:
        enrollment = Enrollment.objects.select_related(
            "user", "course"
        ).get(id=enrollment_id)
    except Enrollment.DoesNotExist:
        logger.error("Certificate generation failed: enrollment %s not found", enrollment_id)
        return

    try:
        certificate = CertificateService.generate(enrollment)
        logger.info(
            "Certificate generated: %s for enrollment %s",
            certificate.cert_number,
            enrollment_id,
        )
    except ConflictError:
        logger.info(
            "Certificate already exists for enrollment %s. Skipping.",
            enrollment_id,
        )
    except Exception as exc:
        logger.error(
            "Certificate generation failed for enrollment %s: %s",
            enrollment_id, exc,
        )
        raise
