import logging
from datetime import date, timedelta
from typing import Optional

from django.conf import settings
from django.utils import timezone

from apps.profiles.models import VerificationStatus
from apps.verification.models import (
    DocumentType,
    IdentityVerificationDocument,
    SubjectType,
    VerificationAction,
    VerificationActionType,
    VerificationPriority,
    VerificationRequest,
    VerificationRequestStatus,
)
from apps.trust.models import TrustChangeReason, TrustSubjectType
from apps.trust.services import apply_trust_event
from common.audit import AuditService
from common.uploads import UploadValidationService

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "video/mp4",
}

ALLOWED_DOCUMENT_TYPES = {dt.value for dt in DocumentType}
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024
SIGNED_URL_EXPIRY_SECONDS = getattr(settings, "VERIFICATION_SIGNED_URL_EXPIRY", 900)


def extract_request_context(request) -> dict:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR", "")
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    return {
        "ip_address": ip[:45],
        "browser": user_agent[:200],
        "device": _parse_device(user_agent),
        "country": "",
        "city": "",
    }


def _parse_device(user_agent: str) -> str:
    ua = user_agent.lower()
    if "mobile" in ua or "android" in ua:
        return "mobile"
    if "tablet" in ua or "ipad" in ua:
        return "tablet"
    return "desktop"


def _get_s3_client():
    import boto3

    return boto3.client(
        "s3",
        region_name=getattr(settings, "AWS_REGION", "us-east-1"),
        aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", ""),
    )


def _get_verification_bucket() -> str:
    bucket = getattr(settings, "AWS_S3_VERIFICATION_BUCKET", "")
    if not bucket:
        raise ValueError("AWS_S3_VERIFICATION_BUCKET is not configured.")
    return bucket


class DocumentValidationError(Exception):
    pass


def validate_document(file, document_type: str) -> None:
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise DocumentValidationError(
            f"Document type '{document_type}' is not supported. "
            f"Allowed types: {', '.join(ALLOWED_DOCUMENT_TYPES)}"
        )
    try:
        UploadValidationService.validate_metadata(
            file_name=file.name,
            content_type=getattr(file, "content_type", ""),
            file_size=file.size,
            allowed_extensions={".pdf", ".png", ".jpg", ".jpeg", ".webp", ".mp4"},
            allowed_mime_types=ALLOWED_MIME_TYPES,
            max_size_bytes=MAX_FILE_SIZE_BYTES,
        )
    except Exception as exc:
        raise DocumentValidationError(str(exc)) from exc
    if file.size == 0:
        raise DocumentValidationError("The uploaded file is empty.")


def upload_verification_document(
    *,
    owner_type: str,
    owner_id,
    document_type: str,
    file,
    uploaded_by,
    expires_at: Optional[date] = None,
) -> IdentityVerificationDocument:
    validate_document(file, document_type)

    import uuid as uuid_lib
    unique_key = str(uuid_lib.uuid4())
    s3_key = f"verification/{owner_type}/{owner_id}/{document_type}/{unique_key}/{file.name}"
    bucket = _get_verification_bucket()

    try:
        s3 = _get_s3_client()
        s3.upload_fileobj(
            file,
            bucket,
            s3_key,
            ExtraArgs={
                "ContentType": file.content_type,
                "ServerSideEncryption": "AES256",
            },
        )
    except Exception as exc:
        logger.error("S3 upload failed for %s/%s: %s", owner_type, owner_id, exc)
        raise RuntimeError("Document upload failed. Please try again.") from exc

    IdentityVerificationDocument.objects.filter(
        owner_type=owner_type,
        owner_id=owner_id,
        document_type=document_type,
        is_active=True,
    ).update(is_active=False)

    doc = IdentityVerificationDocument.objects.create(
        owner_type=owner_type,
        owner_id=owner_id,
        document_type=document_type,
        s3_bucket=bucket,
        s3_key=s3_key,
        file_name=file.name,
        file_size=file.size,
        mime_type=file.content_type,
        is_encrypted=True,
        uploaded_by=uploaded_by,
        expires_at=expires_at,
        is_active=True,
    )

    logger.info(
        "Document uploaded: type=%s owner=%s/%s doc_id=%s",
        document_type, owner_type, owner_id, doc.id,
    )
    return doc


