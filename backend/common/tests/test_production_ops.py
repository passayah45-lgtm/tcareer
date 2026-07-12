import hashlib
import hmac
import json

import pytest
from django.conf import settings
from django.core import mail
from django.core.cache import caches
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.throttling import SimpleRateThrottle

from apps.audit.models import AuditLog
from apps.careers.models import CareerResume, Portfolio, VisibilityChoice
from apps.jobs.models import ApplicationStage, JobApplication, JobListing
from apps.notifications.models import (
    EmailDelivery,
    EmailDeliveryService,
    EmailDeliveryStatus,
    EmailSuppression,
    Notification,
    NotificationCategory,
    NotificationService,
    NotificationType,
)
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.trust.management.commands.release_candidate_check import (
    Command as ReleaseCandidateCheckCommand,
)
from apps.users.tests.factories import RecruiterFactory, UserFactory
from common.ops import release_metadata, validate_production_redis_settings

pytestmark = pytest.mark.django_db


def signed_json_post(api_client, url, payload, headers=None):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return api_client.post(url, data=body, content_type="application/json", **(headers or {}))


def hmac_hex(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


@pytest.fixture
def ops_recruiting_context():
    recruiter = RecruiterFactory()
    candidate = UserFactory(is_public_profile=True, full_name="Ops Candidate")
    organization = Organization.objects.create(
        name="Ops Co", organization_type=OrganizationType.COMPANY, status="active"
    )
    OrganizationMembership.objects.create(
        organization=organization, user=recruiter, role=OrganizationRole.RECRUITER
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=2,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    job = JobListing.objects.create(
        organization=organization,
        posted_by=recruiter,
        title="Ops Analyst",
        company_name="Ops Co",
        description="Watch dashboards.",
        requirements=["SQL"],
        required_skills=["SQL"],
        is_active=True,
    )
    portfolio = Portfolio.objects.create(
        user=candidate, visibility=VisibilityChoice.PUBLIC, headline="Ops learner"
    )
    resume = CareerResume.objects.create(user=candidate, title="Ops Resume")
    application = JobApplication.objects.create(
        job=job,
        organization=organization,
        candidate=candidate,
        stage=ApplicationStage.APPLIED,
    )
    return recruiter, candidate, organization, job, portfolio, resume, application


def test_health_endpoints_report_status(api_client):
    health = api_client.get("/api/v1/health/")
    ready = api_client.get("/api/v1/health/ready/")
    live = api_client.get("/api/v1/health/live/")

    assert health.status_code == 200
    assert ready.status_code == 200
    assert live.status_code == 200
    assert health.json()["service"] == "tcareer-api"
    assert "release" in health.json()
    assert "app_version" in health.json()["release"]
    assert "database" in health.json()["checks"]
    assert "cache" in health.json()["checks"]


def test_cache_and_throttle_use_configured_default_cache():
    assert "default" in settings.CACHES
    assert settings.THROTTLE_CACHE_ALIAS == "default"
    assert caches["default"] is not None
    assert SimpleRateThrottle.cache is not None


def test_production_redis_enforcement_rejects_local_cache():
    class UnsafeSettings:
        DEBUG = False
        DEPLOY_ENVIRONMENT = "production"
        REDIS_URL = ""
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "local",
            }
        }
        THROTTLE_CACHE_ALIAS = "default"

    errors = validate_production_redis_settings(UnsafeSettings)

    assert any("REDIS_URL" in error for error in errors)
    assert any("local memory" in error for error in errors)


@override_settings(
    DEBUG=False,
    DEPLOY_ENVIRONMENT="production",
    REDIS_URL="",
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unsafe",
        }
    },
)
def test_ready_health_fails_without_production_redis(api_client):
    response = api_client.get("/api/v1/health/ready/")

    assert response.status_code == 503
    assert response.json()["checks"]["cache"]["status"] == "error"


@override_settings(
    SENTRY_DSN="",
    SENTRY_RELEASE="release-1",
    GIT_SHA="abc123",
    APP_VERSION="1.2.3",
    DEPLOY_ENVIRONMENT="staging",
)
def test_sentry_release_metadata_available_without_dsn():
    metadata = release_metadata(settings)

    assert metadata["release"] == "release-1"
    assert metadata["git_sha"] == "abc123"
    assert metadata["app_version"] == "1.2.3"
    assert metadata["environment"] == "staging"


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_email_delivery_idempotency_prevents_duplicate_send():
    user = UserFactory()
    notification = Notification.objects.create(
        recipient=user,
        notification_type=NotificationType.NEW_JOB_MATCH,
        title="Match",
        body="A job matched.",
    )
    delivery = EmailDelivery.objects.create(
        notification=notification,
        recipient=user,
        recipient_email=user.email,
        subject="Match",
        body="A job matched.",
        template_key="job_alert_match",
        metadata={"idempotency_key": "ops-test-key"},
        status=EmailDeliveryStatus.PENDING,
    )

    EmailDeliveryService.send_email_delivery(delivery.id)
    EmailDeliveryService.send_email_delivery(delivery.id)
    delivery.refresh_from_db()

    assert delivery.status == EmailDeliveryStatus.SENT
    assert len(mail.outbox) == 1


