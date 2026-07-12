from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permission_service import PermissionService


def _count(model, **filters):
    return model.objects.filter(**filters).count() if filters else model.objects.count()


def _recent(model, limit=6, **filters):
    queryset = model.objects.filter(**filters) if filters else model.objects.all()
    return queryset.order_by("-created_at")[:limit]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_management_dashboard(request):
    if not PermissionService.is_platform_admin(request.user):
        return Response({"detail": "Platform management access is required."}, status=status.HTTP_403_FORBIDDEN)

    from apps.ai_platform.models import AIProvider, AIRequest, AIRequestStatus, AITokenUsage
    from apps.analytics.models import AnalyticsEvent
    from apps.audit.models import AuditLog
    from apps.careers.models import CareerResume, Portfolio
    from apps.certificates.models import Certificate
    from apps.courses.models import Course, CourseStatus, Enrollment, EnrollmentStatus, Lesson
    from apps.jobs.models import JobApplication, JobListing, RecruiterWaitlist
    from apps.notifications.models import EmailDelivery, Notification
    from apps.organizations.models import (
        BulkImportJob,
        DataExportJob,
        Organization,
        OrganizationInvitation,
        OrganizationMembership,
        OrganizationRecruiterEntitlement,
        OrganizationStatus,
    )
    from apps.payments.models import Subscription, SubscriptionStatus
    from apps.users.models import User, UserRole
    from apps.verification.models import VerificationRequest, VerificationRequestStatus

    since = timezone.now() - timedelta(days=7)
    ai_cost = AITokenUsage.objects.aggregate(total=Sum("estimated_cost"))["total"] or 0
    data = {
        "summary": {
            "users": _count(User),
            "active_users": _count(User, is_active=True),
            "students": _count(User, role=UserRole.STUDENT),
            "instructors": _count(User, role=UserRole.INSTRUCTOR),
            "recruiters": _count(User, role=UserRole.RECRUITER),
            "organizations": _count(Organization),
            "published_courses": _count(Course, status=CourseStatus.PUBLISHED, deleted_at__isnull=True),
            "active_jobs": _count(JobListing, is_active=True),
            "pending_verifications": _count(
                VerificationRequest,
                status__in=[
                    VerificationRequestStatus.SUBMITTED,
                    VerificationRequestStatus.UNDER_REVIEW,
                    VerificationRequestStatus.MORE_INFO_REQUIRED,
                ],
            ),
            "ai_requests_7d": _count(AIRequest, created_at__gte=since),
        },
        "learning": {
            "courses": _count(Course, deleted_at__isnull=True),
            "draft_courses": _count(Course, status=CourseStatus.DRAFT, deleted_at__isnull=True),
            "published_courses": _count(Course, status=CourseStatus.PUBLISHED, deleted_at__isnull=True),
            "archived_courses": _count(Course, status=CourseStatus.ARCHIVED),
            "lessons": _count(Lesson, deleted_at__isnull=True),
            "published_lessons": _count(Lesson, is_published=True, deleted_at__isnull=True),
            "active_enrollments": _count(Enrollment, status=EnrollmentStatus.ACTIVE),
            "completed_enrollments": _count(Enrollment, status=EnrollmentStatus.COMPLETED),
            "certificates": _count(Certificate, is_revoked=False),
            "revoked_certificates": _count(Certificate, is_revoked=True),
        },
        "career": {
            "portfolios": _count(Portfolio),
            "public_portfolios": _count(Portfolio, visibility="public"),
            "resumes": _count(CareerResume, is_archived=False),
            "jobs": _count(JobListing),
            "active_jobs": _count(JobListing, is_active=True),
            "applications": _count(JobApplication),
            "applications_by_stage": dict(
                JobApplication.objects.values("stage").annotate(count=Count("id")).values_list("stage", "count")
            ),
            "recruiter_waitlist": _count(RecruiterWaitlist),
        },
        "organizations": {
            "total": _count(Organization),
            "active": _count(Organization, status=OrganizationStatus.ACTIVE),
            "pending": _count(Organization, status=OrganizationStatus.PENDING),
            "suspended": _count(Organization, status=OrganizationStatus.SUSPENDED),
            "memberships": _count(OrganizationMembership, status="active"),
            "pending_invitations": _count(OrganizationInvitation, accepted_at__isnull=True, revoked_at__isnull=True),
            "recruiter_entitlements": _count(OrganizationRecruiterEntitlement),
            "exports_queued": _count(DataExportJob, status="queued"),
            "imports_processing": _count(BulkImportJob, status__in=["validating", "processing"]),
        },
        "trust": {
            "verification_requests": _count(VerificationRequest),
            "submitted": _count(VerificationRequest, status=VerificationRequestStatus.SUBMITTED),
            "under_review": _count(VerificationRequest, status=VerificationRequestStatus.UNDER_REVIEW),
            "approved": _count(VerificationRequest, status=VerificationRequestStatus.APPROVED),
            "rejected": _count(VerificationRequest, status=VerificationRequestStatus.REJECTED),
            "audit_events_7d": _count(AuditLog, created_at__gte=since),
            "analytics_events_7d": _count(AnalyticsEvent, occurred_at__gte=since),
        },
        "ai": {
            "providers": _count(AIProvider),
            "active_providers": _count(AIProvider, is_active=True),
            "requests": _count(AIRequest),
            "requests_7d": _count(AIRequest, created_at__gte=since),
            "failed_requests_7d": _count(AIRequest, created_at__gte=since, status=AIRequestStatus.FAILED),
            "blocked_requests_7d": _count(AIRequest, created_at__gte=since, status=AIRequestStatus.BLOCKED),
            "estimated_cost": str(ai_cost),
        },
        "notifications": {
            "notifications": _count(Notification),
            "unread": _count(Notification, is_read=False),
            "email_pending": _count(EmailDelivery, status="pending"),
            "email_failed": _count(EmailDelivery, status="failed"),
            "email_retrying": _count(EmailDelivery, status="retrying"),
        },
        "revenue": {
            "subscriptions": _count(Subscription),
            "active_subscriptions": _count(Subscription, status=SubscriptionStatus.ACTIVE),
            "past_due": _count(Subscription, status=SubscriptionStatus.PAST_DUE),
            "cancelled": _count(Subscription, status=SubscriptionStatus.CANCELLED),
        },
        "sections": [
            {"label": "Learner operations", "href": "/dashboard", "description": "Student progress, profiles, resumes, applications, interviews, and recommendations."},
            {"label": "Instructor operations", "href": "/instructor/dashboard", "description": "Course publishing, lessons, assessments, certificates, and instructor content quality."},
            {"label": "Recruiter operations", "href": "/recruiter/dashboard", "description": "Jobs, applications, candidate search, interviews, talent pools, and recruiter entitlements."},
            {"label": "Organization console", "href": "/organization/dashboard", "description": "Universities, companies, cohorts, departments, teams, imports, exports, and enterprise analytics."},
            {"label": "AI operations", "href": "/ai/admin", "description": "AI providers, model configuration, usage, budgets, evaluations, and safety controls."},
            {"label": "Notifications", "href": "/settings/notifications", "description": "In-app and email-ready notification preferences and delivery operations."},
            {"label": "Trust and verification", "href": "/platform/verification", "description": "Instructor, recruiter, and organization verification queues."},
            {"label": "Operations queues", "href": "/platform/operations", "description": "Access, organization lifecycle, course moderation, email delivery, and audit queues."},
        ],
        "recent_activity": [
            {
                "id": str(item.id),
                "action": item.action,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "created_at": item.created_at,
            }
            for item in _recent(AuditLog, 8)
        ],
    }
    return Response(data)
