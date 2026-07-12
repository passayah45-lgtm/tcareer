import hashlib
import csv
import io
import secrets
import zipfile
from html import escape
from datetime import timedelta

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from PIL import Image
from rest_framework import serializers

from apps.audit.models import AuditLog
from apps.careers.models import Portfolio, PortfolioSkill, SkillSource
from apps.certificates.models import Certificate
from apps.courses.models import Course, CourseStatus, Enrollment, EnrollmentStatus
from apps.jobs.models import ApplicationStage, Interview, JobApplication, JobListing, SavedCandidate
from apps.organizations.models import (
    BulkImportJob,
    BulkImportType,
    Cohort,
    CohortMember,
    DataExportJob,
    Department,
    DepartmentMember,
    EnterpriseRole,
    EnterpriseWorkerStatus,
    EnterpriseReportJob,
    MembershipStatus,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationPolicy,
    OrganizationProfile,
    OrganizationRole,
    OrganizationTeam,
    TeamMember,
)
from common.audit import AuditService
from common.exceptions import PermissionError
from common.entitlements import EntitlementService
from common.permission_service import PermissionService
from apps.analytics.services import AnalyticsService
from apps.notifications.models import NotificationService, NotificationType
from apps.users.models import User


PRIVILEGED_ORG_ROLES = {
    OrganizationRole.COMPANY_ADMIN,
    OrganizationRole.UNIVERSITY_ADMIN,
    OrganizationRole.CONTENT_MODERATOR,
    OrganizationRole.FINANCE_ADMIN,
    OrganizationRole.PLATFORM_ADMIN,
    OrganizationRole.SUPER_ADMIN,
}


class OrganizationService:
    @staticmethod
    @transaction.atomic
    def create_organization(*, actor, name: str, organization_type: str, website_url: str = "", country_code: str = ""):
        organization = Organization.objects.create(
            name=name,
            organization_type=organization_type,
            website_url=website_url,
            country_code=country_code.upper(),
            created_by=actor,
            owner=actor,
        )
        AuditService.record(
            actor=actor,
            action="organization_created",
            target=organization,
            organization=organization,
            metadata={"organization_type": organization_type},
        )
        return organization

    @staticmethod
    def _ensure_can_grant_role(*, actor, target_user, organization: Organization, role: str) -> None:
        if role in {OrganizationRole.PLATFORM_ADMIN, OrganizationRole.SUPER_ADMIN} and not PermissionService.is_platform_admin(actor):
            raise PermissionError("Only platform admins can grant platform-level organization roles.")
        if role in PRIVILEGED_ORG_ROLES and not PermissionService.can_manage_organization(actor, organization):
            raise PermissionError("You cannot grant privileged organization roles.")
        if actor == target_user and role != OrganizationRole.STUDENT:
            raise PermissionError("Users cannot grant themselves privileged roles.")

    @staticmethod
    @transaction.atomic
    def add_member(*, actor, organization: Organization, user, role: str) -> OrganizationMembership:
        OrganizationService._ensure_can_grant_role(
            actor=actor,
            target_user=user,
            organization=organization,
            role=role,
        )

        membership, _ = OrganizationMembership.objects.update_or_create(
            organization=organization,
            user=user,
            role=role,
            defaults={"status": MembershipStatus.ACTIVE, "invited_by": actor},
        )
        AuditService.record(
            actor=actor,
            action="organization_member_added",
            target=membership,
            organization=organization,
            metadata={"member_user_id": str(user.id), "role": role},
        )
        return membership

    @staticmethod
    @transaction.atomic
    def invite_member(
        *,
        actor,
        organization: Organization,
        email: str,
        role: str,
        expires_in_days: int = 7,
    ) -> tuple[OrganizationInvitation, str]:
        if not PermissionService.can_invite_organization_member(actor, organization, role):
            raise PermissionError("You cannot invite members with this role.")
        if role == OrganizationRole.RECRUITER and not EntitlementService.can_invite_recruiter(actor, organization):
            raise PermissionError("This organization has no available recruiter seats.")

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        invitation = OrganizationInvitation.objects.create(
            organization=organization,
            email=email.lower().strip(),
            role=role,
            invited_by=actor,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(days=expires_in_days),
        )
        AuditService.record(
            actor=actor,
            action="organization_member_invited",
            target=invitation,
            organization=organization,
            metadata={"email": invitation.email, "role": role},
        )
        if role == OrganizationRole.RECRUITER:
            invited_user = User.objects.filter(email=invitation.email).first()
            if invited_user:
                NotificationService.notify(
                    recipient=invited_user,
                    notification_type=NotificationType.RECRUITER_INVITED,
                    title="Recruiter invitation",
                    body=f"You were invited to recruit for {organization.name}.",
                    action_url="/login",
                    payload={"organization_id": str(organization.id), "invitation_id": str(invitation.id)},
                )
        return invitation, raw_token

    @staticmethod
    @transaction.atomic
    def accept_invitation(*, actor, token: str) -> OrganizationMembership:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        try:
            invitation = OrganizationInvitation.objects.select_related("organization").get(
                token_hash=token_hash
            )
        except OrganizationInvitation.DoesNotExist as exc:
            raise PermissionError("Invitation token is invalid.") from exc

        if invitation.revoked_at or invitation.accepted_at:
            raise PermissionError("Invitation token has already been used.")
        if invitation.expires_at <= timezone.now():
            raise PermissionError("Invitation token has expired.")
        if actor.email.lower() != invitation.email.lower() and not PermissionService.is_platform_admin(actor):
            raise PermissionError("Invitation email does not match the authenticated user.")
        if invitation.role == OrganizationRole.RECRUITER and not EntitlementService.can_invite_recruiter(
            invitation.invited_by or actor,
            invitation.organization,
        ):
            raise PermissionError("This organization has no available recruiter seats.")

        membership, _ = OrganizationMembership.objects.update_or_create(
            organization=invitation.organization,
            user=actor,
            role=invitation.role,
            defaults={"status": MembershipStatus.ACTIVE, "invited_by": invitation.invited_by},
        )
        invitation.accepted_by = actor
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_by", "accepted_at", "updated_at"])
        AuditService.record(
            actor=actor,
            action="organization_member_invitation_accepted",
            target=membership,
            organization=invitation.organization,
            metadata={"invitation_id": str(invitation.id), "role": invitation.role},
        )
        AnalyticsService.track(
            name="organization_member_added",
            user=actor,
            organization=invitation.organization,
            target=membership,
            metadata={"source": "invitation_acceptance", "role": invitation.role},
        )
        if invitation.invited_by:
            NotificationService.notify(
                recipient=invitation.invited_by,
                notification_type=NotificationType.ORGANIZATION_INVITATION_ACCEPTED,
                title="Invitation accepted",
                body=f"{actor.full_name} accepted the invitation to {invitation.organization.name}.",
                action_url="/",
                payload={"organization_id": str(invitation.organization.id), "membership_id": str(membership.id)},
            )
        return membership

    @staticmethod
    @transaction.atomic
    def change_member_role(
        *,
        actor,
        membership: OrganizationMembership,
        role: str,
    ) -> OrganizationMembership:
        OrganizationService._ensure_can_grant_role(
            actor=actor,
            target_user=membership.user,
            organization=membership.organization,
            role=role,
        )
        if not PermissionService.can_manage_organization_membership(actor, membership):
            raise PermissionError("You cannot change this organization membership.")

        previous_role = membership.role
        membership.role = role
        membership.save(update_fields=["role", "updated_at"])
        AuditService.record(
            actor=actor,
            action="organization_member_role_changed",
            target=membership,
            organization=membership.organization,
            metadata={
                "member_user_id": str(membership.user_id),
                "previous_role": previous_role,
                "new_role": role,
            },
        )
        return membership

    @staticmethod
    @transaction.atomic
    def remove_member(*, actor, membership: OrganizationMembership) -> OrganizationMembership:
        if actor == membership.user and membership.role != OrganizationRole.STUDENT:
            raise PermissionError("Privileged members cannot remove themselves.")
        if not PermissionService.can_manage_organization_membership(actor, membership):
            raise PermissionError("You cannot remove this organization membership.")

        membership.status = MembershipStatus.REMOVED
        membership.save(update_fields=["status", "updated_at"])
        AuditService.record(
            actor=actor,
            action="organization_member_removed",
            target=membership,
            organization=membership.organization,
            metadata={"member_user_id": str(membership.user_id), "role": membership.role},
        )
        return membership


