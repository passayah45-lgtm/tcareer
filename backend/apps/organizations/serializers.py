from rest_framework import serializers

from apps.organizations.models import (
    BulkImportJob,
    BulkImportType,
    Cohort,
    CohortMember,
    DataExportJob,
    Department,
    DepartmentMember,
    EnterpriseRole,
    EnterpriseReportJob,
    EnterpriseWorkerStatus,
    MembershipStatus,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationPolicy,
    OrganizationProfile,
    OrganizationTeam,
    TeamMember,
)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "organization_type",
            "status",
            "website_url",
            "country_code",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "status", "created_at", "updated_at"]


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name", "organization_type", "website_url", "country_code"]


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "organization",
            "user",
            "user_email",
            "user_full_name",
            "role",
            "status",
            "invited_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "user", "invited_by", "created_at", "updated_at"]


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = [
            "id",
            "organization",
            "email",
            "role",
            "invited_by",
            "expires_at",
            "accepted_at",
            "revoked_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "invited_by",
            "expires_at",
            "accepted_at",
            "revoked_at",
            "created_at",
        ]


class OrganizationInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership._meta.get_field("role").choices)


class OrganizationRoleChangeSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=OrganizationMembership._meta.get_field("role").choices)


class OrganizationMemberRemoveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[MembershipStatus.REMOVED],
        default=MembershipStatus.REMOVED,
    )


class OrganizationInvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256)


class OrganizationProfileSerializer(serializers.ModelSerializer):
    logo_file_url = serializers.SerializerMethodField()
    banner_file_url = serializers.SerializerMethodField()
    favicon_file_url = serializers.SerializerMethodField()
    certificate_logo_file_url = serializers.SerializerMethodField()
    email_header_image_file_url = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationProfile
        exclude = ["organization"]
        read_only_fields = [
            "id",
            "logo",
            "banner",
            "favicon",
            "certificate_logo",
            "email_header_image",
            "logo_file_url",
            "banner_file_url",
            "favicon_file_url",
            "certificate_logo_file_url",
            "email_header_image_file_url",
            "created_at",
            "updated_at",
        ]

    def _file_url(self, obj, field_name):
        file_obj = getattr(obj, field_name)
        return file_obj.url if file_obj else ""

    def get_logo_file_url(self, obj):
        return self._file_url(obj, "logo")

    def get_banner_file_url(self, obj):
        return self._file_url(obj, "banner")

    def get_favicon_file_url(self, obj):
        return self._file_url(obj, "favicon")

    def get_certificate_logo_file_url(self, obj):
        return self._file_url(obj, "certificate_logo")

    def get_email_header_image_file_url(self, obj):
        return self._file_url(obj, "email_header_image")


class OrganizationPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPolicy
        exclude = ["organization"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DepartmentMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="membership.user.email", read_only=True)
    user_full_name = serializers.CharField(source="membership.user.full_name", read_only=True)

    class Meta:
        model = DepartmentMember
        fields = ["id", "membership", "user_email", "user_full_name", "role", "created_at"]
        read_only_fields = ["id", "created_at"]


class DepartmentSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    members = DepartmentMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "description", "status", "metadata", "member_count", "members", "created_at", "updated_at"]
        read_only_fields = ["id", "member_count", "members", "created_at", "updated_at"]


class DepartmentMemberWriteSerializer(serializers.Serializer):
    membership_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=EnterpriseRole.choices, default=EnterpriseRole.MEMBER)


class TeamMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="membership.user.email", read_only=True)
    user_full_name = serializers.CharField(source="membership.user.full_name", read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "membership", "user_email", "user_full_name", "role", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrganizationTeamSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    manager_email = serializers.EmailField(source="manager.user.email", read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = OrganizationTeam
        fields = [
            "id",
            "name",
            "team_type",
            "manager",
            "manager_email",
            "status",
            "permissions",
            "metadata",
            "member_count",
            "members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "manager_email", "member_count", "members", "created_at", "updated_at"]


class TeamMemberWriteSerializer(serializers.Serializer):
    membership_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=EnterpriseRole.choices, default=EnterpriseRole.MEMBER)


class CohortMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="membership.user.email", read_only=True)
    user_full_name = serializers.CharField(source="membership.user.full_name", read_only=True)

    class Meta:
        model = CohortMember
        fields = ["id", "membership", "user_email", "user_full_name", "role", "created_at"]
        read_only_fields = ["id", "created_at"]


class CohortSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    progress_summary = serializers.DictField(read_only=True)
    members = CohortMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Cohort
        fields = [
            "id",
            "name",
            "academic_year",
            "semester",
            "batch",
            "program",
            "graduation_year",
            "status",
            "enrollment_starts_at",
            "enrollment_ends_at",
            "assigned_course_ids",
            "metadata",
            "member_count",
            "progress_summary",
            "members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "member_count", "progress_summary", "members", "created_at", "updated_at"]


class CohortMemberWriteSerializer(serializers.Serializer):
    membership_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=EnterpriseRole.choices, default=EnterpriseRole.MEMBER)


class BulkImportPreviewSerializer(serializers.Serializer):
    import_type = serializers.ChoiceField(choices=BulkImportType.choices)
    csv_content = serializers.CharField()
    source_filename = serializers.CharField(required=False, allow_blank=True, default="")
    commit = serializers.BooleanField(default=False)


class OrganizationLifecycleSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=[
        ("archive", "Archive"),
        ("suspend", "Suspend"),
        ("reactivate", "Reactivate"),
        ("soft_delete", "Soft Delete"),
        ("transfer_ownership", "Transfer Ownership"),
    ])
    owner_id = serializers.UUIDField(required=False)
    metadata = serializers.DictField(required=False, default=dict)