def generate_signed_document_url(
    *,
    document_id,
    requesting_user,
    request=None,
) -> str:
    is_staff = (
        requesting_user.is_staff
        or requesting_user.groups.filter(name="verification_staff").exists()
    )
    if not is_staff:
        raise PermissionError("Only verification staff may access document URLs.")

    doc = IdentityVerificationDocument.objects.get(id=document_id, is_active=True)

    try:
        s3 = _get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": doc.s3_bucket, "Key": doc.s3_key},
            ExpiresIn=SIGNED_URL_EXPIRY_SECONDS,
        )
    except Exception as exc:
        logger.error("Signed URL generation failed for doc %s: %s", document_id, exc)
        raise RuntimeError("Could not generate document access URL.") from exc

    ctx = extract_request_context(request) if request else {}
    VerificationAction.objects.create(
        actor=requesting_user,
        target_type=doc.owner_type,
        target_id=doc.owner_id,
        action=VerificationActionType.SIGNED_URL_GENERATED,
        notes=f"Document ID: {doc.id} | Type: {doc.document_type}",
        **ctx,
    )

    return url


def _get_subject(subject_type: str, subject_id):
    if subject_type == SubjectType.INSTRUCTOR:
        from apps.profiles.models import InstructorProfile
        return InstructorProfile.objects.get(id=subject_id)
    if subject_type == SubjectType.RECRUITER:
        from apps.profiles.models import RecruiterProfile
        return RecruiterProfile.objects.get(id=subject_id)
    if subject_type == SubjectType.ORGANIZATION:
        from apps.profiles.models import Organization
        return Organization.objects.get(id=subject_id)
    raise ValueError(f"Unknown subject_type: {subject_type}")


def _subject_type_to_trust_type(subject_type: str) -> str:
    mapping = {
        SubjectType.INSTRUCTOR: TrustSubjectType.INSTRUCTOR,
        SubjectType.RECRUITER: TrustSubjectType.RECRUITER,
        SubjectType.ORGANIZATION: TrustSubjectType.ORGANIZATION,
    }
    return mapping.get(subject_type, "")


def _write_audit(
    *,
    actor,
    target_type: str,
    target_id,
    action: str,
    previous_status: str = "",
    new_status: str = "",
    reason: str = "",
    notes: str = "",
    request=None,
) -> None:
    ctx = extract_request_context(request) if request else {}
    performed_at = timezone.now()
    previous_action = (
        VerificationAction.objects.filter(target_type=target_type, target_id=target_id)
        .order_by("-performed_at")
        .first()
    )
    if previous_action and previous_action.performed_at >= performed_at:
        performed_at = previous_action.performed_at + timedelta(microseconds=1)
    VerificationAction.objects.create(
        actor=actor,
        target_type=target_type,
        target_id=target_id,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        notes=notes,
        performed_at=performed_at,
        **ctx,
    )


def _update_subject_status(subject, new_status: str, extra_fields: dict = None) -> str:
    previous = subject.verification_status
    subject.verification_status = new_status
    fields = ["verification_status"]
    if extra_fields:
        for field, value in extra_fields.items():
            setattr(subject, field, value)
            fields.append(field)
    subject.save(update_fields=fields)
    return previous


def submit_for_review(
    *,
    subject_type: str,
    subject_id,
    submitted_by,
    applicant_notes: str = "",
    request=None,
) -> VerificationRequest:
    subject = _get_subject(subject_type, subject_id)

    if subject.verification_status == VerificationStatus.SUSPENDED:
        raise PermissionError(
            "This account is suspended. Contact T-Career support to request reinstatement."
        )

    priority, priority_reason = _calculate_priority(subject_type, subject_id)

    req, created = VerificationRequest.objects.get_or_create(
        subject_type=subject_type,
        subject_id=subject_id,
        status__in=[
            VerificationRequestStatus.SUBMITTED,
            VerificationRequestStatus.MORE_INFO_REQUIRED,
        ],
        defaults={
            "submitted_by": submitted_by,
            "status": VerificationRequestStatus.SUBMITTED,
            "priority": priority,
            "priority_reason": priority_reason,
            "applicant_notes": applicant_notes,
        },
    )

    if not created:
        req.status = VerificationRequestStatus.SUBMITTED
        req.applicant_notes = applicant_notes
        req.priority = priority
        req.priority_reason = priority_reason
        req.save(update_fields=["status", "applicant_notes", "priority", "priority_reason"])

    previous = _update_subject_status(subject, VerificationStatus.SUBMITTED)

    _write_audit(
        actor=submitted_by,
        target_type=subject_type,
        target_id=subject_id,
        action=VerificationActionType.SUBMITTED,
        previous_status=previous,
        new_status=VerificationStatus.SUBMITTED,
        notes=applicant_notes,
        request=request,
    )
    AuditService.record(
        actor=submitted_by,
        action="verification_submitted",
        target=req,
        request=request,
        metadata={"subject_type": req.subject_type, "subject_id": str(req.subject_id)},
    )

    trust_type = _subject_type_to_trust_type(subject_type)
    if trust_type:
        apply_trust_event(
            subject_type=trust_type,
            subject_id=subject_id,
            change_reason=TrustChangeReason.IDENTITY_SUBMITTED,
        )

    return req


