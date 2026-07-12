import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.careers.models import Portfolio, PortfolioSkill
from apps.courses.models import Course, Enrollment
from apps.organizations.models import (
    BulkImportJob,
    Cohort,
    CohortMember,
    DataExportJob,
    Department,
    DepartmentMember,
    EnterpriseReportJob,
    EnterpriseWorkerStatus,
    Organization,
    OrganizationMembership,
    OrganizationPolicy,
    OrganizationProfile,
    OrganizationRole,
    OrganizationTeam,
    TeamMember,
    OrganizationType,
)
from common.permission_service import PermissionService
from apps.organizations.services import EnterpriseOrganizationService
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def enterprise_org():
    admin = UserFactory(role="company_admin")
    student = UserFactory(email="learner@example.com")
    outsider = UserFactory()
    organization = Organization.objects.create(
        name="Enterprise Co",
        organization_type=OrganizationType.ENTERPRISE,
        status="active",
        created_by=admin,
    )
    admin_membership = OrganizationMembership.objects.create(
        organization=organization,
        user=admin,
        role=OrganizationRole.COMPANY_ADMIN,
    )
    student_membership = OrganizationMembership.objects.create(
        organization=organization,
        user=student,
        role=OrganizationRole.STUDENT,
    )
    return {
        "admin": admin,
        "student": student,
        "outsider": outsider,
        "organization": organization,
        "admin_membership": admin_membership,
        "student_membership": student_membership,
    }


def test_enterprise_dashboard_returns_hierarchy_branding_policy(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])
    Department.objects.create(organization=enterprise_org["organization"], name="Data")

    response = api_client.get(reverse("organizations:enterprise-dashboard", args=[enterprise_org["organization"].id]))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["organization"]["id"] == str(enterprise_org["organization"].id)
    assert data["hierarchy"]["departments"] == 1
    assert "analytics" in data
    assert data["can_manage"] is True


def test_enterprise_dashboard_denies_non_admin_member(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["student"])

    response = api_client.get(reverse("organizations:enterprise-dashboard", args=[enterprise_org["organization"].id]))

    assert response.status_code == 403


def test_report_viewer_can_view_dashboard_but_cannot_update_branding(api_client, enterprise_org):
    viewer = UserFactory(role="student")
    OrganizationMembership.objects.create(
        organization=enterprise_org["organization"],
        user=viewer,
        role=OrganizationRole.REPORT_VIEWER,
    )
    api_client.force_authenticate(user=viewer)

    dashboard = api_client.get(reverse("organizations:enterprise-dashboard", args=[enterprise_org["organization"].id]))
    update = api_client.patch(
        reverse("organizations:enterprise-branding", args=[enterprise_org["organization"].id]),
        {"primary_color": "#111111"},
        format="json",
    )

    assert dashboard.status_code == 200
    assert update.status_code == 403


def test_enterprise_branding_update_requires_org_admin(api_client, enterprise_org):
    url = reverse("organizations:enterprise-branding", args=[enterprise_org["organization"].id])
    api_client.force_authenticate(user=enterprise_org["student"])

    denied = api_client.patch(url, {"primary_color": "#2255aa"}, format="json")

    assert denied.status_code == 403

    api_client.force_authenticate(user=enterprise_org["admin"])
    allowed = api_client.patch(
        url,
        {"primary_color": "#2255aa", "support_email": "support@example.com"},
        format="json",
    )

    assert allowed.status_code == 200
    profile = OrganizationProfile.objects.get(organization=enterprise_org["organization"])
    assert profile.primary_color == "#2255aa"
    assert AuditLog.objects.filter(action="organization_profile_updated", organization_id=enterprise_org["organization"].id).exists()


def test_enterprise_policy_update_is_scoped(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])

    response = api_client.patch(
        reverse("organizations:enterprise-policies", args=[enterprise_org["organization"].id]),
        {"mfa_required": True, "allowed_email_domains": ["example.com"]},
        format="json",
    )

    assert response.status_code == 200
    policy = OrganizationPolicy.objects.get(organization=enterprise_org["organization"])
    assert policy.mfa_required is True
    assert policy.allowed_email_domains == ["example.com"]