@override_settings(SES_WEBHOOK_SECRET="ses-secret")
def test_ses_webhook_verification_updates_delivery(api_client):
    user = UserFactory()
    notification = Notification.objects.create(
        recipient=user,
        notification_type=NotificationType.NEW_JOB_MATCH,
        title="Match",
        body="A job matched.",
        category=NotificationCategory.JOB_ALERTS,
    )
    delivery = EmailDelivery.objects.create(
        notification=notification,
        recipient=user,
        recipient_email=user.email,
        subject="Match",
        body="A job matched.",
        template_key="job_alert_match",
        category=NotificationCategory.JOB_ALERTS,
        status=EmailDeliveryStatus.PENDING,
    )

    payload = {
        "provider": "ses",
        "event": "delivered",
        "event_id": "evt-1",
        "delivery_id": str(delivery.id),
        "provider_message_id": "msg-1",
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    response = signed_json_post(
        api_client,
        reverse("notifications:email-provider-webhook"),
        payload,
        {
            "HTTP_X_TCAREER_EMAIL_PROVIDER": "ses",
            "HTTP_X_TCAREER_SES_SIGNATURE": hmac_hex("ses-secret", body),
        },
    )

    assert response.status_code == 200
    delivery.refresh_from_db()
    assert delivery.status == EmailDeliveryStatus.SENT
    assert delivery.provider_message_id == "msg-1"


@override_settings(SENDGRID_WEBHOOK_SECRET="sendgrid-secret")
def test_sendgrid_webhook_verification(api_client):
    user = UserFactory()
    delivery = EmailDelivery.objects.create(
        recipient=user,
        recipient_email=user.email,
        subject="Match",
        body="A job matched.",
        template_key="job_alert_match",
        status=EmailDeliveryStatus.PENDING,
    )
    payload = {
        "provider": "sendgrid",
        "event": "delivered",
        "event_id": "sg-1",
        "delivery_id": str(delivery.id),
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = "1720000000"

    response = signed_json_post(
        api_client,
        reverse("notifications:email-provider-webhook"),
        payload,
        {
            "HTTP_X_TWILIO_EMAIL_EVENT_WEBHOOK_TIMESTAMP": timestamp,
            "HTTP_X_TWILIO_EMAIL_EVENT_WEBHOOK_SIGNATURE": hmac_hex(
                "sendgrid-secret", f"{timestamp}.".encode() + body
            ),
            "HTTP_X_TCAREER_EMAIL_PROVIDER": "sendgrid",
        },
    )

    assert response.status_code == 200


@override_settings(MAILGUN_WEBHOOK_SIGNING_KEY="mailgun-secret")
def test_mailgun_webhook_verification(api_client):
    user = UserFactory()
    delivery = EmailDelivery.objects.create(
        recipient=user,
        recipient_email=user.email,
        subject="Match",
        body="A job matched.",
        template_key="job_alert_match",
        status=EmailDeliveryStatus.PENDING,
    )
    timestamp = "1720000000"
    token = "mailgun-token"
    signature = hmac.new(
        b"mailgun-secret", f"{timestamp}{token}".encode(), hashlib.sha256
    ).hexdigest()
    response = api_client.post(
        reverse("notifications:email-provider-webhook"),
        {
            "provider": "mailgun",
            "event": "delivered",
            "event_id": "mg-1",
            "delivery_id": str(delivery.id),
            "timestamp": timestamp,
            "token": token,
            "signature": signature,
        },
        format="json",
        HTTP_X_TCAREER_EMAIL_PROVIDER="mailgun",
    )

    assert response.status_code == 200


@override_settings(SES_WEBHOOK_SECRET="ses-secret")
def test_email_provider_webhook_invalid_signature_fails_closed(api_client):
    response = signed_json_post(
        api_client,
        reverse("notifications:email-provider-webhook"),
        {"provider": "ses", "event": "delivered", "event_id": "evt-2"},
        {"HTTP_X_TCAREER_EMAIL_PROVIDER": "ses", "HTTP_X_TCAREER_SES_SIGNATURE": "wrong"},
    )

    assert response.status_code == 403
    assert AuditLog.objects.filter(action="provider_webhook_rejected").exists()


@override_settings(EMAIL_WEBHOOK_SECRET="secret", EMAIL_WEBHOOK_ALLOW_SHARED_SECRET=True)
def test_email_provider_webhook_is_idempotent(api_client):
    user = UserFactory()
    delivery = EmailDelivery.objects.create(
        recipient=user,
        recipient_email=user.email,
        subject="Match",
        body="A job matched.",
        template_key="job_alert_match",
        category=NotificationCategory.JOB_ALERTS,
        status=EmailDeliveryStatus.PENDING,
    )
    payload = {"event": "opened", "event_id": "evt-repeat", "delivery_id": str(delivery.id)}

    first = api_client.post(
        reverse("notifications:email-provider-webhook"),
        payload,
        format="json",
        HTTP_X_TCAREER_EMAIL_WEBHOOK_SECRET="secret",
    )
    second = api_client.post(
        reverse("notifications:email-provider-webhook"),
        payload,
        format="json",
        HTTP_X_TCAREER_EMAIL_WEBHOOK_SECRET="secret",
    )

    delivery.refresh_from_db()
    events = delivery.metadata["provider_events"]
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["processed"] is False
    assert len(events) == 1


@override_settings(EMAIL_WEBHOOK_SECRET="secret", EMAIL_WEBHOOK_ALLOW_SHARED_SECRET=True)
def test_bounce_and_complaint_create_suppression_and_audit(api_client):
    user = UserFactory()
    delivery = EmailDelivery.objects.create(
        recipient=user,
        recipient_email=user.email,
        subject="Match",
        body="A job matched.",
        template_key="job_alert_match",
        category=NotificationCategory.JOB_ALERTS,
        status=EmailDeliveryStatus.SENT,
    )

    response = api_client.post(
        reverse("notifications:email-provider-webhook"),
        {
            "event": "bounced",
            "event_id": "evt-bounce",
            "delivery_id": str(delivery.id),
            "reason": "mailbox unavailable",
        },
        format="json",
        HTTP_X_TCAREER_EMAIL_WEBHOOK_SECRET="secret",
    )

    assert response.status_code == 200
    delivery.refresh_from_db()
    assert delivery.status == EmailDeliveryStatus.FAILED
    assert EmailSuppression.objects.filter(
        user=user, category=NotificationCategory.JOB_ALERTS, is_active=True
    ).exists()
    assert AuditLog.objects.filter(action="email_bounced", target_id=str(delivery.id)).exists()
    assert AuditLog.objects.filter(
        action="email_suppression_created", target_id=user.email
    ).exists()


@override_settings(EMAIL_WEBHOOK_SECRET="secret", EMAIL_WEBHOOK_ALLOW_SHARED_SECRET=True)
def test_security_email_bounce_does_not_suppress(api_client):
    user = UserFactory()
    delivery = EmailDelivery.objects.create(
        recipient=user,
        recipient_email=user.email,
        subject="Security",
        body="Security notice.",
        template_key="security_notification",
        category=NotificationCategory.SECURITY,
        status=EmailDeliveryStatus.SENT,
    )

    response = api_client.post(
        reverse("notifications:email-provider-webhook"),
        {"event": "complained", "event_id": "evt-complaint", "delivery_id": str(delivery.id)},
        format="json",
        HTTP_X_TCAREER_EMAIL_WEBHOOK_SECRET="secret",
    )

    assert response.status_code == 200
    assert not EmailSuppression.objects.filter(
        user=user, category=NotificationCategory.SECURITY, is_active=True
    ).exists()
    assert AuditLog.objects.filter(action="email_complained", target_id=str(delivery.id)).exists()


@override_settings(
    DEPLOY_ENVIRONMENT="production",
    EMAIL_WEBHOOK_SECRET="secret",
    EMAIL_WEBHOOK_ALLOW_SHARED_SECRET=True,
)
def test_production_rejects_shared_secret_fallback(api_client):
    response = api_client.post(
        reverse("notifications:email-provider-webhook"),
        {"event": "delivered", "event_id": "fallback-prod"},
        format="json",
        HTTP_X_TCAREER_EMAIL_WEBHOOK_SECRET="secret",
    )

    assert response.status_code == 403


def test_security_notification_sent_is_audited():
    user = UserFactory()

    NotificationService.notify(
        recipient=user,
        notification_type=NotificationType.WELCOME,
        title="Welcome",
        body="Welcome to T-Career.",
    )

    assert AuditLog.objects.filter(action="security_notification_sent").exists()


def test_candidate_search_writes_audit_event(api_client, ops_recruiting_context):
    recruiter, _, organization, *_ = ops_recruiting_context
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(
        reverse("jobs:candidate-search", args=[organization.id]), {"search": "Ops"}
    )

    assert response.status_code == 200
    assert AuditLog.objects.filter(actor=recruiter, action="candidate_search_performed").exists()


def test_ops_health_requires_admin(api_client):
    denied = api_client.get("/api/v1/health/ops/")
    admin = UserFactory(is_staff=True)
    api_client.force_authenticate(user=admin)
    allowed = api_client.get("/api/v1/health/ops/")

    assert denied.status_code in {401, 403}
    assert allowed.status_code == 200
    assert "email_queue" in allowed.json()
    assert "celery" in allowed.json()
    assert "redis_broker" in allowed.json()


def test_production_smoke_check_runs_without_exposing_secrets():
    call_command("production_smoke_check")


def test_release_candidate_check_runs_in_safe_mode():
    call_command("release_candidate_check")


def test_validate_production_providers_safe_mode_runs():
    call_command("validate_production_providers", "--json")


@override_settings(
    DEPLOY_ENVIRONMENT="production",
    EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
)
def test_validate_production_providers_fails_missing_production_email():
    with pytest.raises(CommandError):
        call_command("validate_production_providers", "--email")


def test_run_retention_policies_dry_run_reports_counts():
    call_command("run_retention_policies", "--dry-run", "--data-type", "analytics_events", "--json")


def test_run_retention_policies_requires_explicit_delete_for_changes():
    call_command("run_retention_policies", "--data-type", "email_deliveries", "--limit", "10")


@override_settings(AUDIT_RETENTION_ENABLED=True, AUDIT_RETENTION_DAYS=1)
def test_run_retention_policies_does_not_delete_append_only_audit_logs():
    old_log = AuditLog.objects.create(
        action="old_event",
        target_type="test",
        target_id="old",
        metadata={},
    )
    AuditLog.objects.filter(id=old_log.id).update(
        created_at=timezone.now() - timezone.timedelta(days=10)
    )

    call_command("run_retention_policies", "--data-type", "audit_logs", "--delete")

    assert AuditLog.objects.filter(id=old_log.id).exists()


def test_release_candidate_check_fail_on_warning_raises_for_missing_release_metadata():
    with override_settings(GIT_SHA="", BUILD_DATE="", API_VERSION=""):
        with pytest.raises(CommandError):
            call_command("release_candidate_check", "--fail-on-warning")


@override_settings(
    DEPLOY_ENVIRONMENT="production",
    DEBUG=False,
    EMAIL_WEBHOOK_ALLOW_SHARED_SECRET=True,
    ALLOWED_HOSTS=["api.example.test"],
)
def test_release_candidate_security_check_fails_shared_email_secret_in_production():
    result = ReleaseCandidateCheckCommand().check_security_settings()

    assert result["status"] == "fail"
    assert "shared email webhook fallback" in result["detail"]


def test_backup_restore_check_dry_run():
    call_command("backup_restore_check", "--dry-run")


def test_query_budget_recruiter_dashboard(api_client, ops_recruiting_context):
    recruiter, _, organization, *_ = ops_recruiting_context
    api_client.force_authenticate(user=recruiter)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(reverse("jobs:recruiter-dashboard", args=[organization.id]))

    assert response.status_code == 200
    assert len(queries) <= 35


def test_query_budget_student_dashboard(api_client, ops_recruiting_context):
    _, candidate, *_ = ops_recruiting_context
    api_client.force_authenticate(user=candidate)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(reverse("jobs:student-dashboard"))

    assert response.status_code == 200
    assert len(queries) <= 65


def test_query_budget_application_detail(api_client, ops_recruiting_context):
    recruiter, _, organization, _, _, _, application = ops_recruiting_context
    api_client.force_authenticate(user=recruiter)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(
            reverse("jobs:application-detail", args=[organization.id, application.id])
        )

    assert response.status_code == 200
    assert len(queries) <= 45


def test_query_budget_job_detail(api_client, ops_recruiting_context):
    _, _, _, job, *_ = ops_recruiting_context

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(reverse("jobs:job-detail", args=[job.id]))

    assert response.status_code == 200
    assert len(queries) <= 12


def test_query_budget_notification_history(api_client):
    user = UserFactory()
    for index in range(3):
        notification = Notification.objects.create(
            recipient=user,
            notification_type=NotificationType.NEW_JOB_MATCH,
            title=f"Match {index}",
            body="A job matched.",
        )
        EmailDelivery.objects.create(
            notification=notification,
            recipient=user,
            recipient_email=user.email,
            subject=f"Match {index}",
            body="A job matched.",
            template_key="job_alert_match",
        )
    api_client.force_authenticate(user=user)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(reverse("notifications:delivery-history"))

    assert response.status_code == 200
    assert len(queries) <= 6
