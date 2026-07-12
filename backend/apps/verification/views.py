import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    IdentityVerificationDocument,
    SubjectType,
    VerificationAction,
    VerificationRequest,
    VerificationRequestStatus,
)
from .permissions import IsVerificationStaff
from .serializers import (
    DocumentUploadSerializer,
    IdentityVerificationDocumentSerializer,
    StaffApproveSerializer,
    StaffMoreInfoSerializer,
    StaffReinstateSerializer,
    StaffRejectSerializer,
    StaffSuspendSerializer,
    SubmitVerificationSerializer,
    VerificationActionSerializer,
    VerificationRequestDetailSerializer,
    VerificationRequestSerializer,
)
from .services import (
    approve_verification,
    assign_reviewer,
    generate_signed_document_url,
    reject_verification,
    reinstate_subject,
    request_more_information,
    submit_for_review,
    suspend_subject,
    upload_verification_document,
    DocumentValidationError,
)

logger = logging.getLogger(__name__)


# ── Document upload ────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    # Users upload their own verification documents.
    # They cannot upload documents for other users.
    # Staff can upload on behalf of any subject.

    serializer = DocumentUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    file = request.FILES.get("file")
    if not file:
        return Response(
            {"success": False, "errors": {"file": ["No file was uploaded."]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data
    owner_id = data["owner_id"]
    owner_type = data["owner_type"]

    # Verify ownership unless staff
    is_staff = request.user.is_staff or request.user.groups.filter(name="verification_staff").exists()
    if not is_staff:
        if not _owns_subject(request.user, owner_type, owner_id):
            return Response(
                {"success": False, "errors": {"detail": "You can only upload documents for your own profile."}},
                status=status.HTTP_403_FORBIDDEN,
            )

    try:
        doc = upload_verification_document(
            owner_type=owner_type,
            owner_id=owner_id,
            document_type=data["document_type"],
            file=file,
            uploaded_by=request.user,
            expires_at=data.get("expires_at"),
        )
    except DocumentValidationError as exc:
        return Response(
            {"success": False, "errors": {"file": [str(exc)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except (ValueError, RuntimeError) as exc:
        logger.error("Document upload error: %s", exc)
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"success": True, "data": IdentityVerificationDocumentSerializer(doc).data},
        status=status.HTTP_201_CREATED,
    )


# ── Submit verification request ────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_verification(request):
    serializer = SubmitVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data
    is_staff = request.user.is_staff or request.user.groups.filter(name="verification_staff").exists()

    if not is_staff:
        if not _owns_subject(request.user, data["subject_type"], data["subject_id"]):
            return Response(
                {"success": False, "errors": {"detail": "You can only submit verification for your own profile."}},
                status=status.HTTP_403_FORBIDDEN,
            )

    try:
        req = submit_for_review(
            subject_type=data["subject_type"],
            subject_id=data["subject_id"],
            submitted_by=request.user,
            applicant_notes=data.get("applicant_notes", ""),
            request=request,
        )
    except PermissionError as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_403_FORBIDDEN,
        )
    except Exception as exc:
        logger.error("Submit verification error: %s", exc)
        return Response(
            {"success": False, "errors": {"detail": "Verification submission failed."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"success": True, "data": VerificationRequestSerializer(req).data},
        status=status.HTTP_201_CREATED,
    )


# ── My verification status ─────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_verification_status(request):
    # Returns the verification status for all profiles owned by the current user.

    result = {}

    try:
        instructor = request.user.instructor_profile
        result["instructor"] = {
            "status": instructor.verification_status,
            "trust_score": instructor.trust_score,
        }
    except Exception:
        pass

    try:
        recruiter = request.user.recruiter_profile
        result["recruiter"] = {
            "status": recruiter.verification_status,
            "organization": str(recruiter.organization_id),
            "can_post_jobs": recruiter.can_post_jobs,
            "trust_score": recruiter.trust_score,
        }
    except Exception:
        pass

    try:
        learner = request.user.learner_profile
        result["learner"] = {
            "trust_score": learner.trust_score,
        }
    except Exception:
        pass

    return Response({"success": True, "data": result})


# ── Staff: verification queue ──────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsVerificationStaff])
def staff_verification_queue(request):
    # Returns verification requests filtered by status and priority.
    # Supports ?status=submitted&priority=high&subject_type=instructor

    qs = VerificationRequest.objects.select_related("submitted_by", "assigned_to")

    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    else:
        qs = qs.exclude(status__in=[
            VerificationRequestStatus.APPROVED,
            VerificationRequestStatus.REJECTED,
        ])

    priority_filter = request.query_params.get("priority")
    if priority_filter:
        qs = qs.filter(priority=priority_filter)

    subject_type_filter = request.query_params.get("subject_type")
    if subject_type_filter:
        qs = qs.filter(subject_type=subject_type_filter)

    assigned_to_me = request.query_params.get("assigned_to_me")
    if assigned_to_me == "true":
        qs = qs.filter(assigned_to=request.user)

    qs = qs.order_by("-priority", "submitted_at")

    serializer = VerificationRequestSerializer(qs, many=True)
    return Response({"success": True, "data": serializer.data})


# ── Staff: verification detail ─────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsVerificationStaff])
def staff_verification_detail(request, request_id):
    req = get_object_or_404(VerificationRequest, id=request_id)
    serializer = VerificationRequestDetailSerializer(req)
    return Response({"success": True, "data": serializer.data})


# ── Staff: assign reviewer ─────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsVerificationStaff])
def staff_assign(request, request_id):
    try:
        req = assign_reviewer(
            request_id=request_id,
            staff_user=request.user,
            request=request,
        )
    except Exception as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"success": True, "data": VerificationRequestSerializer(req).data})


# ── Staff: approve ─────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsVerificationStaff])
def staff_approve(request, request_id):
    serializer = StaffApproveSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        req = approve_verification(
            request_id=request_id,
            staff_user=request.user,
            request=request,
            **serializer.validated_data,
        )
    except Exception as exc:
        logger.error("Approve error: %s", exc)
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"success": True, "data": VerificationRequestSerializer(req).data})


# ── Staff: reject ──────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsVerificationStaff])
def staff_reject(request, request_id):
    serializer = StaffRejectSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        req = reject_verification(
            request_id=request_id,
            staff_user=request.user,
            request=request,
            **serializer.validated_data,
        )
    except Exception as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"success": True, "data": VerificationRequestSerializer(req).data})


