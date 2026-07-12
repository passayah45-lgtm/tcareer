import pytest
from django.urls import reverse

from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationRole,
    OrganizationType,
    OrganizationRecruiterEntitlement,
)
from apps.organizations.services import OrganizationService
from apps.users.tests.factories import AdminFactory, UserFactory


@pytest.mark.django_db
def test_recruiter_settings_returns_members_entitlement_and_audit(api_client):
    recruiter = UserFactory(role="recruiter")
    organization = Organization.objects.create(name="Settings Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=2,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(reverse("organizations:organization-recruiter-settings", args=[organization.id]))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["organization"]["id"] == str(organization.id)
    assert data["entitlement"]["max_recruiter_seats"] == 2
    assert data["members"][0]["user"] == str(recruiter.id)
    assert data["can_manage"] is False


@pytest.mark.django_db
def test_authenticated_user_can_create_and_list_own_organization(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("organizations:organization-list-create"),
        {
            "name": "Example Bootcamp",
            "organization_type": OrganizationType.BOOTCAMP,
            "country_code": "GN",
        },
        format="json",
    )

    assert response.status_code == 201
    organization_id = response.json()["data"]["id"]

    response = api_client.get(reverse("organizations:organization-list-create"))
    assert response.status_code == 200
    assert any(item["id"] == organization_id for item in response.json()["data"])


@pytest.mark.django_db
def test_org_admin_can_invite_member_through_api(api_client):
    admin = AdminFactory()
    organization = Organization.objects.create(
        name="Example Company",
        organization_type=OrganizationType.COMPANY,
        created_by=admin,
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("organizations:organization-invite", args=[organization.id]),
        {"email": "new@example.com", "role": OrganizationRole.RECRUITER},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["data"]["email"] == "new@example.com"
    assert "token" in response.json()["data"]


@pytest.mark.django_db
def test_member_role_change_requires_authorized_admin(api_client):
    actor = UserFactory()
    target = UserFactory()
    organization = Organization.objects.create(
        name="Example Enterprise",
        organization_type=OrganizationType.ENTERPRISE,
        created_by=target,
    )
    membership = OrganizationMembership.objects.create(
        organization=organization,
        user=target,
        role=OrganizationRole.STUDENT,
    )
    api_client.force_authenticate(user=actor)

    response = api_client.patch(
        reverse("organizations:organization-member-role", args=[organization.id, membership.id]),
        {"role": OrganizationRole.COMPANY_ADMIN},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_invitation_accept_endpoint_accepts_token(api_client):
    admin = AdminFactory()
    user = UserFactory(email="accept@example.com")
    organization = Organization.objects.create(
        name="Accept Org",
        organization_type=OrganizationType.COMPANY,
        created_by=admin,
    )
    _, token = OrganizationService.invite_member(
        actor=admin,
        organization=organization,
        email=user.email,
        role=OrganizationRole.STUDENT,
    )
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("organizations:organization-invitation-accept"),
        {"token": token},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["data"]["role"] == OrganizationRole.STUDENT