def test_department_crud_and_member_assignment_are_tenant_scoped(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])

    created = api_client.post(
        reverse("organizations:enterprise-departments", args=[enterprise_org["organization"].id]),
        {"name": "Career Services", "description": "Placement operations"},
        format="json",
    )

    assert created.status_code == 201
    department_id = created.json()["data"]["id"]

    assigned = api_client.post(
        reverse("organizations:enterprise-department-members", args=[enterprise_org["organization"].id, department_id]),
        {"membership_id": str(enterprise_org["student_membership"].id), "role": "member"},
        format="json",
    )

    assert assigned.status_code == 200
    assert DepartmentMember.objects.filter(department_id=department_id, membership=enterprise_org["student_membership"]).exists()

    other_org = Organization.objects.create(name="Other Org", organization_type=OrganizationType.COMPANY)
    other_member = OrganizationMembership.objects.create(
        organization=other_org,
        user=enterprise_org["outsider"],
        role=OrganizationRole.STUDENT,
    )
    denied = api_client.post(
        reverse("organizations:enterprise-department-members", args=[enterprise_org["organization"].id, department_id]),
        {"membership_id": str(other_member.id), "role": "member"},
        format="json",
    )

    assert denied.status_code == 404


def test_scoped_managers_can_manage_only_assigned_hierarchy_records(api_client, enterprise_org):
    dept_manager_user = UserFactory(role="student")
    team_manager_user = UserFactory(role="student")
    cohort_manager_user = UserFactory(role="student")
    dept_membership = OrganizationMembership.objects.create(
        organization=enterprise_org["organization"],
        user=dept_manager_user,
        role=OrganizationRole.DEPARTMENT_MANAGER,
    )
    team_membership = OrganizationMembership.objects.create(
        organization=enterprise_org["organization"],
        user=team_manager_user,
        role=OrganizationRole.TEAM_MANAGER,
    )
    cohort_membership = OrganizationMembership.objects.create(
        organization=enterprise_org["organization"],
        user=cohort_manager_user,
        role=OrganizationRole.COHORT_MANAGER,
    )
    department = Department.objects.create(organization=enterprise_org["organization"], name="Managed Department")
    other_department = Department.objects.create(organization=enterprise_org["organization"], name="Other Department")
    team = OrganizationTeam.objects.create(organization=enterprise_org["organization"], name="Managed Team")
    cohort = Cohort.objects.create(organization=enterprise_org["organization"], name="Managed Cohort")
    DepartmentMember.objects.create(department=department, membership=dept_membership, role="manager")
    TeamMember.objects.create(team=team, membership=team_membership, role="manager")
    CohortMember.objects.create(cohort=cohort, membership=cohort_membership, role="manager")

    api_client.force_authenticate(user=dept_manager_user)
    allowed = api_client.patch(
        reverse("organizations:enterprise-department-detail", args=[enterprise_org["organization"].id, department.id]),
        {"description": "Updated by scoped manager"},
        format="json",
    )
    denied = api_client.patch(
        reverse("organizations:enterprise-department-detail", args=[enterprise_org["organization"].id, other_department.id]),
        {"description": "Denied"},
        format="json",
    )

    assert allowed.status_code == 200
    assert denied.status_code == 403
    assert PermissionService.can_manage_team(team_manager_user, team)
    assert PermissionService.can_manage_cohort(cohort_manager_user, cohort)


def test_team_and_cohort_endpoints(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])

    team = api_client.post(
        reverse("organizations:enterprise-teams", args=[enterprise_org["organization"].id]),
        {"name": "Recruiting Ops", "team_type": "recruiting", "manager": str(enterprise_org["admin_membership"].id)},
        format="json",
    )
    cohort = api_client.post(
        reverse("organizations:enterprise-cohorts", args=[enterprise_org["organization"].id]),
        {"name": "Data Analyst 2026", "program": "Data Analytics", "graduation_year": 2026},
        format="json",
    )

    assert team.status_code == 201
    assert cohort.status_code == 201

    team_member = api_client.post(
        reverse("organizations:enterprise-team-members", args=[enterprise_org["organization"].id, team.json()["data"]["id"]]),
        {"membership_id": str(enterprise_org["student_membership"].id), "role": "member"},
        format="json",
    )
    cohort_member = api_client.post(
        reverse("organizations:enterprise-cohort-members", args=[enterprise_org["organization"].id, cohort.json()["data"]["id"]]),
        {"membership_id": str(enterprise_org["student_membership"].id), "role": "member"},
        format="json",
    )

    assert team_member.status_code == 200
    assert cohort_member.status_code == 200
    assert OrganizationTeam.objects.filter(name="Recruiting Ops").exists()
    assert Cohort.objects.filter(name="Data Analyst 2026").exists()


