from datetime import timedelta

from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes, throttle_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations.models import (
    BulkImportJob,
    Cohort,
    CohortMember,
    DataExportJob,
    Department,
    DepartmentMember,
    EnterpriseReportJob,
    EnterpriseStatus,
    EnterpriseWorkerStatus,
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationTeam,
    TeamMember,
)
from apps.audit.models import AuditLog
from common.entitlements import EntitlementService
from apps.organizations.serializers import (
    BulkImportJobSerializer,
    BulkImportPreviewSerializer,
    BrandingAssetUploadSerializer,
    CohortMemberWriteSerializer,
    CohortSerializer,
    DataExportJobSerializer,
    DataExportSerializer,
    DepartmentMemberWriteSerializer,
    DepartmentSerializer,
    EnterpriseAuditFilterSerializer,
    EnterpriseReportCreateSerializer,
    EnterpriseReportJobSerializer,
    EnterpriseRoleAssignmentSerializer,
    EnterpriseWorkerStatusSerializer,
    ImportTemplateSerializer,
    OrganizationLifecycleSerializer,
    OrganizationCreateSerializer,
    OrganizationInvitationSerializer,
    OrganizationInvitationAcceptSerializer,
    OrganizationInviteSerializer,
    OrganizationMembershipSerializer,
    OrganizationPolicySerializer,
    OrganizationProfileSerializer,
    OrganizationRoleChangeSerializer,
    OrganizationSerializer,
    OrganizationTeamSerializer,
    TeamMemberWriteSerializer,
)
from apps.users.models import User
from apps.organizations.tasks import process_data_export, process_enterprise_report
from apps.organizations.services import EnterpriseOrganizationService, OrganizationService
from common.audit import AuditService
from common.exceptions import PermissionError
from common.permission_service import PermissionService
from common.throttles import InvitationAcceptRateThrottle


def _dispatch_or_process(task, object_id, fallback):
    try:
        task.delay(str(object_id))
    except Exception:
        fallback()


def _enterprise_organization(request, organization_id, *, manage=False):
    organization = get_object_or_404(Organization, id=organization_id)
    if manage:
        EnterpriseOrganizationService.ensure_can_manage(request.user, organization)
    else:
        EnterpriseOrganizationService.ensure_can_view_reports(request.user, organization)
    return organization


def _annotated_departments(organization):
    return organization.departments.prefetch_related("members__membership__user").annotate(member_count=Count("members"))


def _annotated_teams(organization):
    return organization.teams.select_related("manager__user").prefetch_related("members__membership__user").annotate(member_count=Count("members"))


def _annotated_cohorts(organization):
    return organization.cohorts.prefetch_related("members__membership__user").annotate(member_count=Count("members"))


