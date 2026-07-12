import pytest
from django.core import mail
from django.core.management import call_command
from django.test import override_settings

from apps.notifications.models import EmailDelivery, EmailDeliveryService, EmailDeliveryStatus, Notification, NotificationType
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def make_delivery(user=None, status=EmailDeliveryStatus.PENDING):
    user = user or UserFactory(email="email-target@example.com")
    notification = Notification.objects.create(
        recipient=user,
        notification_type=NotificationType.NEW_JOB_MATCH,
        title="New match",
        body="A job matched your alert.",
        payload={"template_key": "job_alert_match"},
    )
    return EmailDelivery.objects.create(
        notification=notification,
        recipient=user,
        recipient_email=user.email,
        subject="New match",
        body="A job matched your alert.",
        template_key="job_alert_match",
        status=status,
    )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_email_service_dry_run_does_not_send():
    delivery = make_delivery()

    processed = EmailDeliveryService.bulk_process_pending(limit=50, dry_run=True)
    delivery.refresh_from_db()

    assert len(processed) == 1
    assert delivery.status == EmailDeliveryStatus.PENDING
    assert len(mail.outbox) == 0


@override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
def test_email_service_skips_missing_smtp():
    delivery = make_delivery()

    EmailDeliveryService.send_email_delivery(delivery.id)
    delivery.refresh_from_db()

    assert delivery.status == EmailDeliveryStatus.FAILED
    assert "SMTP is not configured" in delivery.last_error


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="T-Career <noreply@example.com>",
)
def test_email_service_sends_with_configured_backend():
    delivery = make_delivery()

    EmailDeliveryService.send_email_delivery(delivery.id)
    delivery.refresh_from_db()

    assert delivery.status == EmailDeliveryStatus.SENT
    assert delivery.sent_at is not None
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [delivery.recipient_email]


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="T-Career <noreply@example.com>",
)
def test_retry_failed_delivery_sends_again():
    delivery = make_delivery(status=EmailDeliveryStatus.FAILED)
    delivery.last_error = "Temporary SMTP problem"
    delivery.save(update_fields=["last_error"])

    processed = EmailDeliveryService.retry_failed(limit=50)
    delivery.refresh_from_db()

    assert processed == [delivery]
    assert delivery.status == EmailDeliveryStatus.SENT
    assert delivery.last_error == ""


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_process_email_deliveries_command_dry_run():
    make_delivery()

    call_command("process_email_deliveries", "--dry-run")

    assert EmailDelivery.objects.filter(status=EmailDeliveryStatus.PENDING).count() == 1
    assert len(mail.outbox) == 0


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="T-Career <noreply@example.com>",
)
def test_process_email_deliveries_command_limit():
    make_delivery(UserFactory(email="one@example.com"))
    make_delivery(UserFactory(email="two@example.com"))

    call_command("process_email_deliveries", "--limit", "1")

    assert EmailDelivery.objects.filter(status=EmailDeliveryStatus.SENT).count() == 1
    assert EmailDelivery.objects.filter(status=EmailDeliveryStatus.PENDING).count() == 1