def test_bulk_import_preview_commit_and_export(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])
    csv_content = "email,full_name\nbulk@example.com,Bulk Learner\n"

    preview = api_client.post(
        reverse("organizations:enterprise-bulk-import", args=[enterprise_org["organization"].id]),
        {"import_type": "students", "csv_content": csv_content, "source_filename": "students.csv", "commit": False},
        format="json",
    )

    assert preview.status_code == 201
    assert preview.json()["data"]["status"] == "previewed"
    assert not OrganizationMembership.objects.filter(user__email="bulk@example.com").exists()

    committed = api_client.post(
        reverse("organizations:enterprise-bulk-import", args=[enterprise_org["organization"].id]),
        {"import_type": "students", "csv_content": csv_content, "source_filename": "students.csv", "commit": True},
        format="json",
    )

    assert committed.status_code == 201
    assert BulkImportJob.objects.filter(status="completed", success_count=1).exists()
    assert OrganizationMembership.objects.filter(
        organization=enterprise_org["organization"],
        user__email="bulk@example.com",
        role=OrganizationRole.STUDENT,
    ).exists()

    export = api_client.post(
        reverse("organizations:enterprise-exports", args=[enterprise_org["organization"].id]),
        {"export_type": "students", "file_format": "csv"},
        format="json",
    )

    assert export.status_code == 202
    export_id = export.json()["data"]["id"]
    call_command("process_data_exports", limit=10)
    export_job = DataExportJob.objects.get(id=export_id)
    assert export_job.status == DataExportJob.Status.COMPLETED
    assert export_job.file
    assert "bulk@example.com" in export_job.file.open("rb").read().decode("utf-8")


def test_branding_upload_validation(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])
    image = SimpleUploadedFile(
        "logo.png",
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82",
        content_type="image/png",
    )

    response = api_client.post(
        reverse("organizations:enterprise-branding-upload", args=[enterprise_org["organization"].id]),
        {"asset_type": "logo", "file": image},
        format="multipart",
    )

    assert response.status_code == 200
    assert OrganizationProfile.objects.get(organization=enterprise_org["organization"]).logo


def test_export_manager_can_export_but_not_change_policies(api_client, enterprise_org):
    export_user = UserFactory(role="student")
    OrganizationMembership.objects.create(
        organization=enterprise_org["organization"],
        user=export_user,
        role=OrganizationRole.EXPORT_MANAGER,
    )
    api_client.force_authenticate(user=export_user)

    export = api_client.post(
        reverse("organizations:enterprise-exports", args=[enterprise_org["organization"].id]),
        {"export_type": "students", "file_format": "xlsx"},
        format="json",
    )
    policy = api_client.patch(
        reverse("organizations:enterprise-policies", args=[enterprise_org["organization"].id]),
        {"mfa_required": True},
        format="json",
    )

    assert export.status_code == 202
    assert policy.status_code == 403
    call_command("process_data_exports", limit=10)
    export_job = DataExportJob.objects.get(id=export.json()["data"]["id"])
    assert export_job.file_name.endswith(".xlsx")
    assert export_job.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_audit_log_export_requires_export_manager_or_platform_admin(api_client, enterprise_org):
    report_user = UserFactory(role="student")
    OrganizationMembership.objects.create(
        organization=enterprise_org["organization"],
        user=report_user,
        role=OrganizationRole.REPORT_VIEWER,
    )
    api_client.force_authenticate(user=report_user)

    response = api_client.post(
        reverse("organizations:enterprise-exports", args=[enterprise_org["organization"].id]),
        {"export_type": "audit_logs", "file_format": "csv"},
        format="json",
    )

    assert response.status_code == 403