class EnterpriseRoleAssignmentSerializer(serializers.Serializer):
    membership_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=OrganizationMembership._meta.get_field("role").choices)


class EnterpriseAuditFilterSerializer(serializers.Serializer):
    action = serializers.CharField(required=False, allow_blank=True)
    action_prefix = serializers.CharField(required=False, allow_blank=True)
    severity = serializers.CharField(required=False, allow_blank=True)
    actor = serializers.UUIDField(required=False)
    user_id = serializers.UUIDField(required=False)
    target_type = serializers.CharField(required=False, allow_blank=True)
    target_id = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    q = serializers.CharField(required=False, allow_blank=True)
    file_format = serializers.ChoiceField(choices=[("json", "JSON"), ("csv", "CSV"), ("xlsx", "XLSX")], default="json")


class EnterpriseReportCreateSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=EnterpriseReportJob.ReportType.choices)
    file_format = serializers.ChoiceField(choices=[("csv", "CSV"), ("xlsx", "XLSX")], default="xlsx")


class BrandingAssetUploadSerializer(serializers.Serializer):
    asset_type = serializers.ChoiceField(choices=[
        ("logo", "Logo"),
        ("banner", "Banner"),
        ("favicon", "Favicon"),
        ("certificate_logo", "Certificate Logo"),
        ("email_header_image", "Email Header Image"),
    ])
    file = serializers.FileField()


class ImportTemplateSerializer(serializers.Serializer):
    import_type = serializers.ChoiceField(choices=BulkImportType.choices)


class BulkImportJobSerializer(serializers.ModelSerializer):
    summary_file_url = serializers.SerializerMethodField()
    error_file_url = serializers.SerializerMethodField()

    class Meta:
        model = BulkImportJob
        fields = [
            "id",
            "import_type",
            "status",
            "source_filename",
            "preview_rows",
            "validation_errors",
            "required_columns",
            "error_report",
            "partial_success_report",
            "success_count",
            "error_count",
            "progress_percentage",
            "started_at",
            "completed_at",
            "failed_at",
            "duration_seconds",
            "retry_count",
            "failure_reason",
            "summary_file_url",
            "error_file_url",
            "created_at",
        ]
        read_only_fields = fields

    def get_summary_file_url(self, obj):
        return obj.summary_file.url if obj.summary_file else ""

    def get_error_file_url(self, obj):
        return obj.error_file.url if obj.error_file else ""


class DataExportSerializer(serializers.Serializer):
    export_type = serializers.ChoiceField(choices=[
        ("students", "Students"),
        ("recruiters", "Recruiters"),
        ("applications", "Applications"),
        ("certificates", "Certificates"),
        ("courses", "Courses"),
        ("audit_logs", "Audit Logs"),
        ("analytics_summary", "Analytics Summary"),
        ("enrollment_report", "Enrollment Report"),
        ("placement_report", "Placement Report"),
        ("hiring_report", "Hiring Report"),
        ("recruiter_activity_report", "Recruiter Activity Report"),
        ("certificate_completion_report", "Certificate Completion Report"),
        ("course_completion_report", "Course Completion Report"),
        ("department_summary_report", "Department Summary Report"),
        ("cohort_summary_report", "Cohort Summary Report"),
        ("organization_summary_report", "Organization Summary Report"),
        ("engagement_summary_report", "Engagement Summary Report"),
        ("export_summary_report", "Export Summary Report"),
    ])
    file_format = serializers.ChoiceField(choices=[("csv", "CSV"), ("xlsx", "XLSX")], default="csv")


class DataExportJobSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DataExportJob
        fields = [
            "id",
            "export_type",
            "file_format",
            "row_count",
            "status",
            "file_name",
            "file_url",
            "content_type",
            "file_size",
            "progress_percentage",
            "started_at",
            "completed_at",
            "failed_at",
            "expires_at",
            "deleted_at",
            "duration_seconds",
            "retry_count",
            "download_count",
            "last_downloaded_at",
            "last_error",
            "failure_reason",
            "retention_days",
            "legal_hold",
            "file_deleted_at",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_file_url(self, obj):
        return obj.file.url if obj.file else ""


class EnterpriseReportJobSerializer(serializers.ModelSerializer):
    export = DataExportJobSerializer(source="export_job", read_only=True)

    class Meta:
        model = EnterpriseReportJob
        fields = [
            "id",
            "report_type",
            "status",
            "progress_percentage",
            "started_at",
            "completed_at",
            "failed_at",
            "duration_seconds",
            "retry_count",
            "failure_reason",
            "metadata",
            "export",
            "created_at",
        ]
        read_only_fields = fields


class EnterpriseWorkerStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseWorkerStatus
        fields = [
            "id",
            "worker_key",
            "last_heartbeat_at",
            "last_successful_run_at",
            "last_failed_run_at",
            "average_duration_seconds",
            "failure_count",
            "retry_count",
            "stuck_job_count",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
