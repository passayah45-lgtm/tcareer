from dataclasses import dataclass

from apps.organizations.models import CandidateProfileUnlock
from common.entitlements import EntitlementService
from common.permission_service import PermissionService
from common.privacy import PrivacyService


@dataclass(frozen=True)
class CandidateVisibility:
    can_view_profile: bool
    can_view_resume: bool
    can_view_portfolio: bool
    can_contact: bool
    is_unlocked: bool
    is_admin_override: bool


class CandidateVisibilityService:
    @staticmethod
    def is_admin(user) -> bool:
        return bool(
            user
            and getattr(user, "is_authenticated", False)
            and (
                getattr(user, "is_staff", False)
                or getattr(user, "is_superuser", False)
                or getattr(user, "role", "") in {"admin", "platform_admin", "super_admin"}
            )
        )

    @staticmethod
    def is_owner(user, candidate) -> bool:
        return bool(user and candidate and getattr(user, "id", None) == getattr(candidate, "id", None))

    @staticmethod
    def is_unlocked(organization, candidate) -> bool:
        if organization is None or candidate is None:
            return False
        return CandidateProfileUnlock.objects.filter(organization=organization, candidate=candidate).exists()

    @staticmethod
    def can_access_organization(user, organization) -> bool:
        if organization is None:
            return False
        if CandidateVisibilityService.is_admin(user):
            return True
        return PermissionService.can_view_organization(user, organization) and EntitlementService.can_search_candidates(
            user,
            organization=organization,
        )

    @staticmethod
    def can_view_profile(user, candidate, organization=None) -> bool:
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if CandidateVisibilityService.is_owner(user, candidate) or CandidateVisibilityService.is_admin(user):
            return True
        if not CandidateVisibilityService.can_access_organization(user, organization):
            return False
        if not EntitlementService.has_active_recruiter_entitlement(organization):
            return False
        entitlement = EntitlementService.get_recruiter_entitlement(organization)
        if not entitlement or not entitlement.can_view_candidate_profiles:
            return False
        if CandidateVisibilityService.is_unlocked(organization, candidate):
            return True
        return PrivacyService.public_profile_enabled(candidate)

    @staticmethod
    def can_unlock_candidate(user, candidate, organization) -> bool:
        if CandidateVisibilityService.is_admin(user):
            return True
        if not PrivacyService.public_profile_enabled(candidate):
            return False
        return CandidateVisibilityService.can_view_profile(user, candidate, organization=organization)

    @staticmethod
    def can_view_resume(user, candidate, organization=None) -> bool:
        if CandidateVisibilityService.is_owner(user, candidate) or CandidateVisibilityService.is_admin(user):
            return True
        return (
            PrivacyService.recruiter_resume_visible(candidate)
            and CandidateVisibilityService.is_unlocked(organization, candidate)
            and CandidateVisibilityService.can_view_profile(user, candidate, organization=organization)
        )

    @staticmethod
    def can_view_portfolio(user, candidate, organization=None) -> bool:
        if CandidateVisibilityService.is_owner(user, candidate) or CandidateVisibilityService.is_admin(user):
            return True
        return PrivacyService.recruiter_portfolio_visible(candidate) and CandidateVisibilityService.can_view_profile(
            user,
            candidate,
            organization=organization,
        )

    @staticmethod
    def can_contact(user, candidate, organization=None) -> bool:
        if CandidateVisibilityService.is_owner(user, candidate) or CandidateVisibilityService.is_admin(user):
            return True
        return PrivacyService.allow_recruiter_contact(candidate) and CandidateVisibilityService.can_view_profile(
            user,
            candidate,
            organization=organization,
        )

    @staticmethod
    def evaluate(user, candidate, organization=None) -> CandidateVisibility:
        unlocked = CandidateVisibilityService.is_unlocked(organization, candidate)
        admin = CandidateVisibilityService.is_admin(user)
        return CandidateVisibility(
            can_view_profile=CandidateVisibilityService.can_view_profile(user, candidate, organization=organization),
            can_view_resume=CandidateVisibilityService.can_view_resume(user, candidate, organization=organization),
            can_view_portfolio=CandidateVisibilityService.can_view_portfolio(user, candidate, organization=organization),
            can_contact=CandidateVisibilityService.can_contact(user, candidate, organization=organization),
            is_unlocked=unlocked,
            is_admin_override=admin,
        )

    @staticmethod
    def evaluate_search_result(user, candidate, organization=None, is_unlocked: bool = False) -> CandidateVisibility:
        admin = CandidateVisibilityService.is_admin(user)
        can_view_profile = admin or is_unlocked or PrivacyService.public_profile_enabled(candidate)
        can_view_profile = can_view_profile and (
            admin
            or CandidateVisibilityService.is_owner(user, candidate)
            or CandidateVisibilityService.can_access_organization(user, organization)
        )
        return CandidateVisibility(
            can_view_profile=can_view_profile,
            can_view_resume=can_view_profile
            and (admin or (is_unlocked and PrivacyService.recruiter_resume_visible(candidate))),
            can_view_portfolio=can_view_profile and (admin or PrivacyService.recruiter_portfolio_visible(candidate)),
            can_contact=can_view_profile and (admin or PrivacyService.allow_recruiter_contact(candidate)),
            is_unlocked=is_unlocked,
            is_admin_override=admin,
        )

    @staticmethod
    def visible_candidate_filter():
        from django.db import models

        return models.Q(user__privacy_settings__public_profile=True) | models.Q(
            user__privacy_settings__isnull=True,
            user__is_public_profile=True,
        )