def test_bulk_import_template_endpoint(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])

    response = api_client.get(
        reverse("organizations:enterprise-import-template", args=[enterprise_org["organization"].id]),
        {"import_type": "cohorts"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["required_columns"] == ["name"]


def test_enterprise_role_management_endpoint(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])

    response = api_client.post(
        reverse("organizations:enterprise-roles", args=[enterprise_org["organization"].id]),
        {"membership_id": str(enterprise_org["student_membership"].id), "role": OrganizationRole.REPORT_VIEWER},
        format="json",
    )

    assert response.status_code == 200
    enterprise_org["student_membership"].refresh_from_db()
    assert enterprise_org["student_membership"].role == OrganizationRole.REPORT_VIEWER


def test_enterprise_audit_center_filters_events(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])
    AuditLog.objects.create(
        actor=enterprise_org["admin"],
        action="organization_test_event",
        target_type="Organization",
        target_id=str(enterprise_org["organization"].id),
        organization_id=enterprise_org["organization"].id,
    )

    response = api_client.get(
        reverse("organizations:enterprise-audit-center", args=[enterprise_org["organization"].id]),
        {"action": "test_event"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1


def test_enterprise_report_generation(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])

    response = api_client.post(
        reverse("organizations:enterprise-reports", args=[enterprise_org["organization"].id]),
        {"report_type": EnterpriseReportJob.ReportType.ORGANIZATION_SUMMARY},
        format="json",
    )

    assert response.status_code == 202
    report = EnterpriseReportJob.objects.get(id=response.json()["data"]["id"])
    assert report.status == EnterpriseReportJob.Status.COMPLETED
    assert report.export_job is not None


def test_export_retention_marks_expired(api_client, enterprise_org):
    export_job = DataExportJob.objects.create(
        organization=enterprise_org["organization"],
        export_type="students",
        file_format="csv",
        status=DataExportJob.Status.COMPLETED,
        expires_at=timezone.now() - timezone.timedelta(days=1),
        created_by=enterprise_org["admin"],
    )

    expired = EnterpriseOrganizationService.expire_exports(organization=enterprise_org["organization"])

    export_job.refresh_from_db()
    assert expired == 1
    assert export_job.status == DataExportJob.Status.EXPIRED


def test_organization_lifecycle_suspend_and_reactivate(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])

    suspend = api_client.post(
        reverse("organizations:enterprise-lifecycle", args=[enterprise_org["organization"].id]),
        {"action": "suspend"},
        format="json",
    )
    reactivate = api_client.post(
        reverse("organizations:enterprise-lifecycle", args=[enterprise_org["organization"].id]),
        {"action": "reactivate"},
        format="json",
    )

    assert suspend.status_code == 200
    assert reactivate.status_code == 200
    enterprise_org["organization"].refresh_from_db()
    assert enterprise_org["organization"].status == "active"


@pytest.mark.parametrize("report_type", [
    "enrollment_report",
    "placement_report",
    "hiring_report",
    "recruiter_activity_report",
    "certificate_completion_report",
    "course_completion_report",
    "department_summary_report",
    "cohort_summary_report",
    "organization_summary_report",
    "engagement_summary_report",
    "export_summary_report",
])
def test_enterprise_report_types_generate_real_export_rows(api_client, enterprise_org, report_type):
    course = Course.objects.create(instructor=enterprise_org["admin"], title=f"Course {report_type}", status="published")
    Enrollment.objects.create(user=enterprise_org["student"], course=course)
    DataExportJob.objects.create(organization=enterprise_org["organization"], export_type="students", file_format="csv")
    api_client.force_authenticate(user=enterprise_org["admin"])

    response = api_client.post(
        reverse("organizations:enterprise-reports", args=[enterprise_org["organization"].id]),
        {"report_type": report_type, "file_format": "csv"},
        format="json",
    )

    assert response.status_code == 202
    report = EnterpriseReportJob.objects.get(id=response.json()["data"]["id"])
    assert report.status == EnterpriseReportJob.Status.COMPLETED
    assert report.export_job.row_count >= 0
    assert report.export_job.file_name.endswith(".csv")


def test_import_materializes_skills_courses_assignments_and_files(api_client, enterprise_org):
    instructor = UserFactory(email="teacher@example.com")
    OrganizationMembership.objects.create(organization=enterprise_org["organization"], user=instructor, role=OrganizationRole.INSTRUCTOR)
    api_client.force_authenticate(user=enterprise_org["admin"])

    skill_response = api_client.post(
        reverse("organizations:enterprise-bulk-import", args=[enterprise_org["organization"].id]),
        {"import_type": "skills", "csv_content": "email,skill\nlearner@example.com,Django\n", "commit": True},
        format="json",
    )
    course_response = api_client.post(
        reverse("organizations:enterprise-bulk-import", args=[enterprise_org["organization"].id]),
        {"import_type": "courses", "csv_content": "title,instructor_email\nEnterprise Django,teacher@example.com\n", "commit": True},
        format="json",
    )
    course = Course.objects.get(title="Enterprise Django")
    assignment_response = api_client.post(
        reverse("organizations:enterprise-bulk-import", args=[enterprise_org["organization"].id]),
        {"import_type": "course_assignments", "csv_content": f"email,course_id\nlearner@example.com,{course.id}\n", "commit": True},
        format="json",
    )

    assert skill_response.status_code == 201
    assert course_response.status_code == 201
    assert assignment_response.status_code == 201
    assert PortfolioSkill.objects.filter(portfolio__user=enterprise_org["student"], name="Django").exists()
    assert Enrollment.objects.filter(user=enterprise_org["student"], course=course).exists()
    job = BulkImportJob.objects.get(id=assignment_response.json()["data"]["id"])
    assert job.summary_file
    assert job.error_file


