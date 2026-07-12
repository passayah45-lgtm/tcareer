from datetime import timedelta

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.audit import AuditService
from common.permission_service import PermissionService


SENSITIVE_ACTIONS = {
    ("users", "deactivate"),
    ("organizations", "suspend"),
    ("organizations", "archive"),
    ("courses", "archive"),
    ("email", "cancel"),
    ("verification", "reject"),
    ("verification", "more_info"),
}


def _require_platform_admin(user):
    return bool(PermissionService.is_platform_admin(user))


def _reason_from_request(request, *, required: bool = False) -> str:
    reason = str(request.data.get("reason") or "").strip()
    if required and len(reason) < 10:
        raise ValueError("A reason of at least 10 characters is required for this admin action.")
    return reason


def _user_item(user):
    return {
        "id": str(user.id),
        "label": user.full_name or user.email,
        "subtitle": user.email,
        "status": "active" if user.is_active else "inactive",
        "metadata": {
            "role": user.role,
            "verified": user.is_verified,
            "email_verified": user.is_email_verified,
        },
        "created_at": user.created_at,
    }


def _organization_item(organization):
    return {
        "id": str(organization.id),
        "label": organization.name,
        "subtitle": organization.organization_type,
        "status": organization.status,
        "metadata": {
            "country": organization.country_code,
            "website": organization.website_url,
        },
        "created_at": organization.created_at,
    }


def _course_item(course):
    return {
        "id": str(course.id),
        "label": course.title,
        "subtitle": getattr(course.instructor, "email", ""),
        "status": course.status,
        "metadata": {
            "slug": course.slug,
            "level": course.level,
            "lessons": course.lessons.filter(deleted_at__isnull=True).count(),
        },
        "created_at": course.created_at,
    }


def _verification_item(verification):
    return {
        "id": str(verification.id),
        "label": f"{verification.subject_type} verification",
        "subtitle": str(verification.subject_id),
        "status": verification.status,
        "metadata": {
            "priority": verification.priority,
            "submitted_by": getattr(verification.submitted_by, "email", ""),
            "assigned_to": getattr(verification.assigned_to, "email", ""),
        },
        "created_at": verification.submitted_at,
    }


def _email_item(delivery):
    return {
        "id": str(delivery.id),
        "label": delivery.subject,
        "subtitle": delivery.recipient_email,
        "status": delivery.status,
        "metadata": {
            "template": delivery.template_key,
            "category": delivery.category,
            "retry_count": delivery.retry_count,
            "last_error": delivery.last_error[:240],
        },
        "created_at": delivery.created_at,
    }


def _audit_item(log):
    return {
        "id": str(log.id),
        "label": log.action,
        "subtitle": f"{log.target_type}:{log.target_id}" if log.target_type else "system",
        "status": "recorded",
        "metadata": {
            "actor": getattr(log.actor, "email", ""),
            "organization_id": str(log.organization_id or ""),
        },
        "created_at": log.created_at,
    }


def _audit_log_response(log):
    return {
        "id": str(log.id),
        "actor_email": getattr(log.actor, "email", ""),
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "organization_id": str(log.organization_id or ""),
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "metadata": log.metadata or {},
        "created_at": log.created_at,
    }


