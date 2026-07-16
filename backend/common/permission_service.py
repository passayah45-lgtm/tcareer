from apps.users.models import UserRole

PRIVILEGED_PLATFORM_ROLES = {
    UserRole.ADMIN,
    UserRole.PLATFORM_ADMIN,
    UserRole.SUPER_ADMIN,
}

ORGANIZATION_ADMIN_ROLES = {"company_admin", "university_admin", "platform_admin", "super_admin"}
RECRUITER_ROLES = {"recruiter", "company_admin"}
ENTERPRISE_REPORT_ROLES = ORGANIZATION_ADMIN_ROLES | {"report_viewer", "export_manager"}
ENTERPRISE_EXPORT_ROLES = ORGANIZATION_ADMIN_ROLES | {"export_manager"}


class PermissionService:
    @staticmethod
    def is_platform_admin(user) -> bool:
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role in PRIVILEGED_PLATFORM_ROLES)
        )

    @staticmethod
    def has_org_role(user, organization, roles: set[str]) -> bool:
        if not user or not user.is_authenticated or organization is None:
            return False
        return user.organization_memberships.filter(
            organization=organization,
            role__in=roles,
            status="active",
        ).exists()

    @staticmethod
    def can_manage_organization(user, organization) -> bool:
        if PermissionService.is_platform_admin(user):
            return True
        return PermissionService.has_org_role(
            user,
            organization,
            ORGANIZATION_ADMIN_ROLES,
        )

    @staticmethod
    def can_view_enterprise_reports(user, organization) -> bool:
        if PermissionService.is_platform_admin(user):
            return True
        return PermissionService.has_org_role(user, organization, ENTERPRISE_REPORT_ROLES)

    @staticmethod
    def can_create_enterprise_export(user, organization, export_type: str = "") -> bool:
        if PermissionService.is_platform_admin(user):
            return True
        if export_type == "audit_logs":
            return PermissionService.has_org_role(
                user, organization, {"export_manager", "platform_admin", "super_admin"}
            )
        return PermissionService.has_org_role(user, organization, ENTERPRISE_EXPORT_ROLES)

    @staticmethod
    def _active_membership(user, organization):
        if not user or not user.is_authenticated or organization is None:
            return None
        return user.organization_memberships.filter(
            organization=organization, status="active"
        ).first()

    @staticmethod
    def can_manage_department(user, department) -> bool:
        if PermissionService.can_manage_organization(user, department.organization):
            return True
        membership = PermissionService._active_membership(user, department.organization)
        return bool(
            membership
            and membership.role == "department_manager"
            and department.members.filter(
                membership=membership, role__in={"manager", "admin"}
            ).exists()
        )

    @staticmethod
    def can_manage_team(user, team) -> bool:
        if PermissionService.can_manage_organization(user, team.organization):
            return True
        membership = PermissionService._active_membership(user, team.organization)
        return bool(
            membership
            and membership.role == "team_manager"
            and team.members.filter(membership=membership, role__in={"manager", "admin"}).exists()
        )

    @staticmethod
    def can_manage_cohort(user, cohort) -> bool:
        if PermissionService.can_manage_organization(user, cohort.organization):
            return True
        membership = PermissionService._active_membership(user, cohort.organization)
        return bool(
            membership
            and membership.role == "cohort_manager"
            and cohort.members.filter(membership=membership, role__in={"manager", "admin"}).exists()
        )

    @staticmethod
    def can_view_organization(user, organization) -> bool:
        if (
            bool(user and user.is_authenticated)
            and getattr(organization, "created_by_id", None) == user.id
        ):
            return True
        if PermissionService.can_manage_organization(user, organization):
            return True
        return PermissionService.has_org_role(
            user,
            organization,
            {
                "student",
                "instructor",
                "mentor",
                "recruiter",
                "content_moderator",
                "finance_admin",
            },
        )

    @staticmethod
    def can_invite_organization_member(user, organization, role: str) -> bool:
        if PermissionService.is_platform_admin(user):
            return True
        if role in {"platform_admin", "super_admin"}:
            return False
        return PermissionService.can_manage_organization(user, organization)

    @staticmethod
    def can_manage_organization_membership(user, membership) -> bool:
        return PermissionService.can_manage_organization(user, membership.organization)

    @staticmethod
    def can_publish_course(user, course) -> bool:
        return PermissionService.is_platform_admin(user) or course.instructor_id == user.id

    @staticmethod
    def is_academic_admin(user) -> bool:
        return bool(
            user
            and user.is_authenticated
            and (
                user.is_superuser
                or user.role in {UserRole.ADMIN, UserRole.PLATFORM_ADMIN, UserRole.SUPER_ADMIN}
            )
        )

    @staticmethod
    def is_academic_reviewer(user) -> bool:
        if PermissionService.is_academic_admin(user):
            return True
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "academic_reviewer_profile", None)
        return bool(profile and profile.is_active)

    @staticmethod
    def can_assign_academic_review(user, course=None, organization=None) -> bool:
        if PermissionService.is_academic_admin(user):
            return True
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "academic_reviewer_profile", None)
        if not profile or not profile.is_active:
            return False
        if profile.reviewer_role == "lead_reviewer":
            if profile.organization_id and organization is not None:
                return profile.organization_id == getattr(organization, "id", None)
            return True
        return False

    @staticmethod
    def can_view_academic_assignment(user, assignment) -> bool:
        if PermissionService.is_academic_admin(user):
            return True
        if not user or not user.is_authenticated:
            return False
        if assignment.assigned_reviewer_id == user.id:
            return True
        if assignment.course_id and assignment.course.instructor_id == user.id:
            return True
        profile = getattr(user, "academic_reviewer_profile", None)
        if not profile or not profile.is_active:
            return False
        if profile.reviewer_role in {"lead_reviewer", "platform_academic_reviewer"}:
            if profile.organization_id and assignment.organization_id:
                return profile.organization_id == assignment.organization_id
            return profile.reviewer_role == "platform_academic_reviewer"
        return False

    @staticmethod
    def can_decide_academic_review(user, assignment) -> bool:
        if PermissionService.is_academic_admin(user):
            return True
        if not user or not user.is_authenticated:
            return False
        if assignment.course_id and assignment.course.instructor_id == user.id:
            return False
        return assignment.assigned_reviewer_id == user.id

    @staticmethod
    def can_access_lesson(user, lesson) -> bool:
        if PermissionService.is_platform_admin(user):
            return True
        course = lesson.course
        if course.instructor_id == user.id:
            return True
        if lesson.is_free_preview:
            return True
        return course.enrollments.filter(user=user, status="active").exists()

    @staticmethod
    def can_manage_job(user, job) -> bool:
        if PermissionService.is_platform_admin(user):
            return True
        if job.posted_by_id == user.id:
            return True
        organization = getattr(job, "organization", None)
        return PermissionService.has_org_role(user, organization, RECRUITER_ROLES)

    @staticmethod
    def can_publish_job(user, job) -> bool:
        return PermissionService.can_manage_job(user, job)

    @staticmethod
    def can_manage_application(user, application) -> bool:
        if PermissionService.is_platform_admin(user):
            return True
        if not user or not user.is_authenticated:
            return False
        if application.assigned_recruiter_id == user.id or application.hiring_manager_id == user.id:
            return True
        return PermissionService.has_org_role(user, application.organization, RECRUITER_ROLES)

    @staticmethod
    def can_view_application(user, application) -> bool:
        if PermissionService.can_manage_application(user, application):
            return True
        return bool(user and user.is_authenticated and application.candidate_id == user.id)

    @staticmethod
    def can_manage_interview(user, interview) -> bool:
        return PermissionService.can_manage_application(user, interview.application)

    @staticmethod
    def can_manage_company_profile(user, organization) -> bool:
        return PermissionService.can_manage_organization(user, organization)

    @staticmethod
    def can_view_private_user_asset(user, owner) -> bool:
        return bool(user and user.is_authenticated) and (
            PermissionService.is_platform_admin(user) or user.id == owner.id
        )

    @staticmethod
    def can_manage_portfolio(user, portfolio) -> bool:
        return PermissionService.can_view_private_user_asset(user, portfolio.user)

    @staticmethod
    def can_view_portfolio(user, portfolio) -> bool:
        if getattr(portfolio, "is_visible_publicly", False):
            return True
        return PermissionService.can_manage_portfolio(user, portfolio)

    @staticmethod
    def can_manage_resume(user, resume) -> bool:
        return PermissionService.can_view_private_user_asset(user, resume.user)

    @staticmethod
    def can_view_certificate(user, certificate) -> bool:
        if not getattr(certificate, "is_revoked", False):
            return True
        return PermissionService.can_view_private_user_asset(user, certificate.user)

    @staticmethod
    def can_manage_certificate(user, certificate) -> bool:
        return PermissionService.is_platform_admin(user) or (
            bool(user and user.is_authenticated)
            and getattr(certificate.course, "instructor_id", None) == user.id
        )

    @staticmethod
    def can_manage_verification(user) -> bool:
        return bool(
            user
            and user.is_authenticated
            and (
                user.role
                in {
                    UserRole.ADMIN,
                    UserRole.CONTENT_MODERATOR,
                    UserRole.PLATFORM_ADMIN,
                    UserRole.SUPER_ADMIN,
                }
                or user.is_superuser
            )
        )

    @staticmethod
    def can_view_verification_record(user, verification_record) -> bool:
        if PermissionService.can_manage_verification(user):
            return True
        return bool(
            user
            and user.is_authenticated
            and getattr(verification_record, "submitted_by_id", None) == user.id
        )

    @staticmethod
    def can_manage_payment(user, payment_subject) -> bool:
        owner = getattr(payment_subject, "user", None)
        return PermissionService.is_platform_admin(user) or (
            owner is not None and user and user.is_authenticated and owner.id == user.id
        )

    @staticmethod
    def can_manage_entitlement(user, entitlement_subject) -> bool:
        return PermissionService.can_manage_payment(user, entitlement_subject)