# ── Staff: request more info ───────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsVerificationStaff])
def staff_more_info(request, request_id):
    serializer = StaffMoreInfoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        req = request_more_information(
            request_id=request_id,
            staff_user=request.user,
            request=request,
            **serializer.validated_data,
        )
    except Exception as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"success": True, "data": VerificationRequestSerializer(req).data})


# ── Staff: suspend ─────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsVerificationStaff])
def staff_suspend(request, subject_type, subject_id):
    serializer = StaffSuspendSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        suspend_subject(
            subject_type=subject_type,
            subject_id=subject_id,
            staff_user=request.user,
            request=request,
            **serializer.validated_data,
        )
    except ValueError as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"success": True, "data": {"message": "Subject suspended."}})


# ── Staff: reinstate ───────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsVerificationStaff])
def staff_reinstate(request, subject_type, subject_id):
    serializer = StaffReinstateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        reinstate_subject(
            subject_type=subject_type,
            subject_id=subject_id,
            staff_user=request.user,
            request=request,
            **serializer.validated_data,
        )
    except ValueError as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"success": True, "data": {"message": "Subject reinstated."}})


# ── Staff: signed document URL ─────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsVerificationStaff])
def staff_signed_document_url(request, document_id):
    try:
        url = generate_signed_document_url(
            document_id=document_id,
            requesting_user=request.user,
            request=request,
        )
    except IdentityVerificationDocument.DoesNotExist:
        return Response(
            {"success": False, "errors": {"detail": "Document not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    except PermissionError as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_403_FORBIDDEN,
        )
    except RuntimeError as exc:
        return Response(
            {"success": False, "errors": {"detail": str(exc)}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({
        "url": url,
        "expires_in_seconds": 900,
        "warning": "This URL expires in 15 minutes. Do not share it.",
    })


# ── Staff: audit log 

@api_view(["GET"])
@permission_classes([IsVerificationStaff])
def staff_audit_log(request):
    qs = VerificationAction.objects.select_related("actor").order_by("-performed_at")

    target_type = request.query_params.get("target_type")
    if target_type:
        qs = qs.filter(target_type=target_type)

    target_id = request.query_params.get("target_id")
    if target_id:
        qs = qs.filter(target_id=target_id)

    action_filter = request.query_params.get("action")
    if action_filter:
        qs = qs.filter(action=action_filter)

    qs = qs[:200]
    serializer = VerificationActionSerializer(qs, many=True)
    return Response({"success": True, "data": serializer.data})


#  Helper 

def _owns_subject(user, subject_type: str, subject_id) -> bool:
    # Checks if the user owns the given subject profile.
    try:
        if subject_type == SubjectType.INSTRUCTOR:
            return str(user.instructor_profile.id) == str(subject_id)
        if subject_type == SubjectType.RECRUITER:
            return str(user.recruiter_profile.id) == str(subject_id)
        if subject_type == SubjectType.ORGANIZATION:
            from apps.profiles.models import Organization
            return Organization.objects.filter(id=subject_id, created_by=user).exists()
    except Exception:
        return False
    return False
