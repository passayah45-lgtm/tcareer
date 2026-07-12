from django.urls import path

from apps.organizations import views

app_name = "organizations"

urlpatterns = [
    path("", views.organization_list_create, name="organization-list-create"),
    path("invitations/accept/", views.organization_invitation_accept, name="organization-invitation-accept"),
    path("<uuid:organization_id>/", views.organization_detail, name="organization-detail"),
    path("<uuid:organization_id>/enterprise/dashboard/", views.enterprise_dashboard, name="enterprise-dashboard"),
    path("<uuid:organization_id>/enterprise/settings/", views.enterprise_settings, name="enterprise-settings"),
    path("<uuid:organization_id>/enterprise/lifecycle/", views.enterprise_lifecycle, name="enterprise-lifecycle"),
    path("<uuid:organization_id>/enterprise/roles/", views.enterprise_roles, name="enterprise-roles"),
    path("<uuid:organization_id>/enterprise/audit/", views.enterprise_audit_center, name="enterprise-audit-center"),
    path("<uuid:organization_id>/enterprise/worker-jobs/", views.enterprise_worker_jobs, name="enterprise-worker-jobs"),
    path("<uuid:organization_id>/enterprise/branding/", views.enterprise_branding, name="enterprise-branding"),
    path("<uuid:organization_id>/enterprise/branding/upload/", views.enterprise_branding_upload, name="enterprise-branding-upload"),
    path("<uuid:organization_id>/enterprise/policies/", views.enterprise_policies, name="enterprise-policies"),
    path("<uuid:organization_id>/enterprise/departments/", views.enterprise_departments, name="enterprise-departments"),
    path(
        "<uuid:organization_id>/enterprise/departments/<uuid:department_id>/",
        views.enterprise_department_detail,
        name="enterprise-department-detail",
    ),
    path(
        "<uuid:organization_id>/enterprise/departments/<uuid:department_id>/members/",
        views.enterprise_department_members,
        name="enterprise-department-members",
    ),
    path("<uuid:organization_id>/enterprise/teams/", views.enterprise_teams, name="enterprise-teams"),
    path(
        "<uuid:organization_id>/enterprise/teams/<uuid:team_id>/",
        views.enterprise_team_detail,
        name="enterprise-team-detail",
    ),
    path(
        "<uuid:organization_id>/enterprise/teams/<uuid:team_id>/members/",
        views.enterprise_team_members,
        name="enterprise-team-members",
    ),
    path("<uuid:organization_id>/enterprise/cohorts/", views.enterprise_cohorts, name="enterprise-cohorts"),
    path(
        "<uuid:organization_id>/enterprise/cohorts/<uuid:cohort_id>/",
        views.enterprise_cohort_detail,
        name="enterprise-cohort-detail",
    ),
    path(
        "<uuid:organization_id>/enterprise/cohorts/<uuid:cohort_id>/members/",
        views.enterprise_cohort_members,
        name="enterprise-cohort-members",
    ),
    path("<uuid:organization_id>/enterprise/imports/", views.enterprise_bulk_import, name="enterprise-bulk-import"),
    path("<uuid:organization_id>/enterprise/imports/jobs/", views.enterprise_import_jobs, name="enterprise-import-jobs"),
    path(
        "<uuid:organization_id>/enterprise/imports/<uuid:import_id>/<str:file_kind>/download/",
        views.enterprise_import_file_download,
        name="enterprise-import-file-download",
    ),
    path("<uuid:organization_id>/enterprise/imports/template/", views.enterprise_import_template, name="enterprise-import-template"),
    path("<uuid:organization_id>/enterprise/exports/", views.enterprise_exports, name="enterprise-exports"),
    path(
        "<uuid:organization_id>/enterprise/exports/<uuid:export_id>/download/",
        views.enterprise_export_download,
        name="enterprise-export-download",
    ),
    path(
        "<uuid:organization_id>/enterprise/exports/<uuid:export_id>/",
        views.enterprise_export_delete,
        name="enterprise-export-delete",
    ),
    path("<uuid:organization_id>/enterprise/reports/", views.enterprise_reports, name="enterprise-reports"),
    path("<uuid:organization_id>/enterprise/analytics/", views.enterprise_analytics, name="enterprise-analytics"),
    path("<uuid:organization_id>/recruiter-settings/", views.organization_recruiter_settings, name="organization-recruiter-settings"),
    path("<uuid:organization_id>/members/", views.organization_members, name="organization-members"),
    path("<uuid:organization_id>/invitations/", views.organization_invite, name="organization-invite"),
    path(
        "<uuid:organization_id>/members/<uuid:membership_id>/role/",
        views.organization_member_role,
        name="organization-member-role",
    ),
    path(
        "<uuid:organization_id>/members/<uuid:membership_id>/",
        views.organization_member_remove,
        name="organization-member-remove",
    ),
]