def assign_reviewer(*, request_id, staff_user, request=None) -> VerificationRequest:
    req = VerificationRequest.objects.get(id=request_id)
    req.assigned_to = staff_user
    req.status = VerificationRequestStatus.UNDER_REVIEW
    req.save(update_fields=["assigned_to", "status"])

    subject = _get_subject(req.subject_type, req.subject_id)
    previous = _update_subject_status(subject, VerificationStatus.UNDER_REVIEW)

    _write_audit(
        actor=staff_user,
        target_type=req.subject_type,
        target_id=req.subject_id,
        action=VerificationActionType.ASSIGNED,
        previous_status=previous,
        new_status=VerificationStatus.UNDER_REVIEW,
        notes=f"Assigned to {staff_user.email}",
        request=request,
    )
    return req


def approve_verification(
    *,
    request_id,
    staff_user,
    reason: str = "",
    internal_notes: str = "",
    reviewer_notes: str = "",
    request=None,
) -> VerificationRequest:
    req = VerificationRequest.objects.get(id=request_id)
    req.status = VerificationRequestStatus.APPROVED
    req.reviewed_at = timezone.now()
    req.internal_notes = internal_notes
    req.reviewer_notes = reviewer_notes
    req.save(update_fields=["status", "reviewed_at", "internal_notes", "reviewer_notes"])

    subject = _get_subject(req.subject_type, req.subject_id)
    previous = _update_subject_status(
        subject,
        VerificationStatus.VERIFIED,
        extra_fields={"verified_at": timezone.now(), "verified_by": staff_user},
    )

    if req.subject_type == SubjectType.RECRUITER:
        subject.can_post_jobs = True
        subject.can_contact_students = True
        subject.save(update_fields=["can_post_jobs", "can_contact_students"])

    _write_audit(
        actor=staff_user,
        target_type=req.subject_type,
        target_id=req.subject_id,
        action=VerificationActionType.APPROVED,
        previous_status=previous,
        new_status=VerificationStatus.VERIFIED,
        reason=reason,
        notes=internal_notes,
        request=request,
    )
    AuditService.record(
        actor=staff_user,
        action="verification_approved",
        target=req,
        request=request,
        metadata={"subject_type": req.subject_type, "subject_id": str(req.subject_id), "reason": reason},
    )

    trust_type = _subject_type_to_trust_type(req.subject_type)
    if trust_type:
        apply_trust_event(
            subject_type=trust_type,
            subject_id=req.subject_id,
            change_reason=TrustChangeReason.IDENTITY_VERIFIED,
            actor=staff_user,
        )

    _send_verification_notification(
        subject_type=req.subject_type,
        subject_id=req.subject_id,
        action="approved",
        reviewer_notes=reviewer_notes,
    )
    return req


def reject_verification(
    *,
    request_id,
    staff_user,
    reason: str,
    internal_notes: str = "",
    reviewer_notes: str = "",
    request=None,
) -> VerificationRequest:
    if not reason.strip():
        raise ValueError("A rejection reason is required.")

    req = VerificationRequest.objects.get(id=request_id)
    req.status = VerificationRequestStatus.REJECTED
    req.reviewed_at = timezone.now()
    req.internal_notes = internal_notes
    req.reviewer_notes = reviewer_notes
    req.save(update_fields=["status", "reviewed_at", "internal_notes", "reviewer_notes"])

    subject = _get_subject(req.subject_type, req.subject_id)
    previous = _update_subject_status(
        subject,
        VerificationStatus.REJECTED,
        extra_fields={"rejection_reason": reason},
    )

    _write_audit(
        actor=staff_user,
        target_type=req.subject_type,
        target_id=req.subject_id,
        action=VerificationActionType.REJECTED,
        previous_status=previous,
        new_status=VerificationStatus.REJECTED,
        reason=reason,
        notes=internal_notes,
        request=request,
    )
    AuditService.record(
        actor=staff_user,
        action="verification_rejected",
        target=req,
        request=request,
        metadata={"subject_type": req.subject_type, "subject_id": str(req.subject_id), "reason": reason},
    )

    _send_verification_notification(
        subject_type=req.subject_type,
        subject_id=req.subject_id,
        action="rejected",
        reviewer_notes=reviewer_notes,
    )
    return req