class EnterpriseOrganizationService:
    MEMBER_IMPORT_ROLES = {
        BulkImportType.STUDENTS: OrganizationRole.STUDENT,
        BulkImportType.RECRUITERS: OrganizationRole.RECRUITER,
        BulkImportType.INSTRUCTORS: OrganizationRole.INSTRUCTOR,
        BulkImportType.EMPLOYEES: OrganizationRole.MENTOR,
    }
    IMPORT_REQUIRED_COLUMNS = {
        BulkImportType.STUDENTS: ["email", "full_name"],
        BulkImportType.RECRUITERS: ["email", "full_name"],
        BulkImportType.INSTRUCTORS: ["email", "full_name"],
        BulkImportType.EMPLOYEES: ["email", "full_name"],
        BulkImportType.DEPARTMENTS: ["name"],
        BulkImportType.TEAMS: ["name"],
        BulkImportType.COHORTS: ["name"],
        BulkImportType.SKILLS: ["email", "skill"],
        BulkImportType.COURSES: ["title", "instructor_email"],
        BulkImportType.COURSE_ASSIGNMENTS: ["email", "course_id"],
        BulkImportType.COHORT_ASSIGNMENTS: ["email", "cohort_name"],
    }
    REPORT_EXPORT_TYPES = {
        "enrollment": "enrollment_report",
        "enrollment_report": "enrollment_report",
        "placement": "placement_report",
        "placement_report": "placement_report",
        "hiring": "hiring_report",
        "hiring_report": "hiring_report",
        "recruiter_activity": "recruiter_activity_report",
        "recruiter_activity_report": "recruiter_activity_report",
        "certificate_completion": "certificate_completion_report",
        "certificate_completion_report": "certificate_completion_report",
        "course_completion": "course_completion_report",
        "course_completion_report": "course_completion_report",
        "department_summary": "department_summary_report",
        "department_summary_report": "department_summary_report",
        "cohort_summary": "cohort_summary_report",
        "cohort_summary_report": "cohort_summary_report",
        "organization_summary": "organization_summary_report",
        "organization_summary_report": "organization_summary_report",
        "engagement_summary": "engagement_summary_report",
        "engagement_summary_report": "engagement_summary_report",
        "export_summary_report": "export_summary_report",
    }
    IMAGE_FIELDS = {
        "logo": "logo",
        "banner": "banner",
        "favicon": "favicon",
        "certificate_logo": "certificate_logo",
        "email_header_image": "email_header_image",
    }

    @staticmethod
    def _csv_file_from_rows(rows):
        return EnterpriseOrganizationService.csv_export(rows).encode("utf-8")

    @staticmethod
    def _save_import_files(job, *, summary_rows=None, error_rows=None):
        update_fields = []
        if summary_rows is not None:
            content = EnterpriseOrganizationService._csv_file_from_rows(summary_rows)
            job.summary_file.save(f"{job.organization.slug}-{job.import_type}-{job.id}-summary.csv", ContentFile(content), save=False)
            update_fields.append("summary_file")
        if error_rows is not None:
            content = EnterpriseOrganizationService._csv_file_from_rows(error_rows)
            job.error_file.save(f"{job.organization.slug}-{job.import_type}-{job.id}-errors.csv", ContentFile(content), save=False)
            update_fields.append("error_file")
        if update_fields:
            update_fields.append("updated_at")
            job.save(update_fields=update_fields)

    @staticmethod
    def _worker_key(prefix, organization):
        return f"{prefix}:{organization.id}"

    @staticmethod
    def record_worker_event(*, worker_key, organization=None, success=None, duration_seconds=0, retries=0, stuck_job_count=None, metadata=None):
        status, _ = EnterpriseWorkerStatus.objects.get_or_create(worker_key=worker_key, organization=organization)
        now = timezone.now()
        status.last_heartbeat_at = now
        if success is True:
            status.last_successful_run_at = now
        elif success is False:
            status.last_failed_run_at = now
            status.failure_count += 1
        if duration_seconds:
            status.average_duration_seconds = int((status.average_duration_seconds + duration_seconds) / 2) if status.average_duration_seconds else int(duration_seconds)
        if retries:
            status.retry_count += retries
        if stuck_job_count is not None:
            status.stuck_job_count = stuck_job_count
        if metadata:
            status.metadata = {**status.metadata, **metadata}
        status.save()
        return status

    @staticmethod
    def ensure_can_manage(actor, organization):
        if not PermissionService.can_manage_organization(actor, organization):
            raise PermissionError("You cannot manage this organization.")

    @staticmethod
    def ensure_can_view_reports(actor, organization):
        if not PermissionService.can_view_enterprise_reports(actor, organization):
            raise PermissionError("You cannot view this organization's enterprise data.")

    @staticmethod
    def ensure_can_export(actor, organization, export_type):
        if not PermissionService.can_create_enterprise_export(actor, organization, export_type):
            raise PermissionError("You cannot create this organization export.")

    @staticmethod
    def transition_job(*, actor=None, job, status_value, organization, metadata=None):
        previous_status = getattr(job, "status", "")
        now = timezone.now()
        job.status = status_value
        if status_value in {"processing", "validating"} and not getattr(job, "started_at", None):
            job.started_at = now
        if status_value == "completed":
            job.completed_at = now
            job.progress_percentage = 100
        if status_value == "failed":
            job.failed_at = now
        if getattr(job, "started_at", None) and getattr(job, "completed_at", None):
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
        job.save()
        AuditService.record(
            actor=actor,
            action=f"enterprise_job_{status_value}",
            target=job,
            organization=organization,
            metadata={"previous_status": previous_status, "new_status": status_value, **(metadata or {})},
        )
        return job

    @staticmethod
    def get_or_create_profile(organization):
        profile, _ = OrganizationProfile.objects.get_or_create(organization=organization)
        return profile

    @staticmethod
    def get_or_create_policy(organization):
        policy, _ = OrganizationPolicy.objects.get_or_create(organization=organization)
        return policy

    @staticmethod
    def dashboard(organization):
        memberships = organization.memberships.filter(status=MembershipStatus.ACTIVE)
        jobs = JobListing.objects.filter(organization=organization)
        applications = JobApplication.objects.filter(organization=organization)
        active_learners = memberships.filter(role=OrganizationRole.STUDENT).count()
        active_recruiters = memberships.filter(role=OrganizationRole.RECRUITER).count()
        enrollments = Enrollment.objects.filter(user__organization_memberships__organization=organization).distinct()
        completed_enrollments = enrollments.filter(status=EnrollmentStatus.COMPLETED).count()
        total_enrollments = enrollments.count()
        applications_count = applications.count()
        hired_count = applications.filter(stage=ApplicationStage.OFFER_ACCEPTED).count()
        placement_rate = round((hired_count / active_learners) * 100, 2) if active_learners else 0
        health_inputs = [
            organization.status == "active",
            active_learners > 0,
            jobs.exists(),
            applications_count > 0,
            bool(getattr(organization, "enterprise_profile", None)),
        ]
        applications_by_status = dict(applications.values_list("stage").annotate(total=Count("id")))
        interviews_by_status = dict(
            Interview.objects.filter(organization=organization).values_list("status").annotate(total=Count("id"))
        )
        department_breakdown = list(
            organization.departments.annotate(member_count=Count("members")).values("id", "name", "status", "member_count")
        )
        cohort_breakdown = list(
            organization.cohorts.annotate(member_count=Count("members")).values("id", "name", "status", "program", "graduation_year", "member_count")
        )
        cohort_progress = []
        for cohort in organization.cohorts.prefetch_related("members__membership__user"):
            user_ids = [member.membership.user_id for member in cohort.members.all()]
            cohort_enrollments = Enrollment.objects.filter(user_id__in=user_ids).distinct()
            total = cohort_enrollments.count()
            completed = cohort_enrollments.filter(status=EnrollmentStatus.COMPLETED).count()
            cohort_progress.append({
                "cohort_id": str(cohort.id),
                "name": cohort.name,
                "completed": completed,
                "total": total,
                "rate": round((completed / total) * 100, 2) if total else 0,
            })
        certificates_count = Certificate.objects.filter(user__organization_memberships__organization=organization).distinct().count()
        return {
            "active_learners": active_learners,
            "active_recruiters": active_recruiters,
            "student_activation_rate": round((total_enrollments / active_learners) * 100, 2) if active_learners else 0,
            "course_completion": {
                "completed": completed_enrollments,
                "total": total_enrollments,
                "rate": round((completed_enrollments / total_enrollments) * 100, 2) if total_enrollments else 0,
            },
            "course_progress_by_cohort": cohort_progress,
            "certificates_issued": certificates_count,
            "certificate_completion_rate": round((certificates_count / active_learners) * 100, 2) if active_learners else 0,
            "jobs_posted": jobs.count(),
            "applications_received": applications_count,
            "applications_by_status": applications_by_status,
            "interviews": Interview.objects.filter(organization=organization).count(),
            "interviews_by_status": interviews_by_status,
            "hiring_success": hired_count,
            "placement_rate": placement_rate,
            "recruiter_activity": {
                "active_recruiters": active_recruiters,
                "jobs_posted": jobs.count(),
                "applications_reviewed": applications.exclude(stage=ApplicationStage.APPLIED).count(),
            },
            "department_breakdown": department_breakdown,
            "cohort_breakdown": cohort_breakdown,
            "student_engagement": {
                "active_members": active_learners,
                "enrollments": total_enrollments,
            },
            "ai_usage": {"events": 0},
            "monthly_trend_summary": {
                "jobs_created_30d": jobs.filter(created_at__gte=timezone.now() - timedelta(days=30)).count(),
                "applications_created_30d": applications.filter(created_at__gte=timezone.now() - timedelta(days=30)).count(),
                "certificates_issued_30d": Certificate.objects.filter(
                    user__organization_memberships__organization=organization,
                    issued_at__gte=timezone.now() - timedelta(days=30),
                ).distinct().count(),
            },
            "revenue": {"placeholder": True, "amount": 0},
            "organization_health_score": int((sum(bool(item) for item in health_inputs) / len(health_inputs)) * 100),
        }

    @staticmethod
    def hierarchy_summary(organization):
        return {
            "departments": organization.departments.filter(status="active").count(),
            "teams": organization.teams.filter(status="active").count(),
            "cohorts": organization.cohorts.exclude(status="archived").count(),
            "members": organization.memberships.filter(status=MembershipStatus.ACTIVE).count(),
        }

    @staticmethod
    def validate_csv(import_type, csv_content):
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        rows = []
        errors = []
        headers = reader.fieldnames or []
        required_columns = EnterpriseOrganizationService.IMPORT_REQUIRED_COLUMNS.get(import_type, [])
        for column in required_columns:
            if column not in headers:
                errors.append({"row": 1, "field": column, "message": f"Missing required column: {column}."})
        for index, row in enumerate(reader, start=2):
            normalized = {key.strip(): (value or "").strip() for key, value in row.items() if key}
            for column in required_columns:
                if not normalized.get(column):
                    errors.append({"row": index, "field": column, "message": f"{column} is required."})
            rows.append({"row_number": index, "data": normalized})
        return rows, errors

    @staticmethod
    def import_template(import_type):
        required = EnterpriseOrganizationService.IMPORT_REQUIRED_COLUMNS.get(import_type, [])
        optional = {
            BulkImportType.STUDENTS: ["department", "cohort_name"],
            BulkImportType.RECRUITERS: ["team_name"],
            BulkImportType.INSTRUCTORS: ["department"],
            BulkImportType.EMPLOYEES: ["department"],
            BulkImportType.DEPARTMENTS: ["description"],
            BulkImportType.TEAMS: ["team_type", "manager_email"],
            BulkImportType.COHORTS: ["program", "academic_year", "graduation_year"],
            BulkImportType.SKILLS: ["level"],
            BulkImportType.COURSES: ["short_description", "description", "level", "status"],
            BulkImportType.COURSE_ASSIGNMENTS: ["cohort_name"],
            BulkImportType.COHORT_ASSIGNMENTS: ["role"],
        }.get(import_type, [])
        headers = required + optional
        sample = {header: "" for header in headers}
        if "email" in sample:
            sample["email"] = "learner@example.com"
        if "full_name" in sample:
            sample["full_name"] = "Learner Example"
        if "name" in sample:
            sample["name"] = "Example Name"
        return {"import_type": import_type, "required_columns": required, "columns": headers, "sample_rows": [sample]}

    @staticmethod
    @transaction.atomic
    def bulk_import(*, actor, organization, import_type, csv_content, source_filename="", commit=False):
        EnterpriseOrganizationService.ensure_can_manage(actor, organization)
        rows, errors = EnterpriseOrganizationService.validate_csv(import_type, csv_content)
        job = BulkImportJob.objects.create(
            organization=organization,
            import_type=import_type,
            source_filename=source_filename,
            source_content=csv_content,
            preview_rows=rows[:100],
            validation_errors=errors,
            required_columns=EnterpriseOrganizationService.IMPORT_REQUIRED_COLUMNS.get(import_type, []),
            error_report=errors,
            error_count=len(errors),
            created_by=actor,
            status=BulkImportJob.Status.FAILED_VALIDATION if errors else (BulkImportJob.Status.QUEUED if commit else BulkImportJob.Status.PREVIEWED),
        )
        if errors:
            EnterpriseOrganizationService._save_import_files(
                job,
                summary_rows=[{"success_count": 0, "created_count": 0, "updated_count": 0, "skipped_count": 0, "failed_count": len(errors), "total_rows": len(rows)}],
                error_rows=errors,
            )
        success_count = 0
        if commit and not errors:
            job = EnterpriseOrganizationService.process_import(job)
            success_count = job.success_count
        else:
            job.success_count = success_count
            job.partial_success_report = [{"success_count": success_count, "total_rows": len(rows)}]
            job.save(update_fields=["success_count", "partial_success_report", "updated_at"])
        AuditService.record(
            actor=actor,
            action="organization_bulk_import_completed" if commit and not errors else "organization_bulk_import_previewed",
            target=job,
            organization=organization,
            metadata={"import_type": import_type, "success_count": success_count, "error_count": len(errors)},
        )
        return job

    @staticmethod
    @transaction.atomic
    def process_import(job):
        if job.status not in {BulkImportJob.Status.QUEUED, BulkImportJob.Status.FAILED}:
            return job
        worker_key = EnterpriseOrganizationService._worker_key("bulk_import", job.organization)
        EnterpriseOrganizationService.transition_job(
            actor=job.created_by,
            job=job,
            status_value=BulkImportJob.Status.VALIDATING,
            organization=job.organization,
        )
        rows, errors = EnterpriseOrganizationService.validate_csv(job.import_type, job.source_content)
        job.preview_rows = rows[:100]
        job.validation_errors = errors
        job.error_report = errors
        job.error_count = len(errors)
        job.progress_percentage = 20
        job.save(update_fields=["preview_rows", "validation_errors", "error_report", "error_count", "progress_percentage", "updated_at"])
        if errors:
            job.failure_reason = "CSV validation failed."
            job.save(update_fields=["failure_reason", "updated_at"])
            EnterpriseOrganizationService._save_import_files(
                job,
                summary_rows=[{"success_count": 0, "created_count": 0, "updated_count": 0, "skipped_count": 0, "failed_count": len(errors), "total_rows": len(rows)}],
                error_rows=errors,
            )
            return EnterpriseOrganizationService.transition_job(
                actor=job.created_by,
                job=job,
                status_value=BulkImportJob.Status.FAILED_VALIDATION,
                organization=job.organization,
                metadata={"error_count": len(errors)},
            )

        EnterpriseOrganizationService.transition_job(
            actor=job.created_by,
            job=job,
            status_value=BulkImportJob.Status.PROCESSING,
            organization=job.organization,
        )
        success_count = 0
        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        duplicates = []
        row_errors = []
        for index, item in enumerate(rows, start=1):
            data = item["data"]
            try:
                if job.import_type in EnterpriseOrganizationService.MEMBER_IMPORT_ROLES:
                    email = data["email"].lower()
                    user = User.objects.filter(email=email).first()
                    user_created = False
                    if user is None:
                        user = User.objects.create_user(
                            email=email,
                            password=secrets.token_urlsafe(24),
                            full_name=data.get("full_name") or email,
                            role=EnterpriseOrganizationService.MEMBER_IMPORT_ROLES[job.import_type],
                        )
                        user_created = True
                    membership, membership_created = OrganizationMembership.objects.update_or_create(
                        organization=job.organization,
                        user=user,
                        role=EnterpriseOrganizationService.MEMBER_IMPORT_ROLES[job.import_type],
                        defaults={"status": MembershipStatus.ACTIVE, "invited_by": job.created_by},
                    )
                    if data.get("department"):
                        department, _ = Department.objects.get_or_create(organization=job.organization, name=data["department"])
                        DepartmentMember.objects.update_or_create(department=department, membership=membership)
                    if data.get("team_name"):
                        team, _ = OrganizationTeam.objects.get_or_create(organization=job.organization, name=data["team_name"])
                        TeamMember.objects.update_or_create(team=team, membership=membership)
                    if data.get("cohort_name"):
                        cohort, _ = Cohort.objects.get_or_create(organization=job.organization, name=data["cohort_name"])
                        CohortMember.objects.update_or_create(cohort=cohort, membership=membership)
                    if membership_created or user_created:
                        created_count += 1
                    else:
                        updated_count += 1
                        duplicates.append({"row": item["row_number"], "email": email})
                    success_count += 1
                elif job.import_type == BulkImportType.DEPARTMENTS:
                    _, created = Department.objects.update_or_create(
                        organization=job.organization,
                        name=data["name"],
                        defaults={"description": data.get("description", "")},
                    )
                    created_count += int(created)
                    updated_count += int(not created)
                    success_count += 1
                elif job.import_type == BulkImportType.TEAMS:
                    manager = None
                    if data.get("manager_email"):
                        manager_user = User.objects.filter(email=data["manager_email"].lower()).first()
                        manager = OrganizationMembership.objects.filter(organization=job.organization, user=manager_user).first() if manager_user else None
                    _, created = OrganizationTeam.objects.update_or_create(
                        organization=job.organization,
                        name=data["name"],
                        defaults={"team_type": data.get("team_type", "other") or "other", "manager": manager},
                    )
                    created_count += int(created)
                    updated_count += int(not created)
                    success_count += 1
                elif job.import_type == BulkImportType.COHORTS:
                    _, created = Cohort.objects.update_or_create(
                        organization=job.organization,
                        name=data["name"],
                        defaults={
                            "program": data.get("program", ""),
                            "academic_year": data.get("academic_year", ""),
                            "graduation_year": int(data["graduation_year"]) if data.get("graduation_year") else None,
                        },
                    )
                    created_count += int(created)
                    updated_count += int(not created)
                    success_count += 1
                elif job.import_type == BulkImportType.SKILLS:
                    user = User.objects.filter(email=data["email"].lower()).first()
                    membership_exists = OrganizationMembership.objects.filter(organization=job.organization, user=user, status=MembershipStatus.ACTIVE).exists() if user else False
                    if not user or not membership_exists:
                        skipped_count += 1
                        row_errors.append({"row": item["row_number"], "field": "email", "message": "User is not an active member of this organization."})
                    else:
                        portfolio, _ = Portfolio.objects.get_or_create(user=user)
                        _, created = PortfolioSkill.objects.update_or_create(
                            portfolio=portfolio,
                            name=data["skill"],
                            defaults={"category": data.get("category", ""), "source": SkillSource.MANUAL},
                        )
                        created_count += int(created)
                        updated_count += int(not created)
                        success_count += 1
                elif job.import_type == BulkImportType.COURSES:
                    instructor = User.objects.filter(email=data["instructor_email"].lower()).first()
                    instructor_member = OrganizationMembership.objects.filter(organization=job.organization, user=instructor).first() if instructor else None
                    if not instructor_member:
                        skipped_count += 1
                        row_errors.append({"row": item["row_number"], "field": "instructor_email", "message": "Instructor must be an organization member."})
                    else:
                        _, created = Course.objects.update_or_create(
                            instructor=instructor,
                            title=data["title"],
                            defaults={
                                "short_description": data.get("short_description", ""),
                                "description": data.get("description", ""),
                                "level": data.get("level") or "beginner",
                                "status": data.get("status") or CourseStatus.DRAFT,
                            },
                        )
                        created_count += int(created)
                        updated_count += int(not created)
                        success_count += 1
                elif job.import_type == BulkImportType.COURSE_ASSIGNMENTS:
                    user = User.objects.filter(email=data["email"].lower()).first()
                    membership_exists = OrganizationMembership.objects.filter(organization=job.organization, user=user, status=MembershipStatus.ACTIVE).exists() if user else False
                    course = Course.objects.filter(id=data["course_id"]).first() if data.get("course_id") else None
                    if not user or not membership_exists or not course:
                        skipped_count += 1
                        row_errors.append({"row": item["row_number"], "field": "course_id", "message": "Active organization member and valid course_id are required."})
                    else:
                        _, created = Enrollment.objects.update_or_create(
                            user=user,
                            course=course,
                            defaults={"status": data.get("status") or EnrollmentStatus.ACTIVE},
                        )
                        if data.get("cohort_name"):
                            cohort, _ = Cohort.objects.get_or_create(organization=job.organization, name=data["cohort_name"])
                            membership = OrganizationMembership.objects.filter(organization=job.organization, user=user).first()
                            if membership:
                                CohortMember.objects.update_or_create(cohort=cohort, membership=membership)
                        created_count += int(created)
                        updated_count += int(not created)
                        success_count += 1
                elif job.import_type == BulkImportType.COHORT_ASSIGNMENTS:
                    user = User.objects.filter(email=data["email"].lower()).first()
                    cohort = Cohort.objects.filter(organization=job.organization, name=data["cohort_name"]).first()
                    membership = OrganizationMembership.objects.filter(organization=job.organization, user=user).first() if user else None
                    if cohort and membership:
                        _, created = CohortMember.objects.update_or_create(
                            cohort=cohort,
                            membership=membership,
                            defaults={"role": data.get("role") or EnterpriseRole.MEMBER},
                        )
                        created_count += int(created)
                        updated_count += int(not created)
                        success_count += 1
                    else:
                        skipped_count += 1
                        row_errors.append({"row": item["row_number"], "field": "cohort_name", "message": "Cohort and organization membership are required."})
            except Exception as exc:
                failed_count += 1
                row_errors.append({"row": item["row_number"], "field": "row", "message": str(exc)[:500]})
            finally:
                job.progress_percentage = min(95, 20 + int((index / max(len(rows), 1)) * 75))
                job.save(update_fields=["progress_percentage", "updated_at"])
        job.success_count = success_count
        job.error_report = row_errors
        job.error_count = len(row_errors)
        job.partial_success_report = [{
            "success_count": success_count,
            "created_count": created_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "total_rows": len(rows),
            "duplicates": len(duplicates),
        }]
        job.save(update_fields=["success_count", "error_report", "error_count", "partial_success_report", "updated_at"])
        EnterpriseOrganizationService._save_import_files(
            job,
            summary_rows=job.partial_success_report,
            error_rows=row_errors or [{"row": "", "field": "", "message": "No row errors."}],
        )
        job = EnterpriseOrganizationService.transition_job(
            actor=job.created_by,
            job=job,
            status_value=BulkImportJob.Status.COMPLETED,
            organization=job.organization,
            metadata={
                "success_count": success_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "duplicates": len(duplicates),
            },
        )
        EnterpriseOrganizationService.record_worker_event(
            worker_key=worker_key,
            organization=job.organization,
            success=failed_count == 0,
            duration_seconds=job.duration_seconds,
            retries=0,
            metadata={"last_import_id": str(job.id), "import_type": job.import_type},
        )
        return job

    @staticmethod
    def validate_branding_image(file_obj):
        content_type = getattr(file_obj, "content_type", "")
        file_name = getattr(file_obj, "name", "")
        file_size = getattr(file_obj, "size", 0)
        extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if content_type not in {"image/png", "image/jpeg", "image/webp", "image/x-icon", "image/vnd.microsoft.icon"}:
            raise serializers.ValidationError({"file": "Branding assets must be images."})
        if extension not in {"png", "jpg", "jpeg", "webp", "ico"}:
            raise serializers.ValidationError({"file": "Unsupported branding image extension."})
        if file_size <= 0 or file_size > 5 * 1024 * 1024:
            raise serializers.ValidationError({"file": "Branding image must be 5MB or smaller."})
        try:
            file_obj.seek(0)
            Image.open(file_obj).verify()
            file_obj.seek(0)
        except Exception as exc:
            raise serializers.ValidationError({"file": "Uploaded file is not a valid image."}) from exc

    @staticmethod
    def update_branding_asset(*, actor, organization, field_name, file_obj):
        EnterpriseOrganizationService.ensure_can_manage(actor, organization)
        if field_name not in EnterpriseOrganizationService.IMAGE_FIELDS:
            raise serializers.ValidationError({"asset_type": "Unsupported branding asset type."})
        EnterpriseOrganizationService.validate_branding_image(file_obj)
        profile = EnterpriseOrganizationService.get_or_create_profile(organization)
        setattr(profile, EnterpriseOrganizationService.IMAGE_FIELDS[field_name], file_obj)
        profile.save(update_fields=[EnterpriseOrganizationService.IMAGE_FIELDS[field_name], "updated_at"])
        AuditService.record(
            actor=actor,
            action="organization_branding_asset_uploaded",
            target=profile,
            organization=organization,
            metadata={"asset_type": field_name, "file_name": getattr(file_obj, "name", "")},
        )
        return profile

    @staticmethod
    def report_rows(organization, report_type):
        normalized = EnterpriseOrganizationService.REPORT_EXPORT_TYPES.get(report_type, report_type)
        memberships = organization.memberships.filter(status=MembershipStatus.ACTIVE).select_related("user")
        member_user_ids = memberships.values_list("user_id", flat=True)
        if normalized == "enrollment_report":
            return list(
                Enrollment.objects.filter(user_id__in=member_user_ids)
                .select_related("user", "course")
                .values("user__email", "user__full_name", "course__title", "status", "last_accessed_at", "completed_at", "amount_paid", "created_at")
            )
        if normalized == "placement_report":
            return list(
                JobApplication.objects.filter(organization=organization)
                .select_related("candidate", "job")
                .values("candidate__email", "candidate__full_name", "job__title", "stage", "assigned_recruiter__email", "created_at", "updated_at")
            )
        if normalized == "hiring_report":
            rows = []
            for job in JobListing.objects.filter(organization=organization).annotate(application_total=Count("applications")):
                rows.append({
                    "job_id": str(job.id),
                    "title": job.title,
                    "status": "active" if job.is_active else "archived",
                    "applications": job.application_total,
                    "posted_by": getattr(job.posted_by, "email", ""),
                    "created_at": job.created_at,
                    "expires_at": job.expires_at,
                })
            return rows
        if normalized == "recruiter_activity_report":
            rows = []
            for membership in memberships.filter(role__in=[OrganizationRole.RECRUITER, OrganizationRole.COMPANY_ADMIN]):
                rows.append({
                    "recruiter_email": membership.user.email,
                    "recruiter_name": membership.user.full_name,
                    "jobs_posted": JobListing.objects.filter(organization=organization, posted_by=membership.user).count(),
                    "applications_assigned": JobApplication.objects.filter(organization=organization, assigned_recruiter=membership.user).count(),
                    "saved_candidates": SavedCandidate.objects.filter(organization=organization, saved_by=membership.user).count(),
                    "interviews_created": Interview.objects.filter(organization=organization, created_by=membership.user).count(),
                })
            return rows
        if normalized == "certificate_completion_report":
            return list(
                Certificate.objects.filter(user_id__in=member_user_ids)
                .select_related("user", "course")
                .values("user__email", "user__full_name", "course__title", "cert_number", "issued_at", "is_revoked")
            )
        if normalized == "course_completion_report":
            rows = []
            enrollments = Enrollment.objects.filter(user_id__in=member_user_ids).select_related("course")
            for item in enrollments.values("course_id", "course__title").annotate(total=Count("id")):
                completed = enrollments.filter(course_id=item["course_id"], status=EnrollmentStatus.COMPLETED).count()
                rows.append({
                    "course_id": str(item["course_id"]),
                    "course_title": item["course__title"],
                    "enrollments": item["total"],
                    "completed": completed,
                    "completion_rate": round((completed / item["total"]) * 100, 2) if item["total"] else 0,
                })
            return rows
        if normalized == "department_summary_report":
            return list(
                organization.departments.annotate(member_count=Count("members")).values("id", "name", "status", "member_count", "created_at")
            )
        if normalized == "cohort_summary_report":
            rows = []
            for cohort in organization.cohorts.prefetch_related("members__membership"):
                user_ids = [member.membership.user_id for member in cohort.members.all()]
                enrollments = Enrollment.objects.filter(user_id__in=user_ids)
                total = enrollments.count()
                completed = enrollments.filter(status=EnrollmentStatus.COMPLETED).count()
                rows.append({
                    "cohort_id": str(cohort.id),
                    "name": cohort.name,
                    "program": cohort.program,
                    "status": cohort.status,
                    "member_count": len(user_ids),
                    "enrollments": total,
                    "completed_enrollments": completed,
                    "completion_rate": round((completed / total) * 100, 2) if total else 0,
                })
            return rows
        if normalized == "organization_summary_report":
            summary = EnterpriseOrganizationService.dashboard(organization)
            return [{
                "organization": organization.name,
                "status": organization.status,
                "active_learners": summary["active_learners"],
                "active_recruiters": summary["active_recruiters"],
                "jobs_posted": summary["jobs_posted"],
                "applications_received": summary["applications_received"],
                "certificates_issued": summary["certificates_issued"],
                "placement_rate": summary["placement_rate"],
                "organization_health_score": summary["organization_health_score"],
            }]
        if normalized == "engagement_summary_report":
            return [{
                "metric": "student_engagement",
                "active_members": memberships.filter(role=OrganizationRole.STUDENT).count(),
                "enrollments": Enrollment.objects.filter(user_id__in=member_user_ids).count(),
                "profile_skills": PortfolioSkill.objects.filter(portfolio__user_id__in=member_user_ids).count(),
                "applications": JobApplication.objects.filter(candidate_id__in=member_user_ids).count(),
            }]
        if normalized == "export_summary_report":
            return list(
                organization.data_exports.values("id", "export_type", "file_format", "status", "row_count", "download_count", "expires_at", "legal_hold", "created_at")
            )
        return []

    @staticmethod
    def export_rows(organization, export_type):
        if export_type in EnterpriseOrganizationService.REPORT_EXPORT_TYPES.values():
            return EnterpriseOrganizationService.report_rows(organization, export_type)
        if export_type == "students":
            return list(organization.memberships.filter(role=OrganizationRole.STUDENT).select_related("user").values("user__email", "user__full_name", "status", "created_at"))
        if export_type == "recruiters":
            return list(organization.memberships.filter(role=OrganizationRole.RECRUITER).select_related("user").values("user__email", "user__full_name", "status", "created_at"))
        if export_type == "applications":
            return list(JobApplication.objects.filter(organization=organization).select_related("job", "candidate").values("candidate__email", "candidate__full_name", "job__title", "stage", "created_at"))
        if export_type == "certificates":
            return list(Certificate.objects.filter(user__organization_memberships__organization=organization).distinct().values("user__email", "course__title", "cert_number", "issued_at"))
        if export_type == "courses":
            return list(Enrollment.objects.filter(user__organization_memberships__organization=organization).select_related("course", "user").values("user__email", "course__title", "status", "last_accessed_at"))
        if export_type == "organizations":
            return [{"name": organization.name, "slug": organization.slug, "organization_type": organization.organization_type, "status": organization.status}]
        if export_type in {"analytics", "analytics_summary"}:
            return [EnterpriseOrganizationService.dashboard(organization)]
        if export_type == "audit_logs":
            return list(AuditLog.objects.filter(organization_id=organization.id).values("action", "target_type", "target_id", "created_at")[:1000])
        return []

    @staticmethod
    def xlsx_export(rows):
        flattened = [{key: str(value) for key, value in row.items()} for row in rows] or [{"empty": ""}]
        headers = sorted({key for row in flattened for key in row.keys()})
        sheet_rows = [headers] + [[row.get(header, "") for header in headers] for row in flattened]
        rows_xml = []
        for row_index, values in enumerate(sheet_rows, start=1):
            cells = []
            for column_index, value in enumerate(values, start=1):
                column = chr(64 + column_index) if column_index <= 26 else f"A{chr(64 + column_index - 26)}"
                cells.append(f'<c r="{column}{row_index}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
            rows_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
        sheet_xml = f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
        workbook_xml = '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Export" sheetId="1" r:id="rId1"/></sheets></workbook>'
        rels_xml = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
        workbook_rels_xml = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
        content_types_xml = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types_xml)
            archive.writestr("_rels/.rels", rels_xml)
            archive.writestr("xl/workbook.xml", workbook_xml)
            archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
            archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        return output.getvalue()

    @staticmethod
    @transaction.atomic
    def queue_export(*, actor, organization, export_type, file_format):
        EnterpriseOrganizationService.ensure_can_export(actor, organization, export_type)
        export_job = DataExportJob.objects.create(
            organization=organization,
            export_type=export_type,
            file_format=file_format,
            created_by=actor,
            expires_at=timezone.now() + timedelta(days=30),
            metadata={"queued_by": str(actor.id)},
        )
        AuditService.record(
            actor=actor,
            action="organization_export_queued",
            target=export_job,
            organization=organization,
            metadata={"export_type": export_type, "file_format": file_format},
        )
        return export_job

    @staticmethod
    @transaction.atomic
    def process_export(export_job):
        if export_job.status not in {DataExportJob.Status.QUEUED, DataExportJob.Status.FAILED}:
            return export_job
        worker_key = EnterpriseOrganizationService._worker_key("data_export", export_job.organization)
        export_job.status = DataExportJob.Status.PROCESSING
        export_job.last_error = ""
        export_job.started_at = timezone.now()
        export_job.progress_percentage = 10
        export_job.save(update_fields=["status", "last_error", "started_at", "progress_percentage", "updated_at"])
        AuditService.record(actor=export_job.created_by, action="organization_export_processing", target=export_job, organization=export_job.organization)
        try:
            rows = EnterpriseOrganizationService.export_rows(export_job.organization, export_job.export_type)
            if export_job.file_format == "xlsx":
                content = EnterpriseOrganizationService.xlsx_export(rows)
                extension = "xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                content = EnterpriseOrganizationService.csv_export(rows).encode("utf-8")
                extension = "csv"
                content_type = "text/csv"
            file_name = f"{export_job.organization.slug}-{export_job.export_type}-{export_job.id}.{extension}"
            export_job.file.save(file_name, ContentFile(content), save=False)
            export_job.file_name = file_name
            export_job.content_type = content_type
            export_job.file_size = len(content)
            export_job.row_count = len(rows)
            export_job.status = DataExportJob.Status.COMPLETED
            export_job.completed_at = timezone.now()
            export_job.duration_seconds = int((export_job.completed_at - export_job.started_at).total_seconds()) if export_job.started_at else 0
            export_job.progress_percentage = 100
            export_job.save(update_fields=["file", "file_name", "content_type", "file_size", "row_count", "status", "completed_at", "duration_seconds", "progress_percentage", "updated_at"])
            AuditService.record(
                actor=export_job.created_by,
                action="organization_export_completed",
                target=export_job,
                organization=export_job.organization,
                metadata={"row_count": export_job.row_count, "file_format": export_job.file_format},
            )
            EnterpriseOrganizationService.record_worker_event(
                worker_key=worker_key,
                organization=export_job.organization,
                success=True,
                duration_seconds=export_job.duration_seconds,
                metadata={"last_export_id": str(export_job.id), "export_type": export_job.export_type},
            )
        except Exception as exc:
            export_job.status = DataExportJob.Status.FAILED
            export_job.failed_at = timezone.now()
            export_job.last_error = str(exc)[:1000]
            export_job.failure_reason = export_job.last_error
            export_job.retry_count += 1
            export_job.save(update_fields=["status", "failed_at", "last_error", "failure_reason", "retry_count", "updated_at"])
            EnterpriseOrganizationService.record_worker_event(
                worker_key=worker_key,
                organization=export_job.organization,
                success=False,
                retries=1,
                metadata={"last_export_id": str(export_job.id), "error": export_job.last_error},
            )
        return export_job

    @staticmethod
    def mark_export_downloaded(export_job):
        export_job.download_count += 1
        export_job.last_downloaded_at = timezone.now()
        export_job.save(update_fields=["download_count", "last_downloaded_at", "updated_at"])
        AuditService.record(
            actor=None,
            action="organization_export_downloaded",
            target=export_job,
            organization=export_job.organization,
            metadata={"download_count": export_job.download_count},
        )

    @staticmethod
    def expire_exports(*, organization=None, delete_files=False):
        queryset = DataExportJob.objects.filter(status=DataExportJob.Status.COMPLETED, expires_at__lte=timezone.now())
        if organization:
            queryset = queryset.filter(organization=organization)
        count = 0
        for export_job in queryset:
            if export_job.legal_hold:
                AuditService.record(
                    actor=None,
                    action="organization_export_cleanup_skipped_legal_hold",
                    target=export_job,
                    organization=export_job.organization,
                )
                continue
            export_job.status = DataExportJob.Status.EXPIRED
            if delete_files and export_job.file:
                export_job.file.delete(save=False)
                export_job.file_deleted_at = timezone.now()
            export_job.save(update_fields=["status", "file", "file_deleted_at", "updated_at"])
            AuditService.record(
                actor=None,
                action="organization_export_file_deleted" if delete_files else "organization_export_expired",
                target=export_job,
                organization=export_job.organization,
                metadata={"delete_files": delete_files},
            )
            count += 1
        return count

    @staticmethod
    def queue_report(*, actor, organization, report_type, file_format="xlsx"):
        EnterpriseOrganizationService.ensure_can_export(actor, organization, "analytics_summary")
        report = EnterpriseReportJob.objects.create(
            organization=organization,
            report_type=report_type,
            created_by=actor,
            metadata={"queued_by": str(actor.id), "file_format": file_format},
        )
        AuditService.record(actor=actor, action="enterprise_report_queued", target=report, organization=organization)
        return report

    @staticmethod
    @transaction.atomic
    def process_report(report):
        if report.status not in {EnterpriseReportJob.Status.QUEUED, EnterpriseReportJob.Status.FAILED}:
            return report
        worker_key = EnterpriseOrganizationService._worker_key("enterprise_report", report.organization)
        report.status = EnterpriseReportJob.Status.PROCESSING
        report.started_at = timezone.now()
        report.progress_percentage = 20
        report.save(update_fields=["status", "started_at", "progress_percentage", "updated_at"])
        try:
            export_type = EnterpriseOrganizationService.REPORT_EXPORT_TYPES.get(report.report_type, report.report_type)
            export = EnterpriseOrganizationService.queue_export(
                actor=report.created_by,
                organization=report.organization,
                export_type=export_type,
                file_format=report.metadata.get("file_format", "xlsx"),
            )
            EnterpriseOrganizationService.process_export(export)
            report.export_job = export
            report.status = EnterpriseReportJob.Status.COMPLETED
            report.completed_at = timezone.now()
            report.duration_seconds = int((report.completed_at - report.started_at).total_seconds())
            report.progress_percentage = 100
            report.save(update_fields=["export_job", "status", "completed_at", "duration_seconds", "progress_percentage", "updated_at"])
            AuditService.record(actor=report.created_by, action="enterprise_report_completed", target=report, organization=report.organization)
            EnterpriseOrganizationService.record_worker_event(
                worker_key=worker_key,
                organization=report.organization,
                success=True,
                duration_seconds=report.duration_seconds,
                metadata={"last_report_id": str(report.id), "report_type": report.report_type},
            )
        except Exception as exc:
            report.status = EnterpriseReportJob.Status.FAILED
            report.failed_at = timezone.now()
            report.failure_reason = str(exc)[:1000]
            report.retry_count += 1
            report.save(update_fields=["status", "failed_at", "failure_reason", "retry_count", "updated_at"])
            EnterpriseOrganizationService.record_worker_event(
                worker_key=worker_key,
                organization=report.organization,
                success=False,
                retries=1,
                metadata={"last_report_id": str(report.id), "error": report.failure_reason},
            )
        return report

    @staticmethod
    def lifecycle_transition(*, actor, organization, action, new_owner=None, metadata=None):
        if not PermissionService.can_manage_organization(actor, organization):
            raise PermissionError("You cannot change this organization's lifecycle.")
        now = timezone.now()
        if action == "archive":
            if organization.status == "active" and organization.memberships.filter(status=MembershipStatus.ACTIVE).exists():
                raise PermissionError("Active organizations with members must be suspended before archive.")
            organization.status = "archived"
            organization.archived_at = now
        elif action == "suspend":
            organization.status = "suspended"
            organization.suspended_at = now
        elif action == "reactivate":
            organization.status = "active"
            organization.suspended_at = None
            organization.archived_at = None
        elif action == "soft_delete":
            if organization.status == "active":
                raise PermissionError("Active organizations cannot be soft deleted.")
            organization.status = "deleted"
            organization.deleted_at = now
        elif action == "transfer_ownership":
            organization.owner = new_owner
        else:
            raise serializers.ValidationError({"action": "Unsupported lifecycle action."})
        organization.lifecycle_metadata = {**organization.lifecycle_metadata, **(metadata or {}), "last_action": action}
        organization.save(update_fields=["status", "archived_at", "suspended_at", "deleted_at", "owner", "lifecycle_metadata", "updated_at"])
        AuditService.record(actor=actor, action=f"organization_{action}", target=organization, organization=organization, metadata=metadata or {})
        return organization

    @staticmethod
    def csv_export(rows):
        if not rows:
            return "empty\n"
        flattened = []
        for row in rows:
            flattened.append({key: str(value) for key, value in row.items()})
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=sorted({key for row in flattened for key in row.keys()}))
        writer.writeheader()
        writer.writerows(flattened)
        return output.getvalue()
