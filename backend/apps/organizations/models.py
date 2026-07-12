from django.conf import settings
from django.db import models
from django.utils.text import slugify

from common.models import BaseModel


def organization_branding_upload_path(instance, filename):
    return f"organizations/{instance.organization_id}/branding/{filename}"


def organization_export_upload_path(instance, filename):
    return f"organizations/{instance.organization_id}/exports/{filename}"


class OrganizationType(models.TextChoices):
    UNIVERSITY = "university", "University"
    COMPANY = "company", "Company"
    BOOTCAMP = "bootcamp", "Bootcamp"
    NGO = "ngo", "NGO"
    GOVERNMENT = "government", "Government Institution"
    ENTERPRISE = "enterprise", "Enterprise Customer"
    PLATFORM_PARTNER = "platform_partner", "Platform Partner"
    OTHER = "other", "Other"


class OrganizationStatus(models.TextChoices):
    PENDING = "pending", "Pending Verification"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"
    DELETED = "deleted", "Deleted"


class OrganizationRole(models.TextChoices):
    STUDENT = "student", "Student"
    INSTRUCTOR = "instructor", "Instructor"
    MENTOR = "mentor", "Mentor"
    RECRUITER = "recruiter", "Recruiter"
    COMPANY_ADMIN = "company_admin", "Company Admin"
    UNIVERSITY_ADMIN = "university_admin", "University Admin"
    CONTENT_MODERATOR = "content_moderator", "Content Moderator"
    FINANCE_ADMIN = "finance_admin", "Finance Admin"
    PLATFORM_ADMIN = "platform_admin", "Platform Admin"
    SUPER_ADMIN = "super_admin", "Super Admin"
    REPORT_VIEWER = "report_viewer", "Report Viewer"
    DEPARTMENT_MANAGER = "department_manager", "Department Manager"
    COHORT_MANAGER = "cohort_manager", "Cohort Manager"
    TEAM_MANAGER = "team_manager", "Team Manager"
    EXPORT_MANAGER = "export_manager", "Export Manager"


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INVITED = "invited", "Invited"
    SUSPENDED = "suspended", "Suspended"
    REMOVED = "removed", "Removed"


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    organization_type = models.CharField(
        max_length=30,
        choices=OrganizationType.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.PENDING,
        db_index=True,
    )
    website_url = models.URLField(blank=True, default="")
    country_code = models.CharField(max_length=2, blank=True, default="", db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_accounts_created",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_accounts_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_organizations",
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    lifecycle_metadata = models.JSONField(default=dict, blank=True)
    merge_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_accounts"
        indexes = [
            models.Index(fields=["organization_type", "status"], name="organizatio_organiz_118010_idx"),
            models.Index(fields=["country_code", "status"], name="organizatio_country_0b7cf0_idx"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:240] or "organization"
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class OrganizationMembership(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        db_index=True,
    )
    role = models.CharField(max_length=30, choices=OrganizationRole.choices, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
        db_index=True,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_memberships_invited",
    )

    class Meta:
        db_table = "organization_account_memberships"
        unique_together = [("organization", "user", "role")]
        indexes = [
            models.Index(fields=["organization", "role", "status"], name="organizatio_organiz_68067a_idx"),
            models.Index(fields=["user", "status"], name="organizatio_user_id_dfbb75_idx"),
        ]

    def __str__(self):
        return f"{self.user_id} {self.role} at {self.organization_id}"


class OrganizationInvitation(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=30, choices=OrganizationRole.choices)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="organization_invitations_sent",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_invitations_accepted",
    )
    token_hash = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "organization_account_invitations"
        indexes = [
            models.Index(fields=["organization", "email"], name="organizatio_organiz_0cc3b2_idx"),
            models.Index(fields=["email", "expires_at"], name="organizatio_email_783529_idx"),
        ]

    def __str__(self):
        return f"{self.email} invited to {self.organization_id} as {self.role}"


class OrganizationRecruiterEntitlement(BaseModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="recruiter_entitlement",
    )
    max_recruiter_seats = models.PositiveIntegerField(default=0)
    can_post_jobs = models.BooleanField(default=False)
    can_search_candidates = models.BooleanField(default=False)
    can_view_candidate_profiles = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recruiter_entitlements_updated",
    )

    class Meta:
        db_table = "organization_recruiter_entitlements"

    def __str__(self):
        return f"Recruiter entitlement for {self.organization_id}"


