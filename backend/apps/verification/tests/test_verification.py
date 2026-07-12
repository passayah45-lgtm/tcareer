import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient

from apps.profiles.models import (
    InstructorProfile,
    Organization,
    OrganizationType,
    RecruiterProfile,
    VerificationStatus,
)
from apps.trust.models import TrustScoreLog
from apps.verification.models import (
    IdentityVerificationDocument,
    VerificationAction,
    VerificationRequest,
    VerificationRequestStatus,
    SubjectType,
    DocumentType,
)
from apps.verification.services import (
    approve_verification,
    DocumentValidationError,
    reject_verification,
    request_more_information,
    reinstate_subject,
    submit_for_review,
    suspend_subject,
    validate_document,
)

User = get_user_model()


def make_user(email, role="student", is_staff=False):
    return User.objects.create_user(
        email=email,
        password="testpass123",
        full_name="Test User",
        role=role,
        is_staff=is_staff,
    )


def make_instructor_profile(user):
    return InstructorProfile.objects.create(user=user)


def make_organization(user):
    return Organization.objects.create(
        name="Test Org",
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        organization_type=OrganizationType.COMPANY,
        created_by=user,
    )


def make_recruiter_profile(user, org):
    return RecruiterProfile.objects.create(user=user, organization=org)


def make_staff_user():
    staff = make_user("staff@tcareer.com", is_staff=True)
    group, _ = Group.objects.get_or_create(name="verification_staff")
    staff.groups.add(group)
    return staff


def make_fake_file(name="id.pdf", content_type="application/pdf", size=1024):
    f = MagicMock()
    f.name = name
    f.content_type = content_type
    f.size = size
    f.read = lambda: b"x" * size
    return f


class DocumentValidationTests(TestCase):

    def test_valid_pdf_passes(self):
        f = make_fake_file("doc.pdf", "application/pdf", 1024)
        try:
            validate_document(f, DocumentType.PASSPORT)
        except DocumentValidationError:
            self.fail("Valid PDF raised DocumentValidationError unexpectedly.")

    def test_invalid_mime_type_rejected(self):
        f = make_fake_file("script.exe", "application/octet-stream", 1024)
        with self.assertRaises(DocumentValidationError) as ctx:
            validate_document(f, DocumentType.PASSPORT)
        self.assertIn("not accepted", str(ctx.exception))

    def test_file_too_large_rejected(self):
        f = make_fake_file("large.pdf", "application/pdf", 201 * 1024 * 1024)
        with self.assertRaises(DocumentValidationError) as ctx:
            validate_document(f, DocumentType.PASSPORT)
        self.assertIn("exceeds", str(ctx.exception))

    def test_empty_file_rejected(self):
        f = make_fake_file("empty.pdf", "application/pdf", 0)
        with self.assertRaises(DocumentValidationError):
            validate_document(f, DocumentType.PASSPORT)

    def test_invalid_document_type_rejected(self):
        f = make_fake_file("doc.pdf", "application/pdf", 1024)
        with self.assertRaises(DocumentValidationError) as ctx:
            validate_document(f, "unknown_type")
        self.assertIn("not supported", str(ctx.exception))

    def test_mp4_for_teaching_demo_passes(self):
        f = make_fake_file("demo.mp4", "video/mp4", 50 * 1024 * 1024)
        try:
            validate_document(f, DocumentType.TEACHING_DEMO)
        except DocumentValidationError:
            self.fail("Valid MP4 raised DocumentValidationError unexpectedly.")


class DocumentUploadAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = make_user("instructor@test.com", role="instructor")
        self.profile = make_instructor_profile(self.user)
        self.client.force_authenticate(user=self.user)

    @patch("apps.verification.services._get_s3_client")
    def test_upload_document_success(self, mock_s3):
        mock_client = MagicMock()
        mock_client.upload_fileobj = MagicMock()
        mock_s3.return_value = mock_client

        with self.settings(AWS_S3_VERIFICATION_BUCKET="test-bucket"):
            file_data = BytesIO(b"PDF content")
            file_data.name = "passport.pdf"
            response = self.client.post(
                "/api/v1/verification/upload/",
                {
                    "document_type": DocumentType.PASSPORT,
                    "owner_type": SubjectType.INSTRUCTOR,
                    "owner_id": str(self.profile.id),
                    "file": file_data,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertNotIn("s3_key", data["data"])
        self.assertNotIn("s3_bucket", data["data"])

    def test_upload_without_file_returns_400(self):
        response = self.client.post(
            "/api/v1/verification/upload/",
            {
                "document_type": DocumentType.PASSPORT,
                "owner_type": SubjectType.INSTRUCTOR,
                "owner_id": str(self.profile.id),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_for_other_user_profile_forbidden(self):
        other_user = make_user("other@test.com", role="instructor")
        other_profile = make_instructor_profile(other_user)

        with self.settings(AWS_S3_VERIFICATION_BUCKET="test-bucket"):
            file_data = BytesIO(b"PDF content")
            file_data.name = "passport.pdf"
            response = self.client.post(
                "/api/v1/verification/upload/",
                {
                    "document_type": DocumentType.PASSPORT,
                    "owner_type": SubjectType.INSTRUCTOR,
                    "owner_id": str(other_profile.id),
                    "file": file_data,
                },
                format="multipart",
            )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_upload_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/v1/verification/upload/", {}, format="multipart"
        )
        self.assertEqual(response.status_code, 401)


class SubmitVerificationTests(TestCase):

    def setUp(self):
        self.instructor_user = make_user("ins@test.com", role="instructor")
        self.profile = make_instructor_profile(self.instructor_user)

    def test_submit_for_review_creates_request(self):
        req = submit_for_review(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            submitted_by=self.instructor_user,
            applicant_notes="Please review my profile.",
        )
        self.assertIsNotNone(req.id)
        self.assertEqual(req.status, VerificationRequestStatus.SUBMITTED)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.SUBMITTED)

    def test_suspended_subject_cannot_submit(self):
        self.profile.verification_status = VerificationStatus.SUSPENDED
        self.profile.save()
        with self.assertRaises(PermissionError):
            submit_for_review(
                subject_type=SubjectType.INSTRUCTOR,
                subject_id=self.profile.id,
                submitted_by=self.instructor_user,
            )

    def test_submit_writes_audit_log(self):
        initial_count = VerificationAction.objects.count()
        submit_for_review(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            submitted_by=self.instructor_user,
        )
        self.assertEqual(VerificationAction.objects.count(), initial_count + 1)

    def test_submit_updates_trust_score(self):
        initial_score = self.profile.trust_score
        submit_for_review(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            submitted_by=self.instructor_user,
        )
        self.profile.refresh_from_db()
        self.assertGreater(self.profile.trust_score, initial_score)
        self.assertTrue(
            TrustScoreLog.objects.filter(subject_id=self.profile.id).exists()
        )


class StaffApprovalTests(TestCase):

    def setUp(self):
        self.staff = make_staff_user()
        self.instructor_user = make_user("ins2@test.com", role="instructor")
        self.profile = make_instructor_profile(self.instructor_user)
        self.req = submit_for_review(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            submitted_by=self.instructor_user,
        )

    def test_approve_sets_verified_status(self):
        approve_verification(
            request_id=self.req.id,
            staff_user=self.staff,
            reason="All documents verified.",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.VERIFIED)
        self.assertIsNotNone(self.profile.verified_at)
        self.assertEqual(self.profile.verified_by, self.staff)

    def test_approve_updates_trust_score(self):
        initial_score = self.profile.trust_score
        approve_verification(request_id=self.req.id, staff_user=self.staff)
        self.profile.refresh_from_db()
        self.assertGreater(self.profile.trust_score, initial_score)

    def test_approve_writes_audit_log(self):
        before = VerificationAction.objects.count()
        approve_verification(
            request_id=self.req.id,
            staff_user=self.staff,
            reason="Verified.",
        )
        self.assertEqual(VerificationAction.objects.count(), before + 1)
        action = VerificationAction.objects.latest("performed_at")
        self.assertEqual(action.new_status, VerificationStatus.VERIFIED)
        self.assertEqual(action.actor, self.staff)

    def test_audit_log_is_append_only(self):
        approve_verification(request_id=self.req.id, staff_user=self.staff)
        action = VerificationAction.objects.latest("performed_at")
        action.reason = "tampered"
        with self.assertRaises(ValueError):
            action.save()


class StaffRejectionTests(TestCase):

    def setUp(self):
        self.staff = make_staff_user()
        self.instructor_user = make_user("ins3@test.com", role="instructor")
        self.profile = make_instructor_profile(self.instructor_user)
        self.req = submit_for_review(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            submitted_by=self.instructor_user,
        )

    def test_reject_sets_rejected_status(self):
        reject_verification(
            request_id=self.req.id,
            staff_user=self.staff,
            reason="Identity document is expired.",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.REJECTED)
        self.assertEqual(self.profile.rejection_reason, "Identity document is expired.")

    def test_reject_without_reason_raises_error(self):
        with self.assertRaises(ValueError):
            reject_verification(
                request_id=self.req.id,
                staff_user=self.staff,
                reason="",
            )

    def test_reject_writes_audit_log(self):
        before = VerificationAction.objects.count()
        reject_verification(
            request_id=self.req.id,
            staff_user=self.staff,
            reason="Document unreadable.",
        )
        self.assertEqual(VerificationAction.objects.count(), before + 1)


class MoreInfoTests(TestCase):

    def setUp(self):
        self.staff = make_staff_user()
        self.instructor_user = make_user("ins4@test.com", role="instructor")
        self.profile = make_instructor_profile(self.instructor_user)
        self.req = submit_for_review(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            submitted_by=self.instructor_user,
        )

    def test_more_info_sets_correct_status(self):
        request_more_information(
            request_id=self.req.id,
            staff_user=self.staff,
            reviewer_notes="Please upload a clearer photo of your passport.",
        )
        self.profile.refresh_from_db()
        self.assertEqual(
            self.profile.verification_status, VerificationStatus.MORE_INFO_REQUIRED
        )

    def test_more_info_without_notes_raises_error(self):
        with self.assertRaises(ValueError):
            request_more_information(
                request_id=self.req.id,
                staff_user=self.staff,
                reviewer_notes="",
            )


class SuspensionTests(TestCase):

    def setUp(self):
        self.staff = make_staff_user()
        self.instructor_user = make_user("ins5@test.com", role="instructor")
        self.profile = make_instructor_profile(self.instructor_user)

    def test_suspend_sets_suspended_status(self):
        suspend_subject(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            staff_user=self.staff,
            reason="Multiple complaints received.",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.SUSPENDED)
        self.assertEqual(self.profile.suspension_reason, "Multiple complaints received.")

    def test_suspend_caps_trust_score(self):
        self.profile.trust_score = 80
        self.profile.verification_status = VerificationStatus.PENDING
        self.profile.save()
        suspend_subject(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            staff_user=self.staff,
            reason="Policy violation.",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.SUSPENDED)
        self.assertLessEqual(self.profile.trust_score, 20)

    def test_reinstate_from_suspended(self):
        self.profile.verification_status = VerificationStatus.SUSPENDED
        self.profile.save()
        reinstate_subject(
            subject_type=SubjectType.INSTRUCTOR,
            subject_id=self.profile.id,
            staff_user=self.staff,
            reason="Issue resolved.",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.VERIFIED)

    def test_reinstate_non_suspended_raises_error(self):
        with self.assertRaises(ValueError):
            reinstate_subject(
                subject_type=SubjectType.INSTRUCTOR,
                subject_id=self.profile.id,
                staff_user=self.staff,
            )

    def test_suspended_user_cannot_resubmit(self):
        self.profile.verification_status = VerificationStatus.SUSPENDED
        self.profile.save()
        with self.assertRaises(PermissionError):
            submit_for_review(
                subject_type=SubjectType.INSTRUCTOR,
                subject_id=self.profile.id,
                submitted_by=self.instructor_user,
            )


class SignedUrlPermissionTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.normal_user = make_user("normal@test.com")
        self.staff = make_staff_user()
        self.doc = IdentityVerificationDocument.objects.create(
            owner_type=SubjectType.INSTRUCTOR,
            owner_id=uuid.uuid4(),
            document_type=DocumentType.PASSPORT,
            s3_bucket="test-bucket",
            s3_key="verification/instructor/test/passport/abc.pdf",
            file_name="passport.pdf",
            file_size=1024,
            mime_type="application/pdf",
            is_encrypted=True,
            uploaded_by=self.normal_user,
        )

    def test_normal_user_cannot_get_signed_url(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(
            f"/api/v1/verification/staff/documents/{self.doc.id}/signed-url/"
        )
        self.assertEqual(response.status_code, 403)

    @patch("apps.verification.services._get_s3_client")
    def test_staff_can_get_signed_url(self, mock_s3):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.example.com/signed?token=abc"
        mock_s3.return_value = mock_client
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            f"/api/v1/verification/staff/documents/{self.doc.id}/signed-url/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["url"], "https://s3.example.com/signed?token=abc")
    @patch("apps.verification.services._get_s3_client")
    def test_signed_url_access_is_logged(self, mock_s3):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.example.com/signed?token=abc"
        mock_s3.return_value = mock_client
        before = VerificationAction.objects.count()
        self.client.force_authenticate(user=self.staff)
        self.client.get(
            f"/api/v1/verification/staff/documents/{self.doc.id}/signed-url/"
        )
        self.assertEqual(VerificationAction.objects.count(), before + 1)


class UnauthorizedAccessTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.normal_user = make_user("user@test.com")

    def test_normal_user_cannot_access_staff_queue(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get("/api/v1/verification/staff/queue/")
        self.assertEqual(response.status_code, 403)

    def test_normal_user_cannot_approve(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            f"/api/v1/verification/staff/queue/{uuid.uuid4()}/approve/",
            {"reason": "approved"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_normal_user_cannot_reject(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(
            f"/api/v1/verification/staff/queue/{uuid.uuid4()}/reject/",
            {"reason": "rejected"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_access_any_endpoint(self):
        response = self.client.get("/api/v1/verification/my-status/")
        self.assertEqual(response.status_code, 401)

    def test_normal_user_cannot_access_audit_log(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get("/api/v1/verification/staff/audit-log/")
        self.assertEqual(response.status_code, 403)

