import pytest
from django.urls import reverse
from rest_framework import status

from apps.audit.models import AuditLog
from apps.profiles.models import InstructorProfile
from apps.users.models import UserRole
from apps.users.tests.factories import UserFactory
from apps.verification.models import (
    DocumentType,
    IdentityVerificationDocument,
    SubjectType,
    VerificationAction,
    VerificationRequest,
    VerificationRequestStatus,
)


pytestmark = pytest.mark.django_db


def _admin():
    return UserFactory(role=UserRole.SUPER_ADMIN, is_staff=True, is_verified=True)


def _verification(status=VerificationRequestStatus.SUBMITTED):
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    profile = InstructorProfile.objects.create(user=instructor)
    request = VerificationRequest.objects.create(
        subject_type=SubjectType.INSTRUCTOR,
        subject_id=profile.id,
        submitted_by=instructor,
        status=status,
    )
    return instructor, profile, request


def test_platform_verification_queue_requires_platform_admin(api_client):
    response = api_client.get(reverse("platform-verification-queue"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    api_client.force_authenticate(user=UserFactory(role=UserRole.STUDENT))
    response = api_client.get(reverse("platform-verification-queue"))
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_platform_verification_queue_filters_by_status(api_client):
    admin = _admin()
    _verification(status=VerificationRequestStatus.SUBMITTED)
    _verification(status=VerificationRequestStatus.APPROVED)
    api_client.force_authenticate(user=admin)

    response = api_client.get(reverse("platform-verification-queue"), {"status": VerificationRequestStatus.APPROVED})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total"] == 1
    assert response.data["results"][0]["status"] == VerificationRequestStatus.APPROVED
    assert response.data["counts"][VerificationRequestStatus.SUBMITTED] == 1
    assert response.data["counts"][VerificationRequestStatus.APPROVED] == 1


def test_platform_verification_detail_hides_private_storage_fields(api_client):
    admin = _admin()
    _, profile, verification = _verification()
    IdentityVerificationDocument.objects.create(
        owner_type=SubjectType.INSTRUCTOR,
        owner_id=profile.id,
        document_type=DocumentType.PASSPORT,
        s3_bucket="private-verification-bucket",
        s3_key="verification/private/passport.pdf",
        file_name="passport.pdf",
        file_size=1234,
        mime_type="application/pdf",
        uploaded_by=verification.submitted_by,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.get(reverse("platform-verification-detail", args=[verification.id]))

    assert response.status_code == status.HTTP_200_OK
    document = response.data["request"]["documents"][0]
    assert document["file_name"] == "passport.pdf"
    assert "s3_bucket" not in document
    assert "s3_key" not in document


def test_platform_verification_approve_updates_request_and_audits(api_client):
    admin = _admin()
    _, profile, verification = _verification()
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("platform-verification-action", args=[verification.id, "approve"]),
        {"reason": "Identity and instructor credentials verified."},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    verification.refresh_from_db()
    profile.refresh_from_db()
    assert verification.status == VerificationRequestStatus.APPROVED
    assert profile.verification_status == "verified"
    assert VerificationAction.objects.filter(target_id=profile.id, action="approved").exists()
    assert AuditLog.objects.filter(action="platform_verification_approve", target_id=str(verification.id)).exists()


def test_platform_verification_reject_requires_reason(api_client):
    admin = _admin()
    _, _, verification = _verification()
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("platform-verification-action", args=[verification.id, "reject"]))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    verification.refresh_from_db()
    assert verification.status == VerificationRequestStatus.SUBMITTED


def test_platform_verification_more_info_requires_reason(api_client):
    admin = _admin()
    _, _, verification = _verification()
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("platform-verification-action", args=[verification.id, "more_info"]), {"reason": "Too short"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    verification.refresh_from_db()
    assert verification.status == VerificationRequestStatus.SUBMITTED
