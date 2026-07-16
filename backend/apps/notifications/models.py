"""
Notification models for T-Career.

Design decisions:

1. Single polymorphic Notification table rather than separate tables per type.
   The notification_type field determines which payload keys are present.
   This keeps queries simple: one table, one index, one API endpoint.

2. action_url is stored as a relative path (e.g. /dashboard, /quiz/uuid).
   The frontend constructs the full URL. This makes the model environment-agnostic.

3. payload is a JSON field for type-specific data.
   For quiz_passed: { "course_title": "Python Fundamentals", "score": 85 }
   For certificate_issued: { "cert_number": "TC-ABCD1234", "course_title": "..." }
   For discussion_reply: { "thread_title": "...", "lesson_title": "..." }

4. Notifications are never hard deleted.
   Old read notifications are archived (read=True) and hidden from the bell.
   This preserves history without blocking the UI.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils.crypto import constant_time_compare, get_random_string
from django.utils import timezone
import hashlib
import logging
from common.models import BaseModel

logger = logging.getLogger("tcareer.email")


class NotificationType(models.TextChoices):
    QUIZ_PASSED = "quiz_passed", "Quiz Passed"
    CERTIFICATE_ISSUED = "certificate_issued", "Certificate Issued"
    TRACK_STAGE_ADVANCED = "track_stage_advanced", "Track Stage Advanced"
    DISCUSSION_REPLY = "discussion_reply", "Discussion Reply"
    NEW_JOB_MATCH = "new_job_match", "New Job Match"
    WELCOME = "welcome", "Welcome"
    APPLICATION_RECEIVED = "application_received", "Application Received"
    APPLICATION_STAGE_CHANGED = "application_stage_changed", "Application Stage Changed"
    INTERVIEW_SCHEDULED = "interview_scheduled", "Interview Scheduled"
    INTERVIEW_UPDATED = "interview_updated", "Interview Updated"
    OFFER_SENT = "offer_sent", "Offer Sent"
    OFFER_ACCEPTED = "offer_accepted", "Offer Accepted"
    OFFER_DECLINED = "offer_declined", "Offer Declined"
    RECRUITER_INVITED = "recruiter_invited", "Recruiter Invited"
    ORGANIZATION_INVITATION_ACCEPTED = (
        "organization_invitation_accepted",
        "Organization Invitation Accepted",
    )
    ACADEMIC_REVIEW_ASSIGNED = "academic_review_assigned", "Academic Review Assigned"
    ACADEMIC_REVIEW_DUE_SOON = "academic_review_due_soon", "Academic Review Due Soon"
    ACADEMIC_REVIEW_OVERDUE = "academic_review_overdue", "Academic Review Overdue"
    ACADEMIC_CHANGES_REQUESTED = "academic_changes_requested", "Academic Changes Requested"
    ACADEMIC_INSTRUCTOR_RESPONDED = "academic_instructor_responded", "Academic Instructor Responded"
    ACADEMIC_CONTENT_RESUBMITTED = "academic_content_resubmitted", "Academic Content Resubmitted"
    ACADEMIC_CONTENT_APPROVED = "academic_content_approved", "Academic Content Approved"
    ACADEMIC_CONTENT_REJECTED = "academic_content_rejected", "Academic Content Rejected"
    PUBLICATION_BLOCKED = "publication_blocked", "Publication Blocked"


class NotificationCategory(models.TextChoices):
    JOB_ALERTS = "job_alerts", "Job Alerts"
    APPLICATIONS = "applications", "Applications"
    INTERVIEWS = "interviews", "Interviews"
    OFFERS = "offers", "Offers"
    ORGANIZATION_INVITES = "organization_invites", "Organization Invites"
    RECRUITER_INVITES = "recruiter_invites", "Recruiter Invites"
    COURSE_UPDATES = "course_updates", "Course Updates"
    CERTIFICATES = "certificates", "Certificates"
    MARKETING = "marketing", "Marketing"
    SECURITY = "security", "Security"


NOTIFICATION_CATEGORY_BY_TYPE = {
    NotificationType.QUIZ_PASSED: NotificationCategory.COURSE_UPDATES,
    NotificationType.CERTIFICATE_ISSUED: NotificationCategory.CERTIFICATES,
    NotificationType.TRACK_STAGE_ADVANCED: NotificationCategory.COURSE_UPDATES,
    NotificationType.DISCUSSION_REPLY: NotificationCategory.COURSE_UPDATES,
    NotificationType.NEW_JOB_MATCH: NotificationCategory.JOB_ALERTS,
    NotificationType.WELCOME: NotificationCategory.SECURITY,
    NotificationType.APPLICATION_RECEIVED: NotificationCategory.APPLICATIONS,
    NotificationType.APPLICATION_STAGE_CHANGED: NotificationCategory.APPLICATIONS,
    NotificationType.INTERVIEW_SCHEDULED: NotificationCategory.INTERVIEWS,
    NotificationType.INTERVIEW_UPDATED: NotificationCategory.INTERVIEWS,
    NotificationType.OFFER_SENT: NotificationCategory.OFFERS,
    NotificationType.OFFER_ACCEPTED: NotificationCategory.OFFERS,
    NotificationType.OFFER_DECLINED: NotificationCategory.OFFERS,
    NotificationType.RECRUITER_INVITED: NotificationCategory.RECRUITER_INVITES,
    NotificationType.ORGANIZATION_INVITATION_ACCEPTED: NotificationCategory.ORGANIZATION_INVITES,
    NotificationType.ACADEMIC_REVIEW_ASSIGNED: NotificationCategory.COURSE_UPDATES,
    NotificationType.ACADEMIC_REVIEW_DUE_SOON: NotificationCategory.COURSE_UPDATES,
    NotificationType.ACADEMIC_REVIEW_OVERDUE: NotificationCategory.COURSE_UPDATES,
    NotificationType.ACADEMIC_CHANGES_REQUESTED: NotificationCategory.COURSE_UPDATES,
    NotificationType.ACADEMIC_INSTRUCTOR_RESPONDED: NotificationCategory.COURSE_UPDATES,
    NotificationType.ACADEMIC_CONTENT_RESUBMITTED: NotificationCategory.COURSE_UPDATES,
    NotificationType.ACADEMIC_CONTENT_APPROVED: NotificationCategory.COURSE_UPDATES,
    NotificationType.ACADEMIC_CONTENT_REJECTED: NotificationCategory.COURSE_UPDATES,
    NotificationType.PUBLICATION_BLOCKED: NotificationCategory.SECURITY,
}


class Notification(BaseModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True,
    )
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=500)
    action_url = models.CharField(
        max_length=300,
        blank=True,
        default="",
        help_text="Relative URL the user is taken to when they click the notification.",
    )
    payload = models.JSONField(
        default=dict,
        help_text="Type-specific data for rendering the notification.",
    )
    category = models.CharField(
        max_length=40,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SECURITY,
        db_index=True,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
        ]

    def __str__(self):
        return f"{self.recipient.email} - {self.notification_type}: {self.title}"

    def mark_read(self):
        if not self.is_read:
            from django.utils import timezone

            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    category = models.CharField(max_length=40, choices=NotificationCategory.choices, db_index=True)
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_preferences"
        unique_together = [("user", "category")]
        indexes = [
            models.Index(fields=["user", "category"], name="notif_pref_user_category_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.category == NotificationCategory.SECURITY:
            self.in_app_enabled = True
            self.email_enabled = True
        super().save(*args, **kwargs)


class EmailSuppression(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_suppressions",
        null=True,
        blank=True,
    )
    email = models.EmailField(db_index=True)
    category = models.CharField(
        max_length=40, choices=NotificationCategory.choices, blank=True, default="", db_index=True
    )
    reason = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "email_suppressions"
        indexes = [
            models.Index(
                fields=["email", "category", "is_active"], name="email_suppression_lookup_idx"
            ),
        ]


class NotificationUnsubscribeToken(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_unsubscribe_tokens",
    )
    email = models.EmailField(db_index=True)
    category = models.CharField(max_length=40, choices=NotificationCategory.choices)
    token_hash = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification_unsubscribe_tokens"
        indexes = [
            models.Index(
                fields=["email", "category", "expires_at"], name="notif_unsub_email_cat_idx"
            ),
        ]

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def create_token(
        cls, user, category: str, expires_at=None
    ) -> tuple["NotificationUnsubscribeToken", str]:
        token = get_random_string(48)
        instance = cls.objects.create(
            user=user,
            email=user.email,
            category=category,
            token_hash=cls.hash_token(token),
            expires_at=expires_at or timezone.now() + timezone.timedelta(days=30),
        )
        return instance, token

    @classmethod
    def validate_token(cls, token: str):
        token_hash = cls.hash_token(token)
        candidate = cls.objects.filter(
            token_hash=token_hash, used_at__isnull=True, expires_at__gt=timezone.now()
        ).first()
        if candidate and constant_time_compare(candidate.token_hash, token_hash):
            return candidate
        return None


class EmailDeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    QUEUED = "queued", "Queued"
    SENT = "sent", "Sent"
    SKIPPED = "skipped", "Skipped"
    FAILED = "failed", "Failed"
    RETRYING = "retrying", "Retrying"
    CANCELLED = "cancelled", "Cancelled"


class EmailDelivery(BaseModel):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="email_deliveries",
        null=True,
        blank=True,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_deliveries",
    )
    recipient_email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    body_html = models.TextField(blank=True, default="")
    template_key = models.CharField(max_length=100, db_index=True)
    category = models.CharField(
        max_length=40,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SECURITY,
        db_index=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.PENDING,
        db_index=True,
    )
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    provider_message_id = models.CharField(max_length=255, blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "email_deliveries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status"], name="email_delivery_recipient_idx"),
            models.Index(fields=["template_key", "status"], name="email_delivery_template_idx"),
        ]

    def mark_failed(self, error: str) -> "EmailDelivery":
        self.status = EmailDeliveryStatus.FAILED
        self.last_error = error[:2000]
        self.failed_at = timezone.now()
        self.save(update_fields=["status", "last_error", "failed_at", "updated_at"])
        return self

    def mark_sent(self, provider_message_id: str = "") -> "EmailDelivery":
        self.status = EmailDeliveryStatus.SENT
        self.sent_at = timezone.now()
        self.failed_at = None
        self.last_error = ""
        self.provider_message_id = provider_message_id
        self.save(
            update_fields=[
                "status",
                "sent_at",
                "failed_at",
                "last_error",
                "provider_message_id",
                "updated_at",
            ]
        )
        return self


EMAIL_READY_NOTIFICATION_TYPES = {
    NotificationType.NEW_JOB_MATCH,
    NotificationType.INTERVIEW_SCHEDULED,
    NotificationType.INTERVIEW_UPDATED,
    NotificationType.APPLICATION_STAGE_CHANGED,
    NotificationType.OFFER_SENT,
    NotificationType.OFFER_ACCEPTED,
    NotificationType.OFFER_DECLINED,
    NotificationType.RECRUITER_INVITED,
    NotificationType.ORGANIZATION_INVITATION_ACCEPTED,
}


EMAIL_TEMPLATE_BY_NOTIFICATION_TYPE = {
    NotificationType.NEW_JOB_MATCH: "job_alert_match",
    NotificationType.INTERVIEW_SCHEDULED: "interview_scheduled",
    NotificationType.INTERVIEW_UPDATED: "interview_updated",
    NotificationType.APPLICATION_STAGE_CHANGED: "application_status_changed",
    NotificationType.OFFER_SENT: "offer_received",
    NotificationType.OFFER_ACCEPTED: "offer_received",
    NotificationType.OFFER_DECLINED: "offer_received",
    NotificationType.RECRUITER_INVITED: "recruiter_invitation",
    NotificationType.ORGANIZATION_INVITATION_ACCEPTED: "organization_invitation",
}


EMAIL_TEMPLATES = {
    "job_alert_match": {
        "subject": "New jobs match your alert",
        "body": "Hi {recipient_name},\n\nWe found jobs that match your alert: {title}.\n\nOpen T-Career to review the matches.",
        "html": "<h1>New jobs match your alert</h1><p>Hi {recipient_name},</p><p>We found jobs that match your alert: <strong>{title}</strong>.</p><p>Open T-Career to review the matches.</p>",
    },
    "interview_scheduled": {
        "subject": "Interview scheduled",
        "body": "Hi {recipient_name},\n\nYour interview has been scheduled. Details: {body}\n\nPlease check T-Career for the latest information.",
        "html": "<h1>Interview scheduled</h1><p>Hi {recipient_name},</p><p>{body}</p><p>Please check T-Career for the latest information.</p>",
    },
    "interview_updated": {
        "subject": "Interview updated",
        "body": "Hi {recipient_name},\n\nYour interview details changed. Details: {body}\n\nPlease check T-Career for the latest information.",
        "html": "<h1>Interview updated</h1><p>Hi {recipient_name},</p><p>{body}</p><p>Please check T-Career for the latest information.</p>",
    },
    "application_status_changed": {
        "subject": "Application status updated",
        "body": "Hi {recipient_name},\n\nYour application status changed: {body}\n\nYou can view the full timeline in T-Career.",
        "html": "<h1>Application status updated</h1><p>Hi {recipient_name},</p><p>{body}</p><p>You can view the full timeline in T-Career.</p>",
    },
    "offer_received": {
        "subject": "Offer update",
        "body": "Hi {recipient_name},\n\nYou have an offer update: {body}\n\nOpen T-Career to review the next steps.",
        "html": "<h1>Offer update</h1><p>Hi {recipient_name},</p><p>{body}</p><p>Open T-Career to review the next steps.</p>",
    },
    "organization_invitation": {
        "subject": "Organization invitation update",
        "body": "Hi {recipient_name},\n\n{body}\n\nOpen T-Career to continue.",
        "html": "<h1>Organization invitation</h1><p>Hi {recipient_name},</p><p>{body}</p><p>Open T-Career to continue.</p>",
    },
    "recruiter_invitation": {
        "subject": "Recruiter invitation",
        "body": "Hi {recipient_name},\n\n{body}\n\nOpen T-Career to accept the invitation.",
        "html": "<h1>Recruiter invitation</h1><p>Hi {recipient_name},</p><p>{body}</p><p>Open T-Career to accept the invitation.</p>",
    },
    "certificate_earned": {
        "subject": "Certificate earned",
        "body": "Hi {recipient_name},\n\nYour certificate is ready: {body}\n\nOpen T-Career to download or share it.",
        "html": "<h1>Certificate earned</h1><p>Hi {recipient_name},</p><p>{body}</p><p>Open T-Career to download or share it.</p>",
    },
    "security_notification": {
        "subject": "Security notification",
        "body": "Hi {recipient_name},\n\n{body}\n\nIf this was not you, review your T-Career account immediately.",
        "html": "<h1>Security notification</h1><p>Hi {recipient_name},</p><p>{body}</p><p>If this was not you, review your T-Career account immediately.</p>",
    },
}


class SafeTemplateDict(dict):
    def __missing__(self, key):
        return ""


class EmailDeliveryService:
    PROCESSABLE_STATUSES = {
        EmailDeliveryStatus.PENDING,
        EmailDeliveryStatus.QUEUED,
    }
    SENDABLE_STATUSES = PROCESSABLE_STATUSES | {EmailDeliveryStatus.FAILED}

    @staticmethod
    def smtp_configured() -> bool:
        backend = getattr(settings, "EMAIL_BACKEND", "")
        if "console" in backend:
            return False
        if "locmem" in backend:
            return True
        return bool(
            getattr(settings, "EMAIL_HOST", "") and getattr(settings, "DEFAULT_FROM_EMAIL", "")
        )

    @staticmethod
    def render_template(
        template_key: str, notification: Notification, metadata: dict | None = None
    ) -> tuple[str, str, str]:
        payload = notification.payload or {}
        context = SafeTemplateDict(
            {
                "recipient_name": notification.recipient.get_full_name()
                or notification.recipient.email,
                "title": notification.title,
                "body": notification.body,
                **payload,
                **(metadata or {}),
            }
        )
        template = EMAIL_TEMPLATES.get(template_key)
        if not template:
            return (
                payload.get("email_subject") or notification.title,
                payload.get("email_body") or notification.body,
                "",
            )
        html = EmailDeliveryService.wrap_html_template(template.get("html", "").format_map(context))
        return template["subject"].format_map(context), template["body"].format_map(context), html

    @staticmethod
    def wrap_html_template(content: str) -> str:
        if not content:
            return ""
        return (
            '<!doctype html><html><body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">'
            '<div style="max-width:640px;margin:0 auto;padding:24px;">'
            '<div style="font-weight:700;font-size:20px;color:#2563eb;margin-bottom:20px;">T-Career</div>'
            f'<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:24px;line-height:1.6;">{content}</div>'
            '<p style="font-size:12px;color:#64748b;margin-top:16px;">You are receiving this because of your T-Career account activity.</p>'
            "</div></body></html>"
        )

    @staticmethod
    def category_for_notification(notification: Notification) -> str:
        payload = notification.payload or {}
        return (
            payload.get("category")
            or notification.category
            or NOTIFICATION_CATEGORY_BY_TYPE.get(
                notification.notification_type,
                NotificationCategory.SECURITY,
            )
        )

    @staticmethod
    def preference_allows_email(user, category: str) -> bool:
        if category == NotificationCategory.SECURITY:
            return True
        pref, _ = NotificationPreference.objects.get_or_create(user=user, category=category)
        return pref.email_enabled

    @staticmethod
    def is_suppressed(user, email: str, category: str) -> bool:
        if category == NotificationCategory.SECURITY:
            return False
        return EmailSuppression.objects.filter(
            models.Q(user=user) | models.Q(email__iexact=email),
            models.Q(category="") | models.Q(category=category),
            is_active=True,
        ).exists()

    @staticmethod
    def create_for_notification(
        notification: Notification, template_key: str = "", metadata: dict | None = None
    ) -> EmailDelivery:
        payload = notification.payload or {}
        template_key = (
            template_key
            or payload.get("template_key")
            or EMAIL_TEMPLATE_BY_NOTIFICATION_TYPE.get(
                notification.notification_type,
                notification.notification_type,
            )
        )
        category = EmailDeliveryService.category_for_notification(notification)
        subject, body, body_html = EmailDeliveryService.render_template(
            template_key, notification, metadata
        )
        status = EmailDeliveryStatus.PENDING
        last_error = ""
        if not EmailDeliveryService.preference_allows_email(notification.recipient, category):
            status = EmailDeliveryStatus.CANCELLED
            last_error = "Email disabled by notification preferences."
        elif EmailDeliveryService.is_suppressed(
            notification.recipient, notification.recipient.email, category
        ):
            status = EmailDeliveryStatus.CANCELLED
            last_error = "Email suppressed for this recipient/category."
        delivery_metadata = {**payload, **(metadata or {})}
        delivery_metadata.setdefault(
            "idempotency_key",
            f"notification:{notification.id}:template:{template_key}:recipient:{notification.recipient_id}",
        )
        delivery = EmailDelivery.objects.create(
            notification=notification,
            recipient=notification.recipient,
            recipient_email=notification.recipient.email,
            subject=subject,
            body=body,
            body_html=body_html,
            template_key=template_key,
            category=category,
            metadata=delivery_metadata,
            status=status,
            last_error=last_error,
        )
        return delivery

    @staticmethod
    def mark_failed(delivery: EmailDelivery, error: str) -> EmailDelivery:
        return delivery.mark_failed(error)

    @staticmethod
    def mark_sent(delivery: EmailDelivery, provider_message_id: str = "") -> EmailDelivery:
        return delivery.mark_sent(provider_message_id)

    @staticmethod
    def send_email_delivery(delivery_id, dry_run: bool = False) -> EmailDelivery:
        with transaction.atomic():
            delivery = (
                EmailDelivery.objects.select_for_update()
                .select_related("recipient")
                .get(id=delivery_id)
            )
            if delivery.status == EmailDeliveryStatus.SENT:
                return delivery
            if delivery.status == EmailDeliveryStatus.CANCELLED:
                return delivery
            if delivery.status == EmailDeliveryStatus.RETRYING:
                processing_timeout = timezone.timedelta(
                    seconds=getattr(settings, "EMAIL_DELIVERY_PROCESSING_TIMEOUT_SECONDS", 900)
                )
                if (
                    delivery.updated_at
                    and delivery.updated_at > timezone.now() - processing_timeout
                ):
                    logger.info(
                        "email_delivery_already_processing", extra={"delivery_id": str(delivery.id)}
                    )
                    return delivery
            elif delivery.status not in EmailDeliveryService.SENDABLE_STATUSES:
                return delivery
            if dry_run:
                return delivery
            idempotency_key = (delivery.metadata or {}).get("idempotency_key")
            if (
                idempotency_key
                and EmailDelivery.objects.filter(
                    metadata__idempotency_key=idempotency_key,
                    status=EmailDeliveryStatus.SENT,
                )
                .exclude(id=delivery.id)
                .exists()
            ):
                delivery.status = EmailDeliveryStatus.CANCELLED
                delivery.last_error = "Duplicate delivery idempotency key already sent."
                delivery.save(update_fields=["status", "last_error", "updated_at"])
                logger.info(
                    "email_delivery_cancelled_duplicate",
                    extra={"delivery_id": str(delivery.id), "idempotency_key": idempotency_key},
                )
                return delivery
            if not delivery.recipient.is_active:
                delivery.status = EmailDeliveryStatus.CANCELLED
                delivery.last_error = "Recipient account is inactive."
                delivery.save(update_fields=["status", "last_error", "updated_at"])
                logger.info(
                    "email_delivery_cancelled_inactive_account",
                    extra={"delivery_id": str(delivery.id)},
                )
                return delivery
            if not EmailDeliveryService.preference_allows_email(
                delivery.recipient, delivery.category
            ):
                delivery.status = EmailDeliveryStatus.CANCELLED
                delivery.last_error = "Email disabled by notification preferences."
                delivery.save(update_fields=["status", "last_error", "updated_at"])
                logger.info(
                    "email_delivery_cancelled_preferences",
                    extra={"delivery_id": str(delivery.id), "category": delivery.category},
                )
                return delivery
            if EmailDeliveryService.is_suppressed(
                delivery.recipient, delivery.recipient_email, delivery.category
            ):
                delivery.status = EmailDeliveryStatus.CANCELLED
                delivery.last_error = "Email suppressed for this recipient/category."
                delivery.save(update_fields=["status", "last_error", "updated_at"])
                logger.info(
                    "email_delivery_cancelled_suppression",
                    extra={"delivery_id": str(delivery.id), "category": delivery.category},
                )
                return delivery
            metadata = delivery.metadata or {}
            metadata.setdefault("idempotency_key", f"delivery:{delivery.id}")
            metadata["processing_started_at"] = timezone.now().isoformat()
            delivery.status = EmailDeliveryStatus.RETRYING
            delivery.metadata = metadata
            delivery.save(update_fields=["status", "metadata", "updated_at"])

        if delivery.status == EmailDeliveryStatus.SENT:
            return delivery
        if delivery.status == EmailDeliveryStatus.CANCELLED:
            return delivery
        max_retries = getattr(settings, "EMAIL_DELIVERY_MAX_RETRIES", 3)
        if delivery.retry_count >= max_retries:
            return delivery.mark_failed("Retry limit reached.")
        if not EmailDeliveryService.smtp_configured():
            delivery.retry_count += 1
            delivery.status = EmailDeliveryStatus.FAILED
            delivery.last_error = "SMTP is not configured; delivery was not sent."
            delivery.failed_at = timezone.now()
            delivery.save(
                update_fields=["retry_count", "status", "last_error", "failed_at", "updated_at"]
            )
            logger.warning(
                "email_delivery_failed_missing_smtp", extra={"delivery_id": str(delivery.id)}
            )
            return delivery
        try:
            send_mail(
                subject=delivery.subject,
                message=delivery.body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", ""),
                recipient_list=[delivery.recipient_email],
                html_message=delivery.body_html or None,
                fail_silently=False,
            )
        except Exception as exc:
            delivery.retry_count += 1
            delivery.status = (
                EmailDeliveryStatus.RETRYING
                if delivery.retry_count < max_retries
                else EmailDeliveryStatus.FAILED
            )
            delivery.last_error = str(exc)[:2000]
            delivery.failed_at = (
                timezone.now() if delivery.status == EmailDeliveryStatus.FAILED else None
            )
            delivery.save(
                update_fields=["retry_count", "status", "last_error", "failed_at", "updated_at"]
            )
            logger.warning(
                "email_delivery_send_failed",
                extra={"delivery_id": str(delivery.id), "error": str(exc)[:200]},
            )
            return delivery
        sent = delivery.mark_sent()
        logger.info(
            "email_delivery_sent",
            extra={"delivery_id": str(delivery.id), "category": delivery.category},
        )
        return sent

    @staticmethod
    def bulk_process_pending(limit: int = 50, dry_run: bool = False) -> list[EmailDelivery]:
        deliveries = list(
            EmailDelivery.objects.filter(
                status__in=EmailDeliveryService.PROCESSABLE_STATUSES
            ).order_by("created_at")[:limit]
        )
        return [
            EmailDeliveryService.send_email_delivery(delivery.id, dry_run=dry_run)
            for delivery in deliveries
        ]

    @staticmethod
    def retry_failed(limit: int = 50, dry_run: bool = False) -> list[EmailDelivery]:
        deliveries = list(
            EmailDelivery.objects.filter(status=EmailDeliveryStatus.FAILED).order_by("created_at")[
                :limit
            ]
        )
        if dry_run:
            return deliveries
        processed = []
        for delivery in deliveries:
            processed.append(EmailDeliveryService.send_email_delivery(delivery.id))
        return processed


class EmailProviderWebhookService:
    HIGH_RISK_EVENTS = {"bounced", "complained"}
    VALID_EVENTS = {"delivered", "bounced", "complained", "opened", "clicked", "failed"}

    @staticmethod
    def _event_id(payload: dict) -> str:
        return str(payload.get("event_id") or payload.get("id") or payload.get("message_id") or "")

    @staticmethod
    def find_delivery(payload: dict):
        delivery_id = payload.get("delivery_id")
        provider_message_id = payload.get("provider_message_id") or payload.get("message_id")
        idempotency_key = payload.get("idempotency_key")
        queryset = EmailDelivery.objects.select_related("recipient")
        if delivery_id:
            return queryset.filter(id=delivery_id).first()
        if provider_message_id:
            return queryset.filter(provider_message_id=provider_message_id).first()
        if idempotency_key:
            return queryset.filter(metadata__idempotency_key=idempotency_key).first()
        return None

    @staticmethod
    @transaction.atomic
    def process_event(payload: dict) -> tuple[EmailDelivery | None, bool]:
        event_type = str(payload.get("event") or payload.get("type") or "").lower()
        if event_type not in EmailProviderWebhookService.VALID_EVENTS:
            raise ValueError("Unsupported email provider event.")
        delivery = EmailProviderWebhookService.find_delivery(payload)
        if delivery is None:
            return None, False

        delivery = (
            EmailDelivery.objects.select_for_update()
            .select_related("recipient")
            .get(id=delivery.id)
        )
        metadata = delivery.metadata or {}
        events = metadata.setdefault("provider_events", [])
        event_id = EmailProviderWebhookService._event_id(payload)
        if event_id and any(item.get("event_id") == event_id for item in events):
            return delivery, False

        events.append(
            {
                "event_id": event_id,
                "event": event_type,
                "received_at": timezone.now().isoformat(),
                "provider_message_id": payload.get("provider_message_id")
                or payload.get("message_id")
                or "",
                "metadata": payload.get("metadata") or {},
            }
        )
        if event_type == "delivered":
            delivery.status = EmailDeliveryStatus.SENT
            delivery.sent_at = delivery.sent_at or timezone.now()
            delivery.last_error = ""
        elif event_type in {"bounced", "complained", "failed"}:
            delivery.status = EmailDeliveryStatus.FAILED
            delivery.failed_at = timezone.now()
            delivery.last_error = str(payload.get("reason") or event_type)[:2000]
        if payload.get("provider_message_id") or payload.get("message_id"):
            delivery.provider_message_id = payload.get("provider_message_id") or payload.get(
                "message_id"
            )
        delivery.metadata = metadata
        delivery.save(
            update_fields=[
                "status",
                "sent_at",
                "failed_at",
                "last_error",
                "provider_message_id",
                "metadata",
                "updated_at",
            ]
        )

        if (
            event_type in EmailProviderWebhookService.HIGH_RISK_EVENTS
            and delivery.category != NotificationCategory.SECURITY
        ):
            EmailSuppression.objects.update_or_create(
                user=delivery.recipient,
                email=delivery.recipient_email,
                category=delivery.category,
                defaults={"is_active": True, "reason": f"provider_{event_type}"},
            )
            from common.audit import AuditService

            AuditService.record(
                actor=None,
                action=f"email_{event_type}",
                target=delivery,
                metadata={
                    "category": delivery.category,
                    "recipient_email": delivery.recipient_email,
                },
            )
            AuditService.record(
                actor=None,
                action="email_suppression_created",
                target_type="EmailSuppression",
                target_id=delivery.recipient_email,
                metadata={"category": delivery.category, "reason": f"provider_{event_type}"},
            )
        elif event_type in EmailProviderWebhookService.HIGH_RISK_EVENTS:
            from common.audit import AuditService

            AuditService.record(
                actor=None,
                action=f"email_{event_type}",
                target=delivery,
                metadata={"category": delivery.category, "security_suppression_skipped": True},
            )
        return delivery, True


class NotificationService:
    """
    Central service for creating notifications.
    All notification creation goes through this service to ensure consistency.
    """

    @staticmethod
    def notify(
        recipient,
        notification_type: str,
        title: str,
        body: str,
        action_url: str = "",
        payload: dict = None,
    ) -> "Notification":
        category = (payload or {}).get("category") or NOTIFICATION_CATEGORY_BY_TYPE.get(
            notification_type, NotificationCategory.SECURITY
        )
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            payload=payload or {},
            category=category,
        )
        if notification_type in EMAIL_READY_NOTIFICATION_TYPES:
            EmailDeliveryService.create_for_notification(notification)
        if category == NotificationCategory.SECURITY:
            try:
                from common.audit import AuditService

                AuditService.record(
                    actor=None,
                    action="security_notification_sent",
                    target=notification,
                    metadata={
                        "recipient_id": str(recipient.id),
                        "notification_type": notification_type,
                    },
                )
            except Exception:
                logger.exception(
                    "security_notification_audit_failed",
                    extra={"notification_id": str(notification.id)},
                )
        return notification

    @staticmethod
    def quiz_passed(user, course, score: int) -> "Notification":
        return NotificationService.notify(
            recipient=user,
            notification_type=NotificationType.QUIZ_PASSED,
            title="You passed the quiz",
            body=f"You scored {score}% on {course.title}. Your certificate is being generated.",
            action_url=f"/certificates",
            payload={"course_title": course.title, "score": score},
        )

    @staticmethod
    def certificate_issued(user, certificate) -> "Notification":
        return NotificationService.notify(
            recipient=user,
            notification_type=NotificationType.CERTIFICATE_ISSUED,
            title="Certificate ready",
            body=f"Your certificate for {certificate.course.title} is ready to download.",
            action_url="/certificates",
            payload={
                "cert_number": certificate.cert_number,
                "course_title": certificate.course.title,
            },
        )

    @staticmethod
    def track_stage_advanced(user, track, new_stage: int) -> "Notification":
        stage_names = {1: "Foundation", 2: "Core Skills", 3: "Advanced"}
        stage_name = stage_names.get(new_stage, f"Stage {new_stage}")
        return NotificationService.notify(
            recipient=user,
            notification_type=NotificationType.TRACK_STAGE_ADVANCED,
            title=f"You reached {stage_name}",
            body=f"You advanced to the {stage_name} stage of the {track.title} track.",
            action_url=f"/tracks/{track.slug}",
            payload={"track_title": track.title, "stage": new_stage},
        )

    @staticmethod
    def discussion_reply(user, thread) -> "Notification":
        return NotificationService.notify(
            recipient=user,
            notification_type=NotificationType.DISCUSSION_REPLY,
            title="Someone replied to your question",
            body=f'New reply on: "{thread.title}"',
            action_url=f"/learn/{thread.lesson.course.slug}/{thread.lesson.id}",
            payload={"thread_title": thread.title},
        )

    @staticmethod
    def welcome(user) -> "Notification":
        return NotificationService.notify(
            recipient=user,
            notification_type=NotificationType.WELCOME,
            title=f"Welcome to T-Career, {user.get_short_name()}",
            body="Start your learning journey by choosing a career track.",
            action_url="/tracks",
        )
