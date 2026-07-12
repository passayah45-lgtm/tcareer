from django.conf import settings
from django.db import models
from common.models import BaseModel


class TrustSubjectType(models.TextChoices):
    INSTRUCTOR = "instructor", "Instructor"
    RECRUITER = "recruiter", "Recruiter"
    ORGANIZATION = "organization", "Organization"
    LEARNER = "learner", "Learner"


class TrustChangeReason(models.TextChoices):
    EMAIL_VERIFIED = "email_verified", "Email Verified"
    PROFILE_COMPLETE = "profile_complete", "Profile Complete"
    IDENTITY_SUBMITTED = "identity_submitted", "Identity Document Submitted"
    IDENTITY_VERIFIED = "identity_verified", "Identity Verified"
    TEACHING_DEMO_SUBMITTED = "teaching_demo_submitted", "Teaching Demo Submitted"
    TEACHING_DEMO_APPROVED = "teaching_demo_approved", "Teaching Demo Approved"
    FIRST_COURSE_PUBLISHED = "first_course_published", "First Course Published"
    RATING_ABOVE_4 = "rating_above_4", "Rating Above 4.0"
    COMPANY_VERIFIED = "company_verified", "Company Verified"
    COMPANY_EMAIL_VERIFIED = "company_email_verified", "Company Email Verified"
    REGISTRATION_SUBMITTED = "registration_submitted", "Registration Document Submitted"
    WEBSITE_VERIFIED = "website_verified", "Website Verified"
    ENTERPRISE_LEVEL = "enterprise_level", "Enterprise Level Granted"
    FIRST_JOB_POSTED = "first_job_posted", "First Job Posted"
    FIRST_CERTIFICATE = "first_certificate", "First Certificate Earned"
    PORTFOLIO_COMPLETE = "portfolio_complete", "Portfolio Has 2+ Projects"
    RESUME_CREATED = "resume_created", "Resume Created"
    COMPLAINT_RECEIVED = "complaint_received", "Complaint Received"
    SUSPENDED = "suspended", "Account Suspended"
    MANUAL_ADJUSTMENT = "manual_adjustment", "Manual Adjustment by Staff"
    SUSPICIOUS_ACTIVITY = "suspicious_activity", "Suspicious Activity Detected"


class TrustScoreLog(BaseModel):
    # Append-only log of every trust score change.
    # The current score on each profile is the result of applying all log
    # entries in order. This makes the score fully auditable and reversible.

    subject_type = models.CharField(
        max_length=30,
        choices=TrustSubjectType.choices,
        db_index=True,
    )
    subject_id = models.UUIDField(db_index=True)
    previous_score = models.SmallIntegerField()
    new_score = models.SmallIntegerField()
    change_value = models.SmallIntegerField(help_text="Positive or negative change applied.")
    change_reason = models.CharField(
        max_length=50,
        choices=TrustChangeReason.choices,
        db_index=True,
    )
    calculated_by = models.CharField(
        max_length=20,
        default="system",
        help_text="system or staff",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trust_adjustments",
        help_text="Null when calculated by the system.",
    )
    notes = models.TextField(blank=True, default="")
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trust_score_logs"
        ordering = ["-performed_at"]
        indexes = [
            models.Index(fields=["subject_type", "subject_id"]),
            models.Index(fields=["change_reason"]),
            models.Index(fields=["performed_at"]),
        ]

    def save(self, *args, **kwargs):
        # Enforce append-only: prevent updates to existing rows.
        if not self._state.adding:
            raise ValueError("TrustScoreLog records are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject_type}:{self.subject_id} {self.change_value:+d} ({self.change_reason})"