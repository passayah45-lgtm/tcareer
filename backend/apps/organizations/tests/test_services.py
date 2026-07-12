import pytest

from django.utils import timezone

from apps.analytics.models import AnalyticsEvent
from apps.organizations.models import (
    MembershipStatus,
    Organization,
    OrganizationInvitation,
    OrganizationRole,
    OrganizationRecruiterEntitlement,
    OrganizationType,
)
from apps.organizations.services import OrganizationService
from apps.users.tests.factories import AdminFactory, UserFactory
from apps.audit.models import AuditLog
from common.exceptions import PermissionError


@pytest.mark.django_db
def test_user_cannot_self_grant_privileged_organization_role():
    user = UserFactory()
    organization = Organization.objects.create(
        name="Example University",
        organization_type=OrganizationType.UNIVERSITY,
        created_by=user,
    )

    with pytest.raises(PermissionError):
        OrganizationService.add_member(
            actor=user,
            organization=organization,
            user=user,
            role=OrganizationRole.UNIVERSITY_ADMIN,
        )


@pytest.mark.django_db
def test_platform_admin_can_add_organization_member():
    admin = AdminFactory()
    user = UserFactory()
    organization = Organization.objects.create(
        name="Example Company",
        organization_type=OrganizationType.COMPANY,
        created_by=admin,
    )

    membership = OrganizationService.add_member(
        actor=admin,
        organization=organization,
        user=user,
        role=OrganizationRole.RECRUITER,
    )

    assert membership.organization == organization
    assert membership.user == user
    assert membership.role == OrganizationRole.RECRUITER


@pytest.mark.django_db
def test_create_organization_records_audit_log():
    user = UserFactory()

    organization = OrganizationService.create_organization(
        actor=user,
        name="Partner Hub",
        organization_type=OrganizationType.PLATFORM_PARTNER,
        country_code="us",
    )

    assert organization.organization_type == OrganizationType.PLATFORM_PARTNER
    assert organization.country_code == "US"
    assert AuditLog.objects.filter(action="organization_created", target_id=str(organization.id)).exists()


@pytest.mark.django_db
def test_org_admin_can_invite_member():
    admin = AdminFactory()
    organization = Organization.objects.create(
        name="Example Company",
        organization_type=OrganizationType.COMPANY,
        created_by=admin,
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )

    invitation, token = OrganizationService.invite_member(
        actor=admin,
        organization=organization,
        email="Recruiter@Example.com",
        role=OrganizationRole.RECRUITER,
    )

    assert isinstance(invitation, OrganizationInvitation)
    assert invitation.email == "recruiter@example.com"
    assert invitation.token_hash != token
    assert len(token) > 20


@pytest.mark.django_db
def test_non_admin_cannot_invite_privileged_member():
    user = UserFactory()
    organization = Organization.objects.create(
        name="Example Company",
        organization_type=OrganizationType.COMPANY,
        created_by=user,
    )

    with pytest.raises(PermissionError):
        OrganizationService.invite_member(
            actor=user,
            organization=organization,
            email="finance@example.com",
            role=OrganizationRole.FINANCE_ADMIN,
        )


@pytest.mark.django_db
def test_admin_can_change_and_remove_member():
    admin = AdminFactory()
    user = UserFactory()
    organization = Organization.objects.create(
        name="Example NGO",
        organization_type=OrganizationType.NGO,
        created_by=admin,
    )
    membership = OrganizationService.add_member(
        actor=admin,
        organization=organization,
        user=user,
        role=OrganizationRole.STUDENT,
    )

    OrganizationService.change_member_role(
        actor=admin,
        membership=membership,
        role=OrganizationRole.MENTOR,
    )
    membership.refresh_from_db()
    assert membership.role == OrganizationRole.MENTOR

    OrganizationService.remove_member(actor=admin, membership=membership)
    membership.refresh_from_db()
    assert membership.status == MembershipStatus.REMOVED


@pytest.mark.django_db
def test_invitation_acceptance_is_single_use_and_tracks_analytics():
    admin = AdminFactory()
    user = UserFactory(email="invitee@example.com")
    organization = Organization.objects.create(
        name="Example Company",
        organization_type=OrganizationType.COMPANY,
        created_by=admin,
    )
    invitation, token = OrganizationService.invite_member(
        actor=admin,
        organization=organization,
        email=user.email,
        role=OrganizationRole.STUDENT,
    )

    membership = OrganizationService.accept_invitation(actor=user, token=token)

    assert membership.organization == organization
    assert membership.user == user
    assert membership.role == OrganizationRole.STUDENT
    invitation.refresh_from_db()
    assert invitation.accepted_by == user
    assert invitation.accepted_at is not None
    assert AnalyticsEvent.objects.filter(name="organization_member_added", user=user).exists()

    with pytest.raises(PermissionError):
        OrganizationService.accept_invitation(actor=user, token=token)


@pytest.mark.django_db
def test_expired_invitation_cannot_be_accepted():
    admin = AdminFactory()
    user = UserFactory(email="late@example.com")
    organization = Organization.objects.create(name="Expired Org", organization_type=OrganizationType.COMPANY)
    invitation, token = OrganizationService.invite_member(
        actor=admin,
        organization=organization,
        email=user.email,
        role=OrganizationRole.STUDENT,
    )
    invitation.expires_at = timezone.now() - timezone.timedelta(minutes=1)
    invitation.save(update_fields=["expires_at"])

    with pytest.raises(PermissionError):
        OrganizationService.accept_invitation(actor=user, token=token)


@pytest.mark.django_db
def test_invitation_email_must_match_unless_platform_admin():
    admin = AdminFactory()
    user = UserFactory(email="wrong@example.com")
    organization = Organization.objects.create(name="Email Org", organization_type=OrganizationType.COMPANY)
    _, token = OrganizationService.invite_member(
        actor=admin,
        organization=organization,
        email="right@example.com",
        role=OrganizationRole.STUDENT,
    )

    with pytest.raises(PermissionError):
        OrganizationService.accept_invitation(actor=user, token=token)

    membership = OrganizationService.accept_invitation(actor=admin, token=token)
    assert membership.user == admin