def test_import_error_file_download_is_tenant_scoped(api_client, enterprise_org):
    job = BulkImportJob.objects.create(
        organization=enterprise_org["organization"],
        import_type="students",
        status=BulkImportJob.Status.FAILED_VALIDATION,
        created_by=enterprise_org["admin"],
    )
    job.error_file.save("errors.csv", ContentFile(b"row,field,message\n1,email,Missing\n"), save=True)
    other_admin = UserFactory(role="company_admin")
    other_org = Organization.objects.create(name="Other Enterprise", organization_type=OrganizationType.ENTERPRISE)
    OrganizationMembership.objects.create(organization=other_org, user=other_admin, role=OrganizationRole.COMPANY_ADMIN)

    api_client.force_authenticate(user=other_admin)
    response = api_client.get(reverse("organizations:enterprise-import-file-download", args=[other_org.id, job.id, "errors"]))

    assert response.status_code == 404


def test_tenant_isolation_denies_cross_org_reports_and_exports(api_client, enterprise_org):
    other_admin = UserFactory(role="company_admin")
    other_org = Organization.objects.create(name="Tenant B", organization_type=OrganizationType.ENTERPRISE)
    OrganizationMembership.objects.create(organization=other_org, user=other_admin, role=OrganizationRole.COMPANY_ADMIN)
    export = DataExportJob.objects.create(
        organization=enterprise_org["organization"],
        export_type="students",
        file_format="csv",
        status=DataExportJob.Status.COMPLETED,
        created_by=enterprise_org["admin"],
    )
    export.file.save("students.csv", ContentFile(b"email\nlearner@example.com\n"), save=True)
    api_client.force_authenticate(user=other_admin)

    reports = api_client.get(reverse("organizations:enterprise-reports", args=[enterprise_org["organization"].id]))
    download = api_client.get(reverse("organizations:enterprise-export-download", args=[other_org.id, export.id]))

    assert reports.status_code == 403
    assert download.status_code == 404


def test_audit_center_filters_severity_prefix_and_target(api_client, enterprise_org):
    api_client.force_authenticate(user=enterprise_org["admin"])
    AuditLog.objects.create(
        actor=enterprise_org["admin"],
        action="organization_export_deleted",
        target_type="DataExportJob",
        target_id="abc",
        organization_id=enterprise_org["organization"].id,
        metadata={"severity": "critical"},
    )
    AuditLog.objects.create(
        actor=enterprise_org["admin"],
        action="organization_member_added",
        target_type="OrganizationMembership",
        target_id="def",
        organization_id=enterprise_org["organization"].id,
        metadata={"severity": "info"},
    )

    response = api_client.get(
        reverse("organizations:enterprise-audit-center", args=[enterprise_org["organization"].id]),
        {"action_prefix": "organization_export", "severity": "critical", "target_type": "DataExportJob", "target_id": "abc"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1


def test_worker_status_and_stuck_job_detection(api_client, enterprise_org):
    report = EnterpriseReportJob.objects.create(
        organization=enterprise_org["organization"],
        report_type="organization_summary_report",
        status=EnterpriseReportJob.Status.PROCESSING,
        created_by=enterprise_org["admin"],
    )
    EnterpriseReportJob.objects.filter(id=report.id).update(updated_at=timezone.now() - timezone.timedelta(hours=2))
    api_client.force_authenticate(user=enterprise_org["admin"])

    response = api_client.get(reverse("organizations:enterprise-worker-jobs", args=[enterprise_org["organization"].id]))

    assert response.status_code == 200
    assert response.json()["data"]["stuck_counts"]["reports"] == 1
    assert EnterpriseWorkerStatus.objects.filter(organization=enterprise_org["organization"]).exists()


def test_retention_cleanup_respects_legal_hold(enterprise_org):
    held = DataExportJob.objects.create(
        organization=enterprise_org["organization"],
        export_type="students",
        file_format="csv",
        status=DataExportJob.Status.COMPLETED,
        expires_at=timezone.now() - timezone.timedelta(days=1),
        legal_hold=True,
        created_by=enterprise_org["admin"],
    )
    expired = EnterpriseOrganizationService.expire_exports(organization=enterprise_org["organization"], delete_files=True)

    held.refresh_from_db()
    assert expired == 0
    assert held.status == DataExportJob.Status.COMPLETED
