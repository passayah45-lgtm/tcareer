"""
Certificate models for T-Career.

A certificate is issued when:
1. The student has completed all published lessons in a course.
2. The student has passed the course quiz.

Both conditions are checked in the certificate service before issuance.

The cert_number is a human-readable unique identifier used in QR codes
and public verification URLs. Format: TC-XXXXXXXXXX (10 hex chars uppercase).
This format is readable, memorable, and safe to expose publicly.
"""

from django.conf import settings
from django.db import models
from common.models import BaseModel


class Certificate(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
        db_index=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.PROTECT,
        related_name="certificates",
        db_index=True,
    )
    enrollment = models.OneToOneField(
        "courses.Enrollment",
        on_delete=models.PROTECT,
        related_name="certificate",
    )
    cert_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Public identifier. Format: TC-XXXXXXXXXX",
    )
    pdf_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="S3 URL of the generated PDF certificate.",
    )
    is_revoked = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Revoked certificates still exist but show as invalid on verification.",
    )
    revoked_reason = models.TextField(blank=True, default="")
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "certificates"
        indexes = [
            models.Index(fields=["user", "is_revoked"]),
            models.Index(fields=["cert_number"]),
        ]

    def __str__(self):
        return f"{self.cert_number} - {self.user.email} - {self.course.title}"

    @property
    def is_valid(self):
        return not self.is_revoked

    @property
    def verify_url(self):
        from django.conf import settings
        return f"{settings.FRONTEND_URL}/verify/{self.cert_number}"