def _verification_detail_response(verification):
    from apps.verification.models import VerificationAction
    from apps.verification.serializers import VerificationActionSerializer, VerificationRequestDetailSerializer

    actions = VerificationAction.objects.select_related("actor").filter(
        target_type=verification.subject_type,
        target_id=verification.subject_id,
    ).order_by("-performed_at", "-created_at")[:100]
    return {
        "request": VerificationRequestDetailSerializer(verification).data,
        "actions": VerificationActionSerializer(actions, many=True).data,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_operations(request):
    if not _require_platform_admin(request.user):
        return Response({"detail": "Platform operations access is required."}, status=status.HTTP_403_FORBIDDEN)

    from apps.audit.models import AuditLog
    from apps.courses.models import Course, CourseStatus
    from apps.notifications.models import EmailDelivery, EmailDeliveryStatus
    from apps.organizations.models import Organization, OrganizationStatus
    from apps.users.models import User
    from apps.verification.models import VerificationRequest, VerificationRequestStatus

    limit = min(max(int(request.query_params.get("limit", 8)), 1), 25)
    pending_verification_statuses = [
        VerificationRequestStatus.SUBMITTED,
        VerificationRequestStatus.UNDER_REVIEW,
        VerificationRequestStatus.MORE_INFO_REQUIRED,
    ]
    email_attention_statuses = [
        EmailDeliveryStatus.PENDING,
        EmailDeliveryStatus.QUEUED,
        EmailDeliveryStatus.FAILED,
        EmailDeliveryStatus.RETRYING,
    ]

    queues = {
        "users": {
            "label": "User access",
            "description": "Recently created accounts and accounts needing activation review.",
            "items": [
                _user_item(user)
                for user in User.objects.order_by("-created_at")[:limit]
            ],
        },
        "organizations": {
            "label": "Organization approvals",
            "description": "Pending, suspended, and recently created organizations.",
            "items": [
                _organization_item(organization)
                for organization in Organization.objects.filter(
                    status__in=[OrganizationStatus.PENDING, OrganizationStatus.SUSPENDED]
                ).order_by("status", "-created_at")[:limit]
            ],
        },
        "courses": {
            "label": "Course moderation",
            "description": "Recently published courses available for platform review.",
            "items": [
                _course_item(course)
                for course in Course.objects.select_related("instructor")
                .filter(status=CourseStatus.PUBLISHED, deleted_at__isnull=True)
                .order_by("-created_at")[:limit]
            ],
        },
        "verification": {
            "label": "Verification review",
            "description": "Identity, instructor, recruiter, and organization verification requests.",
            "items": [
                _verification_item(verification)
                for verification in VerificationRequest.objects.select_related("submitted_by", "assigned_to")
                .filter(status__in=pending_verification_statuses)
                .order_by("-priority", "submitted_at")[:limit]
            ],
        },
        "email": {
            "label": "Email delivery operations",
            "description": "Pending, failed, and retrying email deliveries.",
            "items": [
                _email_item(delivery)
                for delivery in EmailDelivery.objects.select_related("recipient")
                .filter(status__in=email_attention_statuses)
                .order_by("status", "created_at")[:limit]
            ],
        },
        "audit": {
            "label": "Audit search",
            "description": "Recent privileged actions and security-sensitive platform events.",
            "items": [
                _audit_item(log)
                for log in AuditLog.objects.select_related("actor").order_by("-created_at")[:limit]
            ],
        },
    }
    counts = {
        "inactive_users": User.objects.filter(is_active=False).count(),
        "pending_organizations": Organization.objects.filter(status=OrganizationStatus.PENDING).count(),
        "published_courses": Course.objects.filter(status=CourseStatus.PUBLISHED, deleted_at__isnull=True).count(),
        "pending_verifications": VerificationRequest.objects.filter(status__in=pending_verification_statuses).count(),
        "email_attention": EmailDelivery.objects.filter(status__in=email_attention_statuses).count(),
        "audit_events_24h": AuditLog.objects.filter(created_at__gte=timezone.now() - timedelta(hours=24)).count(),
    }
    return Response({"counts": counts, "queues": queues})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def platform_operation_action(request, resource, object_id, action):
    if not _require_platform_admin(request.user):
        return Response({"detail": "Platform operations access is required."}, status=status.HTTP_403_FORBIDDEN)

    try:
        if (resource, action) in SENSITIVE_ACTIONS:
            _reason_from_request(request, required=True)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if resource == "users":
        return _user_action(request, object_id, action)
    if resource == "organizations":
        return _organization_action(request, object_id, action)
    if resource == "courses":
        return _course_action(request, object_id, action)
    if resource == "verification":
        return _verification_action(request, object_id, action)
    if resource == "email":
        return _email_action(request, object_id, action)
    return Response({"detail": "Unsupported platform operation resource."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_verification_queue(request):
    if not _require_platform_admin(request.user):
        return Response({"detail": "Platform verification access is required."}, status=status.HTTP_403_FORBIDDEN)

    from apps.verification.models import VerificationRequest, VerificationRequestStatus

    queryset = VerificationRequest.objects.select_related("submitted_by", "assigned_to").order_by("-priority", "submitted_at")
    status_filter = request.query_params.get("status", "").strip()
    subject_type = request.query_params.get("subject_type", "").strip()
    priority = request.query_params.get("priority", "").strip()
    assigned = request.query_params.get("assigned", "").strip()
    query = request.query_params.get("q", "").strip()

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    else:
        queryset = queryset.filter(
            status__in=[
                VerificationRequestStatus.SUBMITTED,
                VerificationRequestStatus.UNDER_REVIEW,
                VerificationRequestStatus.MORE_INFO_REQUIRED,
            ]
        )
    if subject_type:
        queryset = queryset.filter(subject_type=subject_type)
    if priority:
        queryset = queryset.filter(priority=priority)
    if assigned == "me":
        queryset = queryset.filter(assigned_to=request.user)
    elif assigned == "unassigned":
        queryset = queryset.filter(assigned_to__isnull=True)
    if query:
        queryset = queryset.filter(
            Q(subject_type__icontains=query)
            | Q(status__icontains=query)
            | Q(priority__icontains=query)
            | Q(priority_reason__icontains=query)
            | Q(submitted_by__email__icontains=query)
            | Q(assigned_to__email__icontains=query)
        )

    limit = min(max(int(request.query_params.get("limit", 50)), 1), 100)
    counts = dict(VerificationRequest.objects.values_list("status").annotate(count=Count("id")))
    total = queryset.count()
    return Response(
        {
            "total": total,
            "counts": counts,
            "results": [_verification_item(verification) for verification in queryset[:limit]],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_verification_detail(request, request_id):
    if not _require_platform_admin(request.user):
        return Response({"detail": "Platform verification access is required."}, status=status.HTTP_403_FORBIDDEN)

    from apps.verification.models import VerificationRequest

    verification = get_object_or_404(
        VerificationRequest.objects.select_related("submitted_by", "assigned_to"),
        id=request_id,
    )
    return Response(_verification_detail_response(verification))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def platform_verification_action(request, request_id, action):
    if not _require_platform_admin(request.user):
        return Response({"detail": "Platform verification access is required."}, status=status.HTTP_403_FORBIDDEN)
    try:
        if action in {"reject", "more_info"}:
            _reason_from_request(request, required=True)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return _verification_action(request, request_id, action)


def _user_action(request, object_id, action):
    from apps.users.models import User

    user = get_object_or_404(User, id=object_id)
    if user.id == request.user.id and action == "deactivate":
        return Response({"detail": "You cannot deactivate your own account."}, status=status.HTTP_400_BAD_REQUEST)
    if action not in {"activate", "deactivate"}:
        return Response({"detail": "Unsupported user action."}, status=status.HTTP_400_BAD_REQUEST)
    next_active = action == "activate"
    previous = user.is_active
    reason = _reason_from_request(request)
    user.is_active = next_active
    user.save(update_fields=["is_active", "updated_at"])
    AuditService.record(
        actor=request.user,
        action=f"platform_user_{action}",
        target=user,
        request=request,
        metadata={"previous_is_active": previous, "next_is_active": next_active, "reason": reason},
    )
    return Response({"item": _user_item(user)})


def _organization_action(request, object_id, action):
    from apps.organizations.models import Organization
    from apps.organizations.services import EnterpriseOrganizationService

    organization = get_object_or_404(Organization, id=object_id)
    lifecycle_action = {"activate": "reactivate", "suspend": "suspend", "archive": "archive"}.get(action)
    if not lifecycle_action:
        return Response({"detail": "Unsupported organization action."}, status=status.HTTP_400_BAD_REQUEST)
    reason = _reason_from_request(request)
    organization = EnterpriseOrganizationService.lifecycle_transition(
        actor=request.user,
        organization=organization,
        action=lifecycle_action,
        metadata=request.data.get("metadata") or {"source": "platform_operations", "reason": reason},
    )
    return Response({"item": _organization_item(organization)})


def _course_action(request, object_id, action):
    from apps.courses.models import Course, CourseStatus

    course = get_object_or_404(Course.objects.select_related("instructor"), id=object_id)
    if action != "archive":
        return Response({"detail": "Unsupported course action."}, status=status.HTTP_400_BAD_REQUEST)
    previous = course.status
    reason = _reason_from_request(request)
    course.status = CourseStatus.ARCHIVED
    course.save(update_fields=["status", "updated_at"])
    AuditService.record(
        actor=request.user,
        action="platform_course_archived",
        target=course,
        request=request,
        metadata={"previous_status": previous, "next_status": course.status, "reason": reason},
    )
    return Response({"item": _course_item(course)})


def _verification_action(request, object_id, action):
    from apps.verification.models import VerificationRequest
    from apps.verification.services import (
        approve_verification,
        assign_reviewer,
        reject_verification,
        request_more_information,
    )

    verification = get_object_or_404(VerificationRequest, id=object_id)
    reason = _reason_from_request(request)
    internal_notes = str(request.data.get("internal_notes") or reason or "").strip()
    reviewer_notes = str(request.data.get("reviewer_notes") or reason or "").strip()
    try:
        if action == "assign":
            verification = assign_reviewer(request_id=verification.id, staff_user=request.user, request=request)
        elif action == "approve":
            verification = approve_verification(
                request_id=verification.id,
                staff_user=request.user,
                reason=reason,
                reviewer_notes=reviewer_notes,
                internal_notes=internal_notes,
                request=request,
            )
        elif action == "reject":
            verification = reject_verification(
                request_id=verification.id,
                staff_user=request.user,
                reason=reason,
                reviewer_notes=reviewer_notes,
                internal_notes=internal_notes,
                request=request,
            )
        elif action == "more_info":
            verification = request_more_information(
                request_id=verification.id,
                staff_user=request.user,
                reviewer_notes=reviewer_notes,
                internal_notes=internal_notes,
                request=request,
            )
        else:
            return Response({"detail": "Unsupported verification action."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    AuditService.record(
        actor=request.user,
        action=f"platform_verification_{action}",
        target=verification,
        request=request,
        metadata={"reason": reason, "subject_type": verification.subject_type, "subject_id": str(verification.subject_id)},
    )
    return Response({"item": _verification_item(verification)})


def _email_action(request, object_id, action):
    from apps.notifications.models import EmailDelivery, EmailDeliveryService, EmailDeliveryStatus

    delivery = get_object_or_404(EmailDelivery.objects.select_related("recipient"), id=object_id)
    if action == "retry":
        delivery = EmailDeliveryService.send_email_delivery(delivery.id)
        audit_action = "platform_email_retry"
    elif action == "cancel":
        reason = _reason_from_request(request)
        if delivery.status == EmailDeliveryStatus.SENT:
            return Response({"detail": "Sent email deliveries cannot be cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        delivery.status = EmailDeliveryStatus.CANCELLED
        delivery.last_error = f"Cancelled by platform admin: {reason}"
        delivery.save(update_fields=["status", "last_error", "updated_at"])
        audit_action = "platform_email_cancelled"
    else:
        return Response({"detail": "Unsupported email action."}, status=status.HTTP_400_BAD_REQUEST)
    AuditService.record(
        actor=request.user,
        action=audit_action,
        target=delivery,
        request=request,
        metadata={"recipient_email": delivery.recipient_email, "status": delivery.status, "reason": request.data.get("reason", "")},
    )
    return Response({"item": _email_item(delivery)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_audit_search(request):
    if not _require_platform_admin(request.user):
        return Response({"detail": "Platform audit access is required."}, status=status.HTTP_403_FORBIDDEN)

    from apps.audit.models import AuditLog

    queryset = AuditLog.objects.select_related("actor").order_by("-created_at")
    action = request.query_params.get("action", "").strip()
    target_type = request.query_params.get("target_type", "").strip()
    target_id = request.query_params.get("target_id", "").strip()
    actor = request.query_params.get("actor", "").strip()
    query = request.query_params.get("q", "").strip()
    if action:
        queryset = queryset.filter(action__icontains=action)
    if target_type:
        queryset = queryset.filter(target_type__icontains=target_type)
    if target_id:
        queryset = queryset.filter(target_id__icontains=target_id)
    if actor:
        queryset = queryset.filter(actor_id=actor)
    if query:
        queryset = queryset.filter(
            Q(action__icontains=query) | Q(target_type__icontains=query) | Q(target_id__icontains=query)
        )
    limit = min(max(int(request.query_params.get("limit", 50)), 1), 200)
    total = queryset.count()
    return Response({"total": total, "results": [_audit_log_response(log) for log in queryset[:limit]]})
