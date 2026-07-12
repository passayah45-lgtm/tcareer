import pytest
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.careers.models import CareerResume, Portfolio, VisibilityChoice
from apps.jobs.models import JobListing
from apps.notifications.models import (
    EmailDelivery,
    EmailDeliveryService,
    EmailDeliveryStatus,
    EmailSuppression,
    Notification,
    NotificationCategory,
    NotificationPreference,
    NotificationType,
)
from apps.organizations.models import (
    CandidateProfileUnlock,
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.users.models import UserPrivacySettings
from apps.users.tests.factories import RecruiterFactory, UserFactory
from common.candidate_visibility import CandidateVisibilityService
from common.throttles import NotificationPreferenceRateThrottle


pytestmark = pytest.mark.django_db


@pytest.fixture
def visibility_context():
    recruiter = RecruiterFactory()
    candidate = UserFactory(is_public_profile=True)
    organization = Organization.objects.create(name="Visibility Co", organization_type=OrganizationType.COMPANY, status="active")
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    Portfolio.objects.create(user=candidate, visibility=VisibilityChoice.PUBLIC, headline="API learner")
    return recruiter, candidate, organization


def test_candidate_visibility_service_enforces_privacy_and_unlocks(visibility_context):
    recruiter, candidate, organization = visibility_context
    privacy = UserPrivacySettings.objects.create(
        user=candidate,
        public_profile=True,
        recruiter_resume_visibility=False,
        recruiter_portfolio_visibility=True,
        allow_recruiter_contact=False,
    )

    visibility = CandidateVisibilityService.evaluate(recruiter, candidate, organization=organization)

    assert visibility.can_view_profile is True
    assert visibility.can_view_resume is False
    assert visibility.can_view_portfolio is True
    assert visibility.can_contact is False

    privacy.public_profile = False
    privacy.save()
    assert CandidateVisibilityService.can_view_profile(recruiter, candidate, organization=organization) is False

    CandidateProfileUnlock.objects.create(organization=organization, candidate=candidate, unlocked_by=recruiter)
    assert CandidateVisibilityService.can_view_profile(recruiter, candidate, organization=organization) is True


def test_notification_preferences_are_throttled(api_client, monkeypatch):
    cache.clear()
    rates = dict(NotificationPreferenceRateThrottle.THROTTLE_RATES)
    rates["notification_preferences"] = "1/minute"
    monkeypatch.setattr(NotificationPreferenceRateThrottle, "THROTTLE_RATES", rates)
    user = UserFactory()
    api_client.force_authenticate(user=user)

    first = api_client.get(reverse("notifications:preferences"))
    second = api_client.get(reverse("notifications:preferences"))

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["errors"]["code"] == "rate_limited"


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_email_send_rechecks_suppression_before_provider_send():
    user = UserFactory()
    notification = Notification.objects.create(
        recipient=user,
        notification_type=NotificationType.NEW_JOB_MATCH,
        title="Job match",
        body="A job matched.",
        category=NotificationCategory.JOB_ALERTS,
    )
    delivery = EmailDelivery.objects.create(
        notification=notification,
        recipient=user,
        recipient_email=user.email,
        subject="Job match",
        body="A job matched.",
        template_key="job_alert_match",
        category=NotificationCategory.JOB_ALERTS,
        status=EmailDeliveryStatus.PENDING,
    )
    EmailSuppression.objects.create(user=user, email=user.email, category=NotificationCategory.JOB_ALERTS)

    EmailDeliveryService.send_email_delivery(delivery.id)
    delivery.refresh_from_db()

    assert delivery.status == EmailDeliveryStatus.CANCELLED
    assert "suppressed" in delivery.last_error


def test_privacy_and_notification_changes_are_audited(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    privacy_response = api_client.patch(reverse("users:privacy-settings"), {"allow_recruiter_contact": False}, format="json")
    pref_response = api_client.patch(
        reverse("notifications:preferences"),
        {"preferences": [{"category": "job_alerts", "email_enabled": False}]},
        format="json",
    )

    assert privacy_response.status_code == 200
    assert pref_response.status_code == 200
    assert AuditLog.objects.filter(actor=user, action="privacy_settings_changed").exists()
    assert AuditLog.objects.filter(actor=user, action="notification_preference_changed").exists()


def test_permission_errors_use_standard_error_shape(api_client, visibility_context):
    recruiter, candidate, organization = visibility_context
    UserPrivacySettings.objects.create(user=candidate, recruiter_resume_visibility=False)
    CandidateProfileUnlock.objects.create(organization=organization, candidate=candidate, unlocked_by=recruiter)
    resume = CareerResume.objects.create(user=candidate, title="Hidden Resume")
    resume.files.create(file_url="https://example.com/resume.pdf", file_name="resume.pdf", content_type="application/pdf", uploaded_by=candidate)
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(f"{reverse('careers:career-resume-download', args=[resume.id])}?organization_id={organization.id}", {}, format="json")

    assert response.status_code == 403
    assert response.json()["errors"]["code"] == "permission_denied"


def test_candidate_search_query_count_is_bounded(api_client, visibility_context):
    recruiter, candidate, organization = visibility_context
    for index in range(3):
        user = UserFactory(is_public_profile=True)
        Portfolio.objects.create(user=user, visibility=VisibilityChoice.PUBLIC, headline=f"Candidate {index}")
    JobListing.objects.create(
        organization=organization,
        title="Backend Developer",
        company_name="Visibility Co",
        description="Build APIs",
        requirements=["Django"],
        is_active=True,
    )
    api_client.force_authenticate(user=recruiter)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(reverse("jobs:candidate-search", args=[organization.id]))

    assert response.status_code == 200
    assert len(queries) <= 25
