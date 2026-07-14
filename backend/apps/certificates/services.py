import base64
import logging
import uuid
from io import BytesIO

import qrcode
from django.conf import settings
from django.template.loader import render_to_string

from apps.courses.models import Enrollment, EnrollmentStatus
from common.audit import AuditService
from common.exceptions import ConflictError, ServiceError
from common.storage import upload_to_s3

from .models import Certificate

logger = logging.getLogger(__name__)


def _generate_cert_number() -> str:
    """Generate a unique human-readable certificate number."""
    return f"TC-{uuid.uuid4().hex[:10].upper()}"


def _generate_qr_base64(url: str) -> str:
    """Generate a QR code image as base64 string for embedding in HTML."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


class CertificateService:
    @staticmethod
    def eligibility(enrollment: Enrollment) -> tuple[bool, list[str]]:
        reasons = []
        course = enrollment.course
        if course.status != "published" or course.deleted_at is not None:
            reasons.append("Course must be published before certificates can be issued.")
        published_lessons = course.lessons.filter(is_published=True, deleted_at=None)
        if not published_lessons.exists():
            reasons.append("Course must have published lessons before certificates can be issued.")
        completed_ids = set(
            enrollment.lesson_progress.filter(is_completed=True).values_list("lesson_id", flat=True)
        )
        incomplete = [
            lesson.title for lesson in published_lessons if lesson.id not in completed_ids
        ]
        if incomplete:
            reasons.append("All published lessons must be completed.")
        from apps.assessments.models import QuestionReviewStatus, QuizAttempt, QuizQuestion

        approved_questions = QuizQuestion.objects.filter(
            course=course,
            review_status=QuestionReviewStatus.APPROVED,
            is_certificate_eligible=True,
        )
        if approved_questions.count() < 5:
            reasons.append(
                "At least five approved certificate-eligible assessment questions are required."
            )
        if QuizQuestion.objects.filter(
            course=course,
            explanation__icontains="[REVIEW REQUIRED]",
        ).exists():
            reasons.append("Review-required assessment content cannot be used for certificates.")
        if not QuizAttempt.objects.filter(enrollment=enrollment, passed=True).exists():
            reasons.append(
                "Student must pass the approved course quiz before receiving a certificate."
            )
        if "requires-final-project" in (course.tags or []):
            reasons.append(
                "Final project completion must be verified before certificates can be issued."
            )
        return not reasons, reasons

    @staticmethod
    def generate(enrollment: Enrollment) -> Certificate:
        """
        Generate a certificate PDF for a completed enrollment.

        Checks:
        1. Enrollment must be COMPLETED status.
        2. Student must have passed the quiz.
        3. Certificate must not already exist.

        Generates:
        - Unique cert number
        - QR code pointing to the public verification URL
        - PDF rendered from HTML template
        - Uploads PDF to S3
        - Creates Certificate record in database
        """
        if enrollment.status != EnrollmentStatus.COMPLETED:
            raise ServiceError("Certificate can only be issued for completed enrollments.")

        eligible, reasons = CertificateService.eligibility(enrollment)
        if not eligible:
            raise ServiceError("Certificate eligibility failed: " + " ".join(reasons))

        # Check for existing certificate
        if Certificate.objects.filter(enrollment=enrollment).exists():
            raise ConflictError("A certificate has already been issued for this enrollment.")

        cert_number = _generate_cert_number()
        verify_url = f"{settings.FRONTEND_URL}/verify/{cert_number}"
        qr_base64 = _generate_qr_base64(verify_url)

        issued_date = (
            enrollment.completed_at.strftime("%B %d, %Y") if enrollment.completed_at else "N/A"
        )

        html_content = render_to_string(
            "certificates/certificate.html",
            {
                "student_name": enrollment.user.get_full_name(),
                "course_title": enrollment.course.title,
                "issued_date": issued_date,
                "cert_number": cert_number,
                "verify_url": verify_url,
                "qr_base64": qr_base64,
            },
        )

        pdf_url = CertificateService._render_and_upload(html_content, cert_number)

        certificate = Certificate.objects.create(
            user=enrollment.user,
            course=enrollment.course,
            enrollment=enrollment,
            cert_number=cert_number,
            pdf_url=pdf_url,
        )
        AuditService.record(
            actor=enrollment.user,
            action="certificate_issue",
            target=certificate,
            metadata={
                "course_id": str(enrollment.course_id),
                "cert_number": cert_number,
            },
        )

        logger.info(
            "Certificate issued: %s for user=%s course=%s",
            cert_number,
            enrollment.user.email,
            enrollment.course.title,
        )

        # Send completion email with certificate attached
        from tasks.email import send_certificate_email

        send_certificate_email.delay(str(certificate.id))

        return certificate

    @staticmethod
    def _render_and_upload(html_content: str, cert_number: str) -> str:
        """Render HTML to PDF and upload to S3. Returns the PDF URL."""
        try:
            from weasyprint import HTML

            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)

            s3_key = f"certificates/{cert_number}.pdf"
            pdf_url = upload_to_s3(
                pdf_buffer,
                s3_key,
                content_type="application/pdf",
            )
            return pdf_url

        except ImportError:
            # WeasyPrint not available in this environment.
            # Return a placeholder URL for development.
            logger.warning(
                "WeasyPrint not available. Certificate PDF not generated for %s.",
                cert_number,
            )
            return f"{settings.FRONTEND_URL}/verify/{cert_number}"

        except Exception as exc:
            logger.error("PDF generation failed for %s: %s", cert_number, exc)
            # Do not fail the certificate creation if PDF generation fails.
            # The certificate record still exists and can be re-rendered later.
            return ""

    @staticmethod
    def verify(cert_number: str) -> dict:
        """
        Verify a certificate by its cert number.
        Returns structured data for the public verification endpoint.
        """
        try:
            cert = Certificate.objects.select_related("user", "course").get(cert_number=cert_number)
        except Certificate.DoesNotExist:
            return {
                "valid": False,
                "reason": "Certificate not found.",
                "certificate": None,
            }

        if cert.is_revoked:
            return {
                "valid": False,
                "reason": cert.revoked_reason or "This certificate has been revoked.",
                "certificate": None,
            }

        return {
            "valid": True,
            "reason": "",
            "certificate": {
                "cert_number": cert.cert_number,
                "student_name": cert.user.get_full_name(),
                "course_title": cert.course.title,
                "issued_at": cert.issued_at.isoformat(),
                "pdf_url": cert.pdf_url,
            },
        }
