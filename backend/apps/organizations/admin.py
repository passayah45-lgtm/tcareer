from django.contrib import admin

from apps.organizations.models import (
    BulkImportJob,
    CandidateProfileUnlock,
    Cohort,
    CohortMember,
    DataExportJob,
    Department,
    DepartmentMember,
    EnterpriseReportJob,
    EnterpriseWorkerStatus,
    OrganizationProfile,
    OrganizationPolicy,
    OrganizationTeam,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    TeamMember,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "organization_type", "status", "country_code", "owner", "created_at")
    list_filter = ("organization_type", "status", "country_code")
    search_fields = ("name", "slug", "website_url")
    readonly_fields = ("id", "slug", "created_at", "updated_at")


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "role", "status", "created_at")
    list_filter = ("role", "status")
    search_fields = ("organization__name", "user__email", "user__full_name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ("organization", "email", "role", "invited_by", "expires_at", "accepted_at", "revoked_at")
    list_filter = ("role", "expires_at", "accepted_at", "revoked_at")
    search_fields = ("organization__name", "email")
    readonly_fields = ("id", "token_hash", "created_at", "updated_at")


@admin.register(OrganizationRecruiterEntitlement)
class OrganizationRecruiterEntitlementAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "max_recruiter_seats",
        "can_post_jobs",
        "can_search_candidates",
        "can_view_candidate_profiles",
        "ends_at",
    )
    list_filter = ("can_post_jobs", "can_search_candidates", "can_view_candidate_profiles")
    search_fields = ("organization__name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(CandidateProfileUnlock)
class CandidateProfileUnlockAdmin(admin.ModelAdmin):
    list_display = ("organization", "candidate", "unlocked_by", "created_at")
    search_fields = ("organization__name", "candidate__email", "candidate__full_name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ("organization", "support_email", "time_zone", "default_language", "updated_at")
    search_fields = ("organization__name", "support_email")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrganizationPolicy)
class OrganizationPolicyAdmin(admin.ModelAdmin):
    list_display = ("organization", "mfa_required", "password_min_length", "digest_frequency", "updated_at")
    list_filter = ("mfa_required", "digest_frequency")
    search_fields = ("organization__name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("organization", "name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("organization__name", "name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(DepartmentMember)
class DepartmentMemberAdmin(admin.ModelAdmin):
    list_display = ("department", "membership", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("department__name", "membership__user__email", "membership__organization__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrganizationTeam)
class OrganizationTeamAdmin(admin.ModelAdmin):
    list_display = ("organization", "name", "team_type", "status", "manager", "created_at")
    list_filter = ("team_type", "status")
    search_fields = ("organization__name", "name", "manager__user__email")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("team", "membership", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("team__name", "membership__user__email", "membership__organization__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ("organization", "name", "program", "graduation_year", "status", "created_at")
    list_filter = ("status", "graduation_year")
    search_fields = ("organization__name", "name", "program", "batch")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(CohortMember)
class CohortMemberAdmin(admin.ModelAdmin):
    list_display = ("cohort", "membership", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("cohort__name", "membership__user__email", "membership__organization__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(BulkImportJob)
class BulkImportJobAdmin(admin.ModelAdmin):
    list_display = ("organization", "import_type", "status", "progress_percentage", "success_count", "error_count", "created_by", "created_at")
    list_filter = ("import_type", "status")
    search_fields = ("organization__name", "source_filename", "created_by__email")
    readonly_fields = ("id", "preview_rows", "validation_errors", "required_columns", "error_report", "partial_success_report", "failure_reason", "created_at", "updated_at", "started_at", "completed_at", "failed_at")


@admin.register(DataExportJob)
class DataExportJobAdmin(admin.ModelAdmin):
    list_display = ("organization", "export_type", "file_format", "row_count", "status", "progress_percentage", "download_count", "legal_hold", "created_by", "created_at", "completed_at", "expires_at")
    list_filter = ("export_type", "file_format", "status", "legal_hold")
    search_fields = ("organization__name", "created_by__email")
    readonly_fields = ("id", "file_name", "content_type", "file_size", "last_error", "created_at", "updated_at", "completed_at", "failed_at", "file_deleted_at")


@admin.register(EnterpriseReportJob)
class EnterpriseReportJobAdmin(admin.ModelAdmin):
    list_display = ("organization", "report_type", "status", "progress_percentage", "created_by", "created_at", "completed_at")
    list_filter = ("report_type", "status")
    search_fields = ("organization__name", "created_by__email")
    readonly_fields = ("id", "failure_reason", "created_at", "updated_at", "started_at", "completed_at", "failed_at")


@admin.register(EnterpriseWorkerStatus)
class EnterpriseWorkerStatusAdmin(admin.ModelAdmin):
    list_display = ("worker_key", "organization", "last_heartbeat_at", "last_successful_run_at", "last_failed_run_at", "failure_count", "stuck_job_count")
    list_filter = ("worker_key",)
    search_fields = ("worker_key", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")
