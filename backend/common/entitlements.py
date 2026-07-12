from django.utils import timezone

from apps.organizations.models import CandidateProfileUnlock, OrganizationRole


class EntitlementService:
    @staticmethod
    def get_recruiter_entitlement(organization):
        if organization is None:
            return None
        return getattr(organization, "recruiter_entitlement", None)

    @staticmethod
    def has_active_recruiter_entitlement(organization) -> bool:
        entitlement = EntitlementService.get_recruiter_entitlement(organization)
        if entitlement is None:
            return False
        now = timezone.now()
        if entitlement.starts_at and entitlement.starts_at > now:
            return False
        if entitlement.ends_at and entitlement.ends_at <= now:
            return False
        return True

    @staticmethod
    def active_recruiter_seats(organization) -> int:
        if organization is None:
            return 0
        return organization.memberships.filter(
            role=OrganizationRole.RECRUITER,
            status="active",
        ).count()

    @staticmethod
    def max_recruiter_seats(organization) -> int:
        entitlement = EntitlementService.get_recruiter_entitlement(organization)
        return entitlement.max_recruiter_seats if entitlement else 0

    @staticmethod
    def can_invite_recruiter(actor, organization) -> bool:
        if not EntitlementService.has_active_recruiter_entitlement(organization):
            return bool(actor and getattr(actor, "is_staff", False))
        entitlement = EntitlementService.get_recruiter_entitlement(organization)
        return EntitlementService.active_recruiter_seats(organization) < entitlement.max_recruiter_seats

    @staticmethod
    def has_active_subscription(user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return user.subscriptions.filter(
            status__in=["active", "trialing"],
            current_period_end__gt=timezone.now(),
        ).exists()

    @staticmethod
    def can_access_course(user, course) -> bool:
        if not user or not user.is_authenticated:
            return False
        if course.instructor_id == user.id:
            return True
        if course.is_free:
            return True
        if course.enrollments.filter(user=user, status="active").exists():
            return True
        return EntitlementService.has_active_subscription(user)

    @staticmethod
    def can_use_ai_tutor(user, course=None) -> bool:
        if not user or not user.is_authenticated:
            return False
        return EntitlementService.has_active_subscription(user) or (
            course is not None and course.enrollments.filter(user=user, status="active").exists()
        )

    @staticmethod
    def can_download_certificate(user, certificate) -> bool:
        return bool(
            user
            and user.is_authenticated
            and not certificate.is_revoked
            and (certificate.user_id == user.id or user.is_staff)
        )

    @staticmethod
    def can_recruiter_post_jobs(user) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.role in {"recruiter", "company_admin", "admin", "platform_admin", "super_admin"}:
            return True
        return user.organization_memberships.filter(
            role__in=["recruiter", "company_admin"],
            status="active",
        ).exists()

    @staticmethod
    def can_post_job(user, organization=None) -> bool:
        if not user or not user.is_authenticated:
            return False
        if organization is not None:
            if not EntitlementService.has_active_recruiter_entitlement(organization):
                return bool(user.is_staff)
            entitlement = EntitlementService.get_recruiter_entitlement(organization)
            if not entitlement.can_post_jobs:
                return False
            return user.organization_memberships.filter(
                organization=organization,
                role__in=["recruiter", "company_admin", "platform_admin", "super_admin"],
                status="active",
            ).exists() or user.is_staff
        return EntitlementService.can_recruiter_post_jobs(user)

    @staticmethod
    def can_recruiter_search_candidates(user) -> bool:
        return EntitlementService.can_recruiter_post_jobs(user)

    @staticmethod
    def can_search_candidates(user, organization=None) -> bool:
        if organization is None:
            return EntitlementService.can_recruiter_search_candidates(user)
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if not EntitlementService.has_active_recruiter_entitlement(organization):
            return False
        entitlement = EntitlementService.get_recruiter_entitlement(organization)
        if not entitlement.can_search_candidates:
            return False
        return user.organization_memberships.filter(
            organization=organization,
            role__in=["recruiter", "company_admin"],
            status="active",
        ).exists()

    @staticmethod
    def can_view_candidate_profile(user, candidate, organization=None) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.id == candidate.id or user.is_staff:
            return True
        if organization is None:
            return False
        if not EntitlementService.can_search_candidates(user, organization=organization):
            return False
        if not EntitlementService.has_active_recruiter_entitlement(organization):
            return False
        entitlement = EntitlementService.get_recruiter_entitlement(organization)
        if not entitlement.can_view_candidate_profiles:
            return False
        if CandidateProfileUnlock.objects.filter(organization=organization, candidate=candidate).exists():
            return True
        from common.privacy import PrivacyService

        return PrivacyService.public_profile_enabled(candidate)

    @staticmethod
    def can_organization_access_reports(user, organization) -> bool:
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.organization_memberships.filter(
            organization=organization,
            role__in=["company_admin", "university_admin", "finance_admin"],
            status="active",
        ).exists()

    @staticmethod
    def can_access_organization_reports(user, organization) -> bool:
        return EntitlementService.can_organization_access_reports(user, organization)

    @staticmethod
    def can_use_premium_resume_analysis(user) -> bool:
        return EntitlementService.has_active_subscription(user)

    @staticmethod
    def can_use_resume_analysis(user) -> bool:
        return EntitlementService.has_active_subscription(user)

    @staticmethod
    def can_use_portfolio_analysis(user) -> bool:
        return EntitlementService.has_active_subscription(user)
