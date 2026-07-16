import pytest
from django.urls import reverse

from apps.notifications.models import (
    EmailDelivery,
    EmailDeliveryService,
    EmailDeliveryStatus,
    EmailSuppression,
    Notification,
    NotificationCategory,
    NotificationPreference,
    NotificationService,
    NotificationType,
)
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def test_notification_preferences_security_always_enabled(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse("notifications:preferences"),
        {
            "preferences": [
                {"category": "security", "email_enabled": False, "in_app_enabled": False}
            ]
        },
        format="json",
    )

    assert response.status_code == 200
    pref = NotificationPreference.objects.get(user=user, category=NotificationCategory.SECURITY)
    assert pref.email_enabled is True
    assert pref.in_app_enabled is True


def test_unsubscribe_suppresses_non_security_email(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("notifications:unsubscribe"), {"category": "job_alerts"}, format="json"
    )
    assert response.status_code == 200
    assert EmailSuppression.objects.filter(
        user=user, category=NotificationCategory.JOB_ALERTS, is_active=True
    ).exists()

    notification = NotificationService.notify(
        recipient=user,
        notification_type=NotificationType.NEW_JOB_MATCH,
        title="Job match",
        body="A job matched.",
    )
    delivery = EmailDelivery.objects.get(notification=notification)
    assert delivery.status == EmailDeliveryStatus.CANCELLED
    assert "suppressed" in delivery.last_error or "preferences" in delivery.last_error


def test_security_notification_bypasses_suppression():
    user = UserFactory()
    EmailSuppression.objects.create(user=user, email=user.email, category="", is_active=True)

    notification = NotificationService.notify(
        recipient=user,
        notification_type=NotificationType.APPLICATION_STAGE_CHANGED,
        title="Security notice",
        body="Account activity.",
        payload={
            "category": NotificationCategory.SECURITY,
            "template_key": "security_notification",
        },
    )

    delivery = EmailDelivery.objects.get(notification=notification)
    assert delivery.category == NotificationCategory.SECURITY
    assert delivery.status == EmailDeliveryStatus.PENDING


def test_notification_history_exposes_delivery_fields(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    notification = Notification.objects.create(
        recipient=user,
        notification_type=NotificationType.NEW_JOB_MATCH,
        title="Job match",
        body="A job matched.",
        category=NotificationCategory.JOB_ALERTS,
    )
    EmailDelivery.objects.create(
        notification=notification,
        recipient=user,
        recipient_email=user.email,
        subject="Job match",
        body="A job matched.",
        template_key="job_alert_match",
        category=NotificationCategory.JOB_ALERTS,
        status=EmailDeliveryStatus.FAILED,
        retry_count=2,
        last_error="SMTP timeout",
    )

    response = api_client.get(reverse("notifications:delivery-history"))

    assert response.status_code == 200
    payload = response.json()
    delivery = payload.get("deliveries", payload.get("data", {}).get("deliveries"))[0]
    assert delivery["category"] == "job_alerts"
    assert delivery["status"] == "failed"
    assert delivery["retry_count"] == 2


def test_email_template_rendering_includes_html():
    user = UserFactory(full_name="Ada Student")
    notification = Notification.objects.create(
        recipient=user,
        notification_type=NotificationType.NEW_JOB_MATCH,
        title="Data Analyst",
        body="A job matched.",
        category=NotificationCategory.JOB_ALERTS,
    )

    subject, body, html = EmailDeliveryService.render_template("job_alert_match", notification)

    assert "New jobs" in subject
    assert "Ada" in body
    assert "T-Career" in html
