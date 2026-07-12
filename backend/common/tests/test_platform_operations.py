import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.audit.models import AuditLog
from apps.courses.models import Course, CourseStatus
from apps.notifications.models import EmailDelivery, EmailDeliveryStatus, Notification, NotificationCategory, NotificationType
from apps.organizations.models import Organization, OrganizationStatus, OrganizationType
from apps.profiles.models import InstructorProfile
from apps.users.models import UserRole
from apps.users.tests.factories import UserFactory
from apps.verification.models import SubjectType, VerificationRequest, VerificationRequestStatus


pytestmark = pytest.mark.django_db


def _admin():
    return UserFactory(role=UserRole.SUPER_ADMIN, is_staff=True, is_verified=True)


def _notification(user):
    return Notification.objects.create(
        recipient=user,
        notification_type=NotificationType.WELCOME,
        title="Welcome",
        body="Welcome to T-Career",
        category=NotificationCategory.SECURITY,
    )


def test_platform_operations_requires_platform_admin(api_client):
    response = api_client.get(reverse("platform-operations"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    api_client.force_authenticate(user=UserFactory(role=UserRole.STUDENT))
    response = api_client.get(reverse("platform-operations"))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_platform_operations_returns_queues(api_client):
    admin = _admin()
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    Course.objects.create(
        instructor=instructor,
        title="Production Admin Course",
        slug="production-admin-course",
        status=CourseStatus.PUBLISHED,
    )
    Organization.objects.create(
        name="Pending University",
        organization_type=OrganizationType.UNIVERSITY,
        status=OrganizationStatus.PENDING,
    )
    EmailDelivery.objects.create(
        notification=_notification(admin),
        recipient=admin,
        recipient_email=admin.email,
        subject="Needs retry",
        body="Retry me",
        template_key="security_notification",
        category=NotificationCategory.SECURITY,
        status=EmailDeliveryStatus.FAILED,
    )

    api_client.force_authenticate(user=admin)
    response = api_client.get(reverse("platform-operations"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["counts"]["published_courses"] == 1
    assert response.data["counts"]["pending_organizations"] == 1
    assert response.data["counts"]["email_attention"] == 1
    assert {"users", "organizations", "courses", "verification", "email", "audit"} <= set(response.data["queues"])


def test_platform_user_action_deactivates_and_audits(api_client):
    admin = _admin()
    target = UserFactory(role=UserRole.STUDENT, is_active=True)
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-operation-action", args=["users", target.id, "deactivate"]),
        {"reason": "Account requested platform deactivation."},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    target.refresh_from_db()
    assert target.is_active is False
    assert AuditLog.objects.filter(action="platform_user_deactivate", target_id=str(target.id)).exists()


def test_platform_user_action_blocks_self_deactivation(api_client):
    admin = _admin()
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-operation-action", args=["users", admin.id, "deactivate"]),
        {"reason": "Testing self deactivation protection."},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    admin.refresh_from_db()
    assert admin.is_active is True


def test_platform_course_archive_action(api_client):
    admin = _admin()
    course = Course.objects.create(
        instructor=UserFactory(role=UserRole.INSTRUCTOR),
        title="Archive Me",
        slug="archive-me",
        status=CourseStatus.PUBLISHED,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-operation-action", args=["courses", course.id, "archive"]),
        {"reason": "Course violates moderation requirements."},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    course.refresh_from_db()
    assert course.status == CourseStatus.ARCHIVED
    assert AuditLog.objects.filter(action="platform_course_archived", target_id=str(course.id)).exists()


def test_platform_organization_lifecycle_action(api_client):
    admin = _admin()
    organization = Organization.objects.create(
        name="Suspendable Company",
        organization_type=OrganizationType.COMPANY,
        status=OrganizationStatus.ACTIVE,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-operation-action", args=["organizations", organization.id, "suspend"]),
        {"reason": "Organization requires compliance review."},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    organization.refresh_from_db()
    assert organization.status == OrganizationStatus.SUSPENDED
    assert organization.suspended_at is not None
    assert AuditLog.objects.filter(action="organization_suspend", target_id=str(organization.id)).exists()


def test_platform_email_cancel_action(api_client):
    admin = _admin()
    delivery = EmailDelivery.objects.create(
        notification=_notification(admin),
        recipient=admin,
        recipient_email=admin.email,
        subject="Pending email",
        body="Pending body",
        template_key="security_notification",
        category=NotificationCategory.SECURITY,
        status=EmailDeliveryStatus.PENDING,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-operation-action", args=["email", delivery.id, "cancel"]),
        {"reason": "Recipient should not receive this delivery."},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    delivery.refresh_from_db()
    assert delivery.status == EmailDeliveryStatus.CANCELLED
    assert AuditLog.objects.filter(action="platform_email_cancelled", target_id=str(delivery.id)).exists()


def test_platform_sensitive_actions_require_reason(api_client):
    admin = _admin()
    target = UserFactory(role=UserRole.STUDENT, is_active=True)
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("platform-operation-action", args=["users", target.id, "deactivate"]))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    target.refresh_from_db()
    assert target.is_active is True


def test_platform_email_retry_action_uses_email_service(api_client, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    admin = _admin()
    delivery = EmailDelivery.objects.create(
        notification=_notification(admin),
        recipient=admin,
        recipient_email=admin.email,
        subject="Retry email",
        body="Retry body",
        template_key="security_notification",
        category=NotificationCategory.SECURITY,
        status=EmailDeliveryStatus.FAILED,
        failed_at=timezone.now(),
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("platform-operation-action", args=["email", delivery.id, "retry"]))

    assert response.status_code == status.HTTP_200_OK
    delivery.refresh_from_db()
    assert delivery.status == EmailDeliveryStatus.FAILED
    assert "SMTP is not configured" in delivery.last_error
    assert AuditLog.objects.filter(action="platform_email_retry", target_id=str(delivery.id)).exists()


def test_platform_verification_approve_action(api_client):
    admin = _admin()
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    profile = InstructorProfile.objects.create(user=instructor)
    verification = VerificationRequest.objects.create(
        subject_type=SubjectType.INSTRUCTOR,
        subject_id=profile.id,
        submitted_by=instructor,
        status=VerificationRequestStatus.SUBMITTED,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-operation-action", args=["verification", verification.id, "approve"]),
        {"reason": "Documents and teaching credentials verified."},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    verification.refresh_from_db()
    profile.refresh_from_db()
    assert verification.status == VerificationRequestStatus.APPROVED
    assert profile.verification_status == "verified"
    assert AuditLog.objects.filter(action="platform_verification_approve", target_id=str(verification.id)).exists()


def test_platform_verification_reject_requires_reason(api_client):
    admin = _admin()
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    profile = InstructorProfile.objects.create(user=instructor)
    verification = VerificationRequest.objects.create(
        subject_type=SubjectType.INSTRUCTOR,
        subject_id=profile.id,
        submitted_by=instructor,
        status=VerificationRequestStatus.SUBMITTED,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("platform-operation-action", args=["verification", verification.id, "reject"]))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    verification.refresh_from_db()
    assert verification.status == VerificationRequestStatus.SUBMITTED


def test_platform_verification_more_info_action(api_client):
    admin = _admin()
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    profile = InstructorProfile.objects.create(user=instructor)
    verification = VerificationRequest.objects.create(
        subject_type=SubjectType.INSTRUCTOR,
        subject_id=profile.id,
        submitted_by=instructor,
        status=VerificationRequestStatus.SUBMITTED,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-operation-action", args=["verification", verification.id, "more_info"]),
        {"reason": "Please upload a clearer identity document."},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    verification.refresh_from_db()
    assert verification.status == VerificationRequestStatus.MORE_INFO_REQUIRED
    assert AuditLog.objects.filter(action="platform_verification_more_info", target_id=str(verification.id)).exists()


def test_platform_audit_search_filters_results(api_client):
    admin = _admin()
    target = UserFactory(role=UserRole.STUDENT)
    AuditLog.objects.create(actor=admin, action="platform_user_deactivate", target_type="User", target_id=str(target.id))
    AuditLog.objects.create(actor=admin, action="unrelated_event", target_type="System", target_id="system")
    api_client.force_authenticate(user=admin)

    response = api_client.get(reverse("platform-audit-search"), {"q": "deactivate"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total"] == 1
    assert response.data["results"][0]["action"] == "platform_user_deactivate"