def request_more_information(
    *,
    request_id,
    staff_user,
    reviewer_notes: str,
    internal_notes: str = "",
    request=None,
) -> VerificationRequest:
    if not reviewer_notes.strip():
        raise ValueError("You must specify what additional information is required.")

    req = VerificationRequest.objects.get(id=request_id)
    req.status = VerificationRequestStatus.MORE_INFO_REQUIRED
    req.reviewer_notes = reviewer_notes
    req.internal_notes = internal_notes
    req.save(update_fields=["status", "reviewer_notes", "internal_notes"])

    subject = _get_subject(req.subject_type, req.subject_id)
    previous = _update_subject_status(subject, VerificationStatus.MORE_INFO_REQUIRED)

    _write_audit(
        actor=staff_user,
        target_type=req.subject_type,
        target_id=req.subject_id,
        action=VerificationActionType.MORE_INFO_REQUESTED,
        previous_status=previous,
        new_status=VerificationStatus.MORE_INFO_REQUIRED,
        notes=reviewer_notes,
        request=request,
    )

    _send_verification_notification(
        subject_type=req.subject_type,
        subject_id=req.subject_id,
        action="more_info_required",
        reviewer_notes=reviewer_notes,
    )
    return req


def suspend_subject(
    *,
    subject_type: str,
    subject_id,
    staff_user,
    reason: str,
    internal_notes: str = "",
    request=None,
) -> None:
    if not reason.strip():
        raise ValueError("A suspension reason is required.")

    subject = _get_subject(subject_type, subject_id)
    previous = _update_subject_status(
        subject,
        VerificationStatus.SUSPENDED,
        extra_fields={"suspension_reason": reason},
    )

    if subject_type == SubjectType.RECRUITER:
        subject.can_post_jobs = False
        subject.can_contact_students = False
        subject.save(update_fields=["can_post_jobs", "can_contact_students"])

    _write_audit(
        actor=staff_user,
        target_type=subject_type,
        target_id=subject_id,
        action=VerificationActionType.SUSPENDED,
        previous_status=previous,
        new_status=VerificationStatus.SUSPENDED,
        reason=reason,
        notes=internal_notes,
        request=request,
    )

    trust_type = _subject_type_to_trust_type(subject_type)
    if trust_type:
        apply_trust_event(
            subject_type=trust_type,
            subject_id=subject_id,
            change_reason=TrustChangeReason.SUSPENDED,
            actor=staff_user,
            notes=reason,
        )

    _send_verification_notification(
        subject_type=subject_type,
        subject_id=subject_id,
        action="suspended",
        reviewer_notes=reason,
    )


def reinstate_subject(
    *,
    subject_type: str,
    subject_id,
    staff_user,
    reason: str = "",
    internal_notes: str = "",
    request=None,
) -> None:
    subject = _get_subject(subject_type, subject_id)

    if subject.verification_status != VerificationStatus.SUSPENDED:
        raise ValueError("Only suspended subjects can be reinstated.")

    previous = _update_subject_status(
        subject,
        VerificationStatus.VERIFIED,
        extra_fields={"suspension_reason": ""},
    )

    _write_audit(
        actor=staff_user,
        target_type=subject_type,
        target_id=subject_id,
        action=VerificationActionType.REINSTATED,
        previous_status=previous,
        new_status=VerificationStatus.VERIFIED,
        reason=reason,
        notes=internal_notes,
        request=request,
    )

    _send_verification_notification(
        subject_type=subject_type,
        subject_id=subject_id,
        action="reinstated",
        reviewer_notes=reason,
    )


def _calculate_priority(subject_type: str, subject_id) -> tuple:
    try:
        subject = _get_subject(subject_type, subject_id)
    except Exception:
        return VerificationPriority.NORMAL, ""

    if subject_type == SubjectType.ORGANIZATION:
        if getattr(subject, "organization_type", "") in ("university", "government"):
            return VerificationPriority.HIGH, "university_or_government"

    if subject_type == SubjectType.INSTRUCTOR:
        if getattr(subject, "courses_published", 0) > 0:
            return VerificationPriority.HIGH, "active_instructor"

    return VerificationPriority.NORMAL, ""


def _send_verification_notification(
    *,
    subject_type: str,
    subject_id,
    action: str,
    reviewer_notes: str = "",
) -> None:
    logger.info(
        "Verification notification: subject=%s/%s action=%s",
        subject_type, subject_id, action,
    )