class CandidateProfileUnlock(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="candidate_profile_unlocks",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile_unlocks",
    )
    unlocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="candidate_profiles_unlocked",
    )

    class Meta:
        db_table = "candidate_profile_unlocks"
        unique_together = [("organization", "candidate")]
        indexes = [
            models.Index(fields=["organization", "candidate"], name="candidate_p_organiz_6acffe_idx"),
        ]

    def __str__(self):
        return f"{self.organization_id} -> {self.candidate_id}"


class EnterpriseRole(models.TextChoices):
    MEMBER = "member", "Member"
    MANAGER = "manager", "Manager"
    ADMIN = "admin", "Admin"


class EnterpriseStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class OrganizationProfile(BaseModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="enterprise_profile",
    )
    logo_url = models.URLField(blank=True, default="")
    banner_url = models.URLField(blank=True, default="")
    favicon_url = models.URLField(blank=True, default="")
    logo = models.FileField(upload_to=organization_branding_upload_path, blank=True, default="")
    banner = models.FileField(upload_to=organization_branding_upload_path, blank=True, default="")
    favicon = models.FileField(upload_to=organization_branding_upload_path, blank=True, default="")
    certificate_logo = models.FileField(upload_to=organization_branding_upload_path, blank=True, default="")
    email_header_image = models.FileField(upload_to=organization_branding_upload_path, blank=True, default="")
    primary_color = models.CharField(max_length=20, blank=True, default="")
    secondary_color = models.CharField(max_length=20, blank=True, default="")
    support_email = models.EmailField(blank=True, default="")
    support_phone = models.CharField(max_length=50, blank=True, default="")
    time_zone = models.CharField(max_length=80, blank=True, default="UTC")
    default_language = models.CharField(max_length=10, blank=True, default="en")
    email_branding = models.JSONField(default=dict, blank=True)
    certificate_branding = models.JSONField(default=dict, blank=True)
    landing_page_branding = models.JSONField(default=dict, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_enterprise_profiles"


class OrganizationPolicy(BaseModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="policy",
    )
    password_min_length = models.PositiveSmallIntegerField(default=8)
    mfa_required = models.BooleanField(default=False)
    profile_visibility_default = models.BooleanField(default=True)
    resume_visibility_default = models.BooleanField(default=True)
    portfolio_visibility_default = models.BooleanField(default=True)
    invitation_expiration_days = models.PositiveSmallIntegerField(default=7)
    session_timeout_minutes = models.PositiveIntegerField(default=480)
    allowed_email_domains = models.JSONField(default=list, blank=True)
    recruiter_permissions = models.JSONField(default=dict, blank=True)
    student_permissions = models.JSONField(default=dict, blank=True)
    notification_defaults = models.JSONField(default=dict, blank=True)
    digest_frequency = models.CharField(max_length=30, blank=True, default="weekly")
    quiet_hours = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_policies"


class Department(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=EnterpriseStatus.choices, default=EnterpriseStatus.ACTIVE, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_departments"
        unique_together = [("organization", "name")]
        indexes = [models.Index(fields=["organization", "status"], name="org_dept_org_status_idx")]

    def __str__(self):
        return f"{self.name} ({self.organization_id})"


class DepartmentMember(BaseModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="members")
    membership = models.ForeignKey(OrganizationMembership, on_delete=models.CASCADE, related_name="department_memberships")
    role = models.CharField(max_length=20, choices=EnterpriseRole.choices, default=EnterpriseRole.MEMBER)

    class Meta:
        db_table = "organization_department_members"
        unique_together = [("department", "membership")]


class TeamType(models.TextChoices):
    RECRUITING = "recruiting", "Recruiting Team"
    INSTRUCTOR = "instructor", "Instructor Team"
    CAREER = "career", "Career Team"
    PLACEMENT = "placement", "Placement Team"
    ADMISSIONS = "admissions", "Admissions Team"
    OPERATIONS = "operations", "Operations Team"
    FINANCE = "finance", "Finance Team"
    OTHER = "other", "Other"


class OrganizationTeam(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=255)
    team_type = models.CharField(max_length=30, choices=TeamType.choices, default=TeamType.OTHER)
    manager = models.ForeignKey(
        OrganizationMembership,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_teams",
    )
    status = models.CharField(max_length=20, choices=EnterpriseStatus.choices, default=EnterpriseStatus.ACTIVE, db_index=True)
    permissions = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_teams"
        unique_together = [("organization", "name")]
        indexes = [models.Index(fields=["organization", "team_type", "status"], name="org_team_type_status_idx")]


class TeamMember(BaseModel):
    team = models.ForeignKey(OrganizationTeam, on_delete=models.CASCADE, related_name="members")
    membership = models.ForeignKey(OrganizationMembership, on_delete=models.CASCADE, related_name="team_memberships")
    role = models.CharField(max_length=20, choices=EnterpriseRole.choices, default=EnterpriseRole.MEMBER)

    class Meta:
        db_table = "organization_team_members"
        unique_together = [("team", "membership")]


class CohortStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class Cohort(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="cohorts")
    name = models.CharField(max_length=255)
    academic_year = models.CharField(max_length=20, blank=True, default="")
    semester = models.CharField(max_length=50, blank=True, default="")
    batch = models.CharField(max_length=100, blank=True, default="")
    program = models.CharField(max_length=255, blank=True, default="")
    graduation_year = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CohortStatus.choices, default=CohortStatus.ACTIVE, db_index=True)
    enrollment_starts_at = models.DateField(null=True, blank=True)
    enrollment_ends_at = models.DateField(null=True, blank=True)
    assigned_course_ids = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_cohorts"
        unique_together = [("organization", "name")]
        indexes = [models.Index(fields=["organization", "status"], name="org_cohort_org_status_idx")]


class CohortMember(BaseModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="members")
    membership = models.ForeignKey(OrganizationMembership, on_delete=models.CASCADE, related_name="cohort_memberships")
    role = models.CharField(max_length=20, choices=EnterpriseRole.choices, default=EnterpriseRole.MEMBER)

    class Meta:
        db_table = "organization_cohort_members"
        unique_together = [("cohort", "membership")]


class BulkImportType(models.TextChoices):
    STUDENTS = "students", "Students"
    RECRUITERS = "recruiters", "Recruiters"
    INSTRUCTORS = "instructors", "Instructors"
    EMPLOYEES = "employees", "Employees"
    DEPARTMENTS = "departments", "Departments"
    TEAMS = "teams", "Teams"
    COHORTS = "cohorts", "Cohorts"
    SKILLS = "skills", "Skills"
    COURSES = "courses", "Courses"
    COURSE_ASSIGNMENTS = "course_assignments", "Course Assignments"
    COHORT_ASSIGNMENTS = "cohort_assignments", "Cohort Assignments"


class BulkImportJob(BaseModel):
    class Status(models.TextChoices):
        PREVIEWED = "previewed", "Previewed"
        QUEUED = "queued", "Queued"
        VALIDATING = "validating", "Validating"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        FAILED_VALIDATION = "failed_validation", "Failed Validation"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="bulk_imports")
    import_type = models.CharField(max_length=40, choices=BulkImportType.choices)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PREVIEWED, db_index=True)
    source_filename = models.CharField(max_length=255, blank=True, default="")
    source_content = models.TextField(blank=True, default="")
    preview_rows = models.JSONField(default=list, blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    required_columns = models.JSONField(default=list, blank=True)
    error_report = models.JSONField(default=list, blank=True)
    partial_success_report = models.JSONField(default=list, blank=True)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    retry_count = models.PositiveIntegerField(default=0)
    failure_reason = models.TextField(blank=True, default="")
    summary_file = models.FileField(upload_to=organization_export_upload_path, blank=True, default="")
    error_file = models.FileField(upload_to=organization_export_upload_path, blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "organization_bulk_import_jobs"
        indexes = [models.Index(fields=["organization", "import_type", "status"], name="org_bulk_type_status_idx")]


class DataExportJob(BaseModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="data_exports")
    export_type = models.CharField(max_length=40)
    file_format = models.CharField(max_length=10, default="csv")
    row_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.QUEUED, db_index=True)
    file = models.FileField(upload_to=organization_export_upload_path, blank=True, default="")
    file_name = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=100, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    retry_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    failure_reason = models.TextField(blank=True, default="")
    retention_days = models.PositiveIntegerField(default=30)
    legal_hold = models.BooleanField(default=False, db_index=True)
    file_deleted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "organization_data_export_jobs"


class EnterpriseReportJob(BaseModel):
    class ReportType(models.TextChoices):
        ENROLLMENT = "enrollment", "Enrollment"
        ENROLLMENT_REPORT = "enrollment_report", "Enrollment Report"
        PLACEMENT = "placement", "Placement"
        PLACEMENT_REPORT = "placement_report", "Placement Report"
        HIRING = "hiring", "Hiring"
        HIRING_REPORT = "hiring_report", "Hiring Report"
        RECRUITER_ACTIVITY = "recruiter_activity", "Recruiter Activity"
        RECRUITER_ACTIVITY_REPORT = "recruiter_activity_report", "Recruiter Activity Report"
        CERTIFICATE_COMPLETION = "certificate_completion", "Certificate Completion"
        CERTIFICATE_COMPLETION_REPORT = "certificate_completion_report", "Certificate Completion Report"
        COURSE_COMPLETION = "course_completion", "Course Completion"
        COURSE_COMPLETION_REPORT = "course_completion_report", "Course Completion Report"
        DEPARTMENT_SUMMARY = "department_summary", "Department Summary"
        DEPARTMENT_SUMMARY_REPORT = "department_summary_report", "Department Summary Report"
        COHORT_SUMMARY = "cohort_summary", "Cohort Summary"
        COHORT_SUMMARY_REPORT = "cohort_summary_report", "Cohort Summary Report"
        ORGANIZATION_SUMMARY = "organization_summary", "Organization Summary"
        ORGANIZATION_SUMMARY_REPORT = "organization_summary_report", "Organization Summary Report"
        ENGAGEMENT_SUMMARY = "engagement_summary", "Engagement Summary"
        ENGAGEMENT_SUMMARY_REPORT = "engagement_summary_report", "Engagement Summary Report"
        EXPORT_SUMMARY_REPORT = "export_summary_report", "Export Summary Report"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="enterprise_reports")
    report_type = models.CharField(max_length=50, choices=ReportType.choices)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.QUEUED, db_index=True)
    export_job = models.ForeignKey(DataExportJob, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    retry_count = models.PositiveIntegerField(default=0)
    failure_reason = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "organization_enterprise_report_jobs"
        indexes = [
            models.Index(fields=["organization", "report_type", "status"], name="org_report_type_status_idx"),
        ]


class EnterpriseWorkerStatus(BaseModel):
    worker_key = models.CharField(max_length=100, db_index=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="worker_statuses",
        null=True,
        blank=True,
    )
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    last_successful_run_at = models.DateTimeField(null=True, blank=True)
    last_failed_run_at = models.DateTimeField(null=True, blank=True)
    average_duration_seconds = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    retry_count = models.PositiveIntegerField(default=0)
    stuck_job_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_enterprise_worker_statuses"
        unique_together = [("worker_key", "organization")]
        indexes = [
            models.Index(fields=["organization", "worker_key"], name="org_worker_key_idx"),
            models.Index(fields=["last_heartbeat_at"], name="org_worker_heartbeat_idx"),
        ]