def _organization_membership(organization, membership_id):
    return get_object_or_404(
        OrganizationMembership.objects.select_related("user", "organization"),
        id=membership_id,
        organization=organization,
        status=MembershipStatus.ACTIVE,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def organization_list_create(request):
    if request.method == "GET":
        if PermissionService.is_platform_admin(request.user):
            organizations = Organization.objects.all().order_by("name")
        else:
            organizations = Organization.objects.filter(
                Q(memberships__user=request.user, memberships__status=MembershipStatus.ACTIVE)
                | Q(created_by=request.user)
            ).distinct().order_by("name")
        return Response(OrganizationSerializer(organizations, many=True).data)

    serializer = OrganizationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = OrganizationService.create_organization(
        actor=request.user,
        **serializer.validated_data,
    )
    return Response(OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organization_detail(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    if not PermissionService.can_view_organization(request.user, organization):
        raise PermissionError("You cannot view this organization.")
    return Response(OrganizationSerializer(organization).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organization_members(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    if not PermissionService.can_view_organization(request.user, organization):
        raise PermissionError("You cannot view this organization's members.")
    memberships = organization.memberships.select_related("user", "invited_by").order_by("user__email", "role")
    return Response(OrganizationMembershipSerializer(memberships, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organization_recruiter_settings(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    if not PermissionService.can_view_organization(request.user, organization):
        raise PermissionError("You cannot view this organization's recruiter settings.")

    entitlement = EntitlementService.get_recruiter_entitlement(organization)
    active_seats = EntitlementService.active_recruiter_seats(organization)
    max_seats = EntitlementService.max_recruiter_seats(organization)
    invitations = organization.invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).order_by("-created_at")
    audit_logs = AuditLog.objects.filter(organization_id=organization.id).order_by("-created_at")[:25]

    return Response({
        "organization": OrganizationSerializer(organization).data,
        "can_manage": PermissionService.can_manage_organization(request.user, organization),
        "members": OrganizationMembershipSerializer(
            organization.memberships.select_related("user", "invited_by").order_by("user__email", "role"),
            many=True,
        ).data,
        "pending_invitations": OrganizationInvitationSerializer(invitations, many=True).data,
        "entitlement": {
            "has_active_recruiter_entitlement": EntitlementService.has_active_recruiter_entitlement(organization),
            "max_recruiter_seats": max_seats,
            "active_recruiter_seats": active_seats,
            "remaining_recruiter_seats": max(max_seats - active_seats, 0),
            "can_post_jobs": bool(entitlement and entitlement.can_post_jobs),
            "can_search_candidates": bool(entitlement and entitlement.can_search_candidates),
            "can_view_candidate_profiles": bool(entitlement and entitlement.can_view_candidate_profiles),
        },
        "candidate_unlock_usage": {
            "used": organization.candidate_profile_unlocks.count(),
            "limit": None,
        },
        "recent_audit_activity": list(
            audit_logs.values("id", "action", "target_type", "target_id", "metadata", "created_at")
        ),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def organization_invite(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    serializer = OrganizationInviteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    invitation, token = OrganizationService.invite_member(
        actor=request.user,
        organization=organization,
        email=serializer.validated_data["email"],
        role=serializer.validated_data["role"],
    )
    data = OrganizationInvitationSerializer(invitation).data
    data["token"] = token
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([InvitationAcceptRateThrottle])
def organization_invitation_accept(request):
    serializer = OrganizationInvitationAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    membership = OrganizationService.accept_invitation(
        actor=request.user,
        token=serializer.validated_data["token"],
    )
    return Response(OrganizationMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def organization_member_role(request, organization_id, membership_id):
    organization = get_object_or_404(Organization, id=organization_id)
    membership = get_object_or_404(
        OrganizationMembership.objects.select_related("organization", "user"),
        id=membership_id,
        organization=organization,
    )
    serializer = OrganizationRoleChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    membership = OrganizationService.change_member_role(
        actor=request.user,
        membership=membership,
        role=serializer.validated_data["role"],
    )
    return Response(OrganizationMembershipSerializer(membership).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def organization_member_remove(request, organization_id, membership_id):
    organization = get_object_or_404(Organization, id=organization_id)
    membership = get_object_or_404(
        OrganizationMembership.objects.select_related("organization", "user"),
        id=membership_id,
        organization=organization,
    )
    OrganizationService.remove_member(actor=request.user, membership=membership)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_dashboard(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    profile = EnterpriseOrganizationService.get_or_create_profile(organization)
    policy = EnterpriseOrganizationService.get_or_create_policy(organization)
    recent_audit = AuditLog.objects.filter(organization_id=organization.id).order_by("-created_at")[:20]
    imports = BulkImportJob.objects.filter(organization=organization).order_by("-created_at")[:10]
    exports = DataExportJob.objects.filter(organization=organization).order_by("-created_at")[:10]
    return Response(
        {
            "organization": OrganizationSerializer(organization).data,
            "profile": OrganizationProfileSerializer(profile).data,
            "policy": OrganizationPolicySerializer(policy).data,
            "hierarchy": EnterpriseOrganizationService.hierarchy_summary(organization),
            "analytics": EnterpriseOrganizationService.dashboard(organization),
            "recent_audit_activity": list(
                recent_audit.values("id", "action", "target_type", "target_id", "metadata", "created_at")
            ),
            "recent_imports": BulkImportJobSerializer(imports, many=True).data,
            "recent_exports": DataExportJobSerializer(exports, many=True).data,
            "can_manage": PermissionService.can_manage_organization(request.user, organization),
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def enterprise_settings(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=request.method == "PATCH")
    profile = EnterpriseOrganizationService.get_or_create_profile(organization)
    policy = EnterpriseOrganizationService.get_or_create_policy(organization)
    if request.method == "PATCH":
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            actor=request.user,
            action="organization_settings_updated",
            target=organization,
            organization=organization,
            request=request,
            metadata={"fields": sorted(serializer.validated_data.keys())},
        )
    return Response(
        {
            "organization": OrganizationSerializer(organization).data,
            "profile": OrganizationProfileSerializer(profile).data,
            "policy": OrganizationPolicySerializer(policy).data,
            "members": OrganizationMembershipSerializer(
                organization.memberships.select_related("user", "invited_by").order_by("user__email", "role"),
                many=True,
            ).data,
            "pending_invitations": OrganizationInvitationSerializer(
                organization.invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).order_by("-created_at"),
                many=True,
            ).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enterprise_lifecycle(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    serializer = OrganizationLifecycleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    owner = None
    if serializer.validated_data["action"] == "transfer_ownership":
        owner = get_object_or_404(User, id=serializer.validated_data.get("owner_id"))
    updated = EnterpriseOrganizationService.lifecycle_transition(
        actor=request.user,
        organization=organization,
        action=serializer.validated_data["action"],
        new_owner=owner,
        metadata=serializer.validated_data.get("metadata", {}),
    )
    return Response(OrganizationSerializer(updated).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def enterprise_roles(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=request.method == "POST")
    if request.method == "GET":
        memberships = organization.memberships.select_related("user", "invited_by").order_by("role", "user__email")
        data = OrganizationMembershipSerializer(memberships, many=True).data
        return Response({
            "memberships": data,
            "permission_summary": {
                "report_viewer": "View dashboards, analytics, exports, audit center, and reports.",
                "export_manager": "Create exports and reports, including audit exports.",
                "department_manager": "Manage assigned departments only.",
                "team_manager": "Manage assigned teams only.",
                "cohort_manager": "Manage assigned cohorts only.",
            },
        })
    serializer = EnterpriseRoleAssignmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    membership = get_object_or_404(OrganizationMembership, id=serializer.validated_data["membership_id"], organization=organization)
    membership = OrganizationService.change_member_role(
        actor=request.user,
        membership=membership,
        role=serializer.validated_data["role"],
    )
    return Response(OrganizationMembershipSerializer(membership).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_audit_center(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    serializer = EnterpriseAuditFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    logs = AuditLog.objects.filter(organization_id=organization.id).order_by("-created_at")
    filters = serializer.validated_data
    if filters.get("action"):
        logs = logs.filter(action__icontains=filters["action"])
    if filters.get("action_prefix"):
        logs = logs.filter(action__startswith=filters["action_prefix"])
    if filters.get("severity"):
        logs = logs.filter(metadata__severity=filters["severity"])
    if filters.get("actor"):
        logs = logs.filter(actor_id=filters["actor"])
    if filters.get("user_id"):
        logs = logs.filter(actor_id=filters["user_id"])
    if filters.get("target_type"):
        logs = logs.filter(target_type__icontains=filters["target_type"])
    if filters.get("target_id"):
        logs = logs.filter(target_id=filters["target_id"])
    if filters.get("start_date"):
        logs = logs.filter(created_at__gte=filters["start_date"])
    if filters.get("end_date"):
        logs = logs.filter(created_at__lte=filters["end_date"])
    if filters.get("q"):
        logs = logs.filter(Q(action__icontains=filters["q"]) | Q(target_type__icontains=filters["q"]) | Q(target_id__icontains=filters["q"]))
    rows = list(logs.values("id", "action", "target_type", "target_id", "actor_id", "metadata", "ip_address", "created_at")[:500])
    if filters["file_format"] == "xlsx":
        response = HttpResponse(
            EnterpriseOrganizationService.xlsx_export(rows),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{organization.slug}-audit.xlsx"'
        return response
    if filters["file_format"] == "csv":
        response = HttpResponse(EnterpriseOrganizationService.csv_export(rows), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{organization.slug}-audit.csv"'
        return response
    return Response({"total": logs.count(), "events": rows})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def enterprise_branding(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=request.method == "PATCH")
    profile = EnterpriseOrganizationService.get_or_create_profile(organization)
    if request.method == "PATCH":
        serializer = OrganizationProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            actor=request.user,
            action="organization_profile_updated",
            target=profile,
            organization=organization,
            request=request,
            metadata={"fields": sorted(serializer.validated_data.keys())},
        )
    return Response(OrganizationProfileSerializer(profile).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def enterprise_branding_upload(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=True)
    serializer = BrandingAssetUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    profile = EnterpriseOrganizationService.update_branding_asset(
        actor=request.user,
        organization=organization,
        field_name=serializer.validated_data["asset_type"],
        file_obj=serializer.validated_data["file"],
    )
    return Response(OrganizationProfileSerializer(profile).data)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def enterprise_policies(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=request.method == "PATCH")
    policy = EnterpriseOrganizationService.get_or_create_policy(organization)
    if request.method == "PATCH":
        serializer = OrganizationPolicySerializer(policy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            actor=request.user,
            action="organization_policy_updated",
            target=policy,
            organization=organization,
            request=request,
            metadata={"fields": sorted(serializer.validated_data.keys())},
        )
    return Response(OrganizationPolicySerializer(policy).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def enterprise_departments(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=request.method == "POST")
    if request.method == "GET":
        return Response(DepartmentSerializer(_annotated_departments(organization).order_by("name"), many=True).data)
    serializer = DepartmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    department = serializer.save(organization=organization)
    AuditService.record(
        actor=request.user,
        action="organization_department_created",
        target=department,
        organization=organization,
        request=request,
    )
    department = _annotated_departments(organization).get(id=department.id)
    return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def enterprise_department_detail(request, organization_id, department_id):
    organization = get_object_or_404(Organization, id=organization_id)
    department = get_object_or_404(_annotated_departments(organization), id=department_id)
    if not (
        PermissionService.can_view_enterprise_reports(request.user, organization)
        or PermissionService.can_manage_department(request.user, department)
    ):
        raise PermissionError("You cannot view this department.")
    if request.method == "GET":
        return Response(DepartmentSerializer(department).data)
    if not PermissionService.can_manage_department(request.user, department):
        raise PermissionError("You cannot manage this department.")
    if request.method == "DELETE":
        department.status = EnterpriseStatus.ARCHIVED
        department.save(update_fields=["status", "updated_at"])
        AuditService.record(
            actor=request.user,
            action="organization_department_archived",
            target=department,
            organization=organization,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = DepartmentSerializer(department, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(DepartmentSerializer(_annotated_departments(organization).get(id=department.id)).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enterprise_department_members(request, organization_id, department_id):
    organization = _enterprise_organization(request, organization_id, manage=True)
    department = get_object_or_404(Department, id=department_id, organization=organization)
    serializer = DepartmentMemberWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    membership = _organization_membership(organization, serializer.validated_data["membership_id"])
    member, _ = DepartmentMember.objects.update_or_create(
        department=department,
        membership=membership,
        defaults={"role": serializer.validated_data["role"]},
    )
    AuditService.record(
        actor=request.user,
        action="organization_department_member_added",
        target=member,
        organization=organization,
        request=request,
        metadata={"membership_id": str(membership.id), "role": member.role},
    )
    return Response(DepartmentSerializer(_annotated_departments(organization).get(id=department.id)).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def enterprise_teams(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=request.method == "POST")
    if request.method == "GET":
        return Response(OrganizationTeamSerializer(_annotated_teams(organization).order_by("name"), many=True).data)
    serializer = OrganizationTeamSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    manager = serializer.validated_data.get("manager")
    if manager and manager.organization_id != organization.id:
        raise PermissionError("Team manager must belong to this organization.")
    team = serializer.save(organization=organization)
    AuditService.record(actor=request.user, action="organization_team_created", target=team, organization=organization, request=request)
    return Response(OrganizationTeamSerializer(_annotated_teams(organization).get(id=team.id)).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def enterprise_team_detail(request, organization_id, team_id):
    organization = get_object_or_404(Organization, id=organization_id)
    team = get_object_or_404(_annotated_teams(organization), id=team_id)
    if not (
        PermissionService.can_view_enterprise_reports(request.user, organization)
        or PermissionService.can_manage_team(request.user, team)
    ):
        raise PermissionError("You cannot view this team.")
    if request.method == "GET":
        return Response(OrganizationTeamSerializer(team).data)
    if not PermissionService.can_manage_team(request.user, team):
        raise PermissionError("You cannot manage this team.")
    if request.method == "DELETE":
        team.status = EnterpriseStatus.ARCHIVED
        team.save(update_fields=["status", "updated_at"])
        AuditService.record(actor=request.user, action="organization_team_archived", target=team, organization=organization, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = OrganizationTeamSerializer(team, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    manager = serializer.validated_data.get("manager")
    if manager and manager.organization_id != organization.id:
        raise PermissionError("Team manager must belong to this organization.")
    serializer.save()
    return Response(OrganizationTeamSerializer(_annotated_teams(organization).get(id=team.id)).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enterprise_team_members(request, organization_id, team_id):
    organization = _enterprise_organization(request, organization_id, manage=True)
    team = get_object_or_404(OrganizationTeam, id=team_id, organization=organization)
    serializer = TeamMemberWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    membership = _organization_membership(organization, serializer.validated_data["membership_id"])
    member, _ = TeamMember.objects.update_or_create(
        team=team,
        membership=membership,
        defaults={"role": serializer.validated_data["role"]},
    )
    AuditService.record(
        actor=request.user,
        action="organization_team_member_added",
        target=member,
        organization=organization,
        request=request,
        metadata={"membership_id": str(membership.id), "role": member.role},
    )
    return Response(OrganizationTeamSerializer(_annotated_teams(organization).get(id=team.id)).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def enterprise_cohorts(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=request.method == "POST")
    if request.method == "GET":
        return Response(CohortSerializer(_annotated_cohorts(organization).order_by("-created_at"), many=True).data)
    serializer = CohortSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cohort = serializer.save(organization=organization)
    AuditService.record(actor=request.user, action="organization_cohort_created", target=cohort, organization=organization, request=request)
    return Response(CohortSerializer(_annotated_cohorts(organization).get(id=cohort.id)).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def enterprise_cohort_detail(request, organization_id, cohort_id):
    organization = get_object_or_404(Organization, id=organization_id)
    cohort = get_object_or_404(_annotated_cohorts(organization), id=cohort_id)
    if not (
        PermissionService.can_view_enterprise_reports(request.user, organization)
        or PermissionService.can_manage_cohort(request.user, cohort)
    ):
        raise PermissionError("You cannot view this cohort.")
    if request.method == "GET":
        return Response(CohortSerializer(cohort).data)
    if not PermissionService.can_manage_cohort(request.user, cohort):
        raise PermissionError("You cannot manage this cohort.")
    if request.method == "DELETE":
        cohort.status = "archived"
        cohort.save(update_fields=["status", "updated_at"])
        AuditService.record(actor=request.user, action="organization_cohort_archived", target=cohort, organization=organization, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = CohortSerializer(cohort, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(CohortSerializer(_annotated_cohorts(organization).get(id=cohort.id)).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enterprise_cohort_members(request, organization_id, cohort_id):
    organization = _enterprise_organization(request, organization_id, manage=True)
    cohort = get_object_or_404(Cohort, id=cohort_id, organization=organization)
    serializer = CohortMemberWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    membership = _organization_membership(organization, serializer.validated_data["membership_id"])
    member, _ = CohortMember.objects.update_or_create(
        cohort=cohort,
        membership=membership,
        defaults={"role": serializer.validated_data["role"]},
    )
    AuditService.record(
        actor=request.user,
        action="organization_cohort_member_added",
        target=member,
        organization=organization,
        request=request,
        metadata={"membership_id": str(membership.id), "role": member.role},
    )
    return Response(CohortSerializer(_annotated_cohorts(organization).get(id=cohort.id)).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enterprise_bulk_import(request, organization_id):
    organization = _enterprise_organization(request, organization_id, manage=True)
    serializer = BulkImportPreviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    job = EnterpriseOrganizationService.bulk_import(
        actor=request.user,
        organization=organization,
        import_type=serializer.validated_data["import_type"],
        csv_content=serializer.validated_data["csv_content"],
        source_filename=serializer.validated_data.get("source_filename", ""),
        commit=serializer.validated_data["commit"],
    )
    return Response(BulkImportJobSerializer(job).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_import_jobs(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    jobs = BulkImportJob.objects.filter(organization=organization).order_by("-created_at")[:100]
    return Response(BulkImportJobSerializer(jobs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_import_file_download(request, organization_id, import_id, file_kind):
    organization = _enterprise_organization(request, organization_id)
    job = get_object_or_404(BulkImportJob, id=import_id, organization=organization)
    file_obj = job.summary_file if file_kind == "summary" else job.error_file if file_kind == "errors" else None
    if not file_obj:
        return Response({"detail": "Import file is not ready."}, status=status.HTTP_409_CONFLICT)
    AuditService.record(
        actor=request.user,
        action="organization_import_file_downloaded",
        target=job,
        organization=organization,
        request=request,
        metadata={"file_kind": file_kind},
    )
    response = HttpResponse(file_obj.open("rb").read(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{file_obj.name.rsplit("/", 1)[-1]}"'
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_import_template(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    serializer = ImportTemplateSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    template = EnterpriseOrganizationService.import_template(serializer.validated_data["import_type"])
    if request.query_params.get("download") == "1":
        csv_body = EnterpriseOrganizationService.csv_export(template["sample_rows"])
        response = HttpResponse(csv_body, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{organization.slug}-{template["import_type"]}-template.csv"'
        return response
    return Response(template)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def enterprise_exports(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    if request.method == "GET":
        exports = DataExportJob.objects.filter(organization=organization).order_by("-created_at")[:50]
        return Response(DataExportJobSerializer(exports, many=True).data)
    serializer = DataExportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    export_type = serializer.validated_data["export_type"]
    file_format = serializer.validated_data["file_format"]
    export_job = EnterpriseOrganizationService.queue_export(
        actor=request.user,
        organization=organization,
        export_type=export_type,
        file_format=file_format,
    )
    _dispatch_or_process(process_data_export, export_job.id, lambda: EnterpriseOrganizationService.process_export(export_job))
    return Response(DataExportJobSerializer(export_job).data, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_export_download(request, organization_id, export_id):
    organization = _enterprise_organization(request, organization_id)
    export_job = get_object_or_404(DataExportJob, id=export_id, organization=organization)
    if not export_job.file or export_job.status != DataExportJob.Status.COMPLETED:
        return Response({"detail": "Export file is not ready."}, status=status.HTTP_409_CONFLICT)
    EnterpriseOrganizationService.mark_export_downloaded(export_job)
    response = HttpResponse(export_job.file.open("rb").read(), content_type=export_job.content_type or "application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{export_job.file_name or export_job.file.name}"'
    return response


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def enterprise_export_delete(request, organization_id, export_id):
    organization = _enterprise_organization(request, organization_id, manage=True)
    export_job = get_object_or_404(DataExportJob, id=export_id, organization=organization)
    export_job.deleted_at = timezone.now()
    export_job.status = DataExportJob.Status.CANCELLED
    export_job.save(update_fields=["deleted_at", "status", "updated_at"])
    AuditService.record(actor=request.user, action="organization_export_deleted", target=export_job, organization=organization)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def enterprise_reports(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    if request.method == "GET":
        reports = organization.enterprise_reports.select_related("export_job").order_by("-created_at")[:100]
        return Response(EnterpriseReportJobSerializer(reports, many=True).data)
    serializer = EnterpriseReportCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    report = EnterpriseOrganizationService.queue_report(
        actor=request.user,
        organization=organization,
        report_type=serializer.validated_data["report_type"],
        file_format=serializer.validated_data["file_format"],
    )
    _dispatch_or_process(process_enterprise_report, report.id, lambda: EnterpriseOrganizationService.process_report(report))
    return Response(EnterpriseReportJobSerializer(report).data, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_worker_jobs(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    stuck_threshold = timezone.now() - timedelta(hours=1)
    stuck_counts = {
        "exports": organization.data_exports.filter(status=DataExportJob.Status.PROCESSING, updated_at__lte=stuck_threshold).count(),
        "imports": organization.bulk_imports.filter(status__in=[BulkImportJob.Status.VALIDATING, BulkImportJob.Status.PROCESSING], updated_at__lte=stuck_threshold).count(),
        "reports": organization.enterprise_reports.filter(status=EnterpriseReportJob.Status.PROCESSING, updated_at__lte=stuck_threshold).count(),
    }
    for key, count in stuck_counts.items():
        EnterpriseOrganizationService.record_worker_event(
            worker_key=EnterpriseOrganizationService._worker_key(key, organization),
            organization=organization,
            stuck_job_count=count,
        )
    return Response({
        "exports": DataExportJobSerializer(organization.data_exports.order_by("-created_at")[:20], many=True).data,
        "imports": BulkImportJobSerializer(organization.bulk_imports.order_by("-created_at")[:20], many=True).data,
        "reports": EnterpriseReportJobSerializer(organization.enterprise_reports.order_by("-created_at")[:20], many=True).data,
        "worker_statuses": EnterpriseWorkerStatusSerializer(
            EnterpriseWorkerStatus.objects.filter(organization=organization).order_by("worker_key"),
            many=True,
        ).data,
        "stuck_counts": stuck_counts,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enterprise_analytics(request, organization_id):
    organization = _enterprise_organization(request, organization_id)
    return Response(
        {
            "organization": OrganizationSerializer(organization).data,
            "hierarchy": EnterpriseOrganizationService.hierarchy_summary(organization),
            "analytics": EnterpriseOrganizationService.dashboard(organization),
        }
    )
