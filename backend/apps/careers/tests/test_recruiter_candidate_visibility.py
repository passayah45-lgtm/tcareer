import pytest
from django.urls import reverse

from apps.analytics.models import AnalyticsEvent
from apps.careers.models import Portfolio, VisibilityChoice
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.users.tests.factories import RecruiterFactory, UserFactory


@pytest.mark.django_db
def test_recruiter_view_requires_organization_id(api_client):
    recruiter = RecruiterFactory()
    candidate = UserFactory(username="candidate-one")
    Portfolio.objects.create(user=candidate, visibility=VisibilityChoice.PUBLIC)
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(reverse("careers:portfolio-recruiter", args=[candidate.username]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_recruiter_can_view_visible_candidate_with_entitled_organization(api_client):
    recruiter = RecruiterFactory()
    candidate = UserFactory(username="candidate-two", is_public_profile=True)
    Portfolio.objects.create(user=candidate, visibility=VisibilityChoice.PUBLIC)
    organization = Organization.objects.create(name="Talent Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(
        reverse("careers:portfolio-recruiter", args=[candidate.username]),
        {"organization_id": str(organization.id)},
    )

    assert response.status_code == 200
    assert AnalyticsEvent.objects.filter(name="recruiter_viewed_candidate", target_id=str(candidate.id)).exists()


@pytest.mark.django_db
def test_recruiter_cannot_view_private_candidate(api_client):
    recruiter = RecruiterFactory()
    candidate = UserFactory(username="candidate-private", is_public_profile=True)
    Portfolio.objects.create(user=candidate, visibility=VisibilityChoice.PRIVATE)
    organization = Organization.objects.create(name="Talent Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(
        reverse("careers:portfolio-recruiter", args=[candidate.username]),
        {"organization_id": str(organization.id)},
    )

    assert response.status_code == 404
