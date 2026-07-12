import pytest
from django.urls import reverse

from apps.careers.models import CareerResume, Portfolio, VisibilityChoice
from apps.jobs.models import JobListing
from apps.organizations.models import (
    CandidateProfileUnlock,
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.users.models import UserPrivacySettings
from apps.users.tests.factories import RecruiterFactory, UserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def recruiter_context():
    recruiter = RecruiterFactory()
    candidate = UserFactory(is_public_profile=True)
    organization = Organization.objects.create(
        name="Hiring Trust Co",
        organization_type=OrganizationType.COMPANY,
        status="active",
    )
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    Portfolio.objects.create(user=candidate, visibility=VisibilityChoice.PUBLIC, headline="Backend learner")
    JobListing.objects.create(
        organization=organization,
        title="Backend Developer",
        company_name="Hiring Trust Co",
        description="Build APIs",
        requirements=["Django"],
        is_active=True,
    )
    return recruiter, candidate, organization


def test_privacy_settings_endpoint_updates_profile_visibility(api_client):
    user = UserFactory(is_public_profile=True)
    api_client.force_authenticate(user=user)

    response = api_client.patch(reverse("users:privacy-settings"), {"public_profile": False, "allow_ai_analysis": False}, format="json")

    assert response.status_code == 200
    user.refresh_from_db()
    privacy = UserPrivacySettings.objects.get(user=user)
    assert privacy.public_profile is False
    assert privacy.allow_ai_analysis is False
    assert user.is_public_profile is False


def test_candidate_search_respects_public_profile_privacy(api_client, recruiter_context):
    recruiter, candidate, organization = recruiter_context
    UserPrivacySettings.objects.create(user=candidate, public_profile=False)
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(reverse("jobs:candidate-search", args=[organization.id]))

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_hidden_resume_cannot_be_downloaded_by_unlocked_recruiter(api_client, recruiter_context):
    recruiter, candidate, organization = recruiter_context
    privacy = UserPrivacySettings.objects.create(user=candidate, recruiter_resume_visibility=False)
    privacy.save()
    CandidateProfileUnlock.objects.create(organization=organization, candidate=candidate, unlocked_by=recruiter)
    resume = CareerResume.objects.create(user=candidate, title="Private Resume")
    resume.files.create(
        file_url="https://example.com/private.pdf",
        file_name="private.pdf",
        content_type="application/pdf",
        uploaded_by=candidate,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        f"{reverse('careers:career-resume-download', args=[resume.id])}?organization_id={organization.id}",
        {},
        format="json",
    )

    assert response.status_code == 403


def test_hidden_portfolio_is_not_visible_to_recruiter(api_client, recruiter_context):
    recruiter, candidate, organization = recruiter_context
    if not candidate.username:
        candidate.username = candidate.generate_username()
        candidate.save(update_fields=["username", "updated_at"])
    UserPrivacySettings.objects.create(user=candidate, recruiter_portfolio_visibility=False)
    CandidateProfileUnlock.objects.create(organization=organization, candidate=candidate, unlocked_by=recruiter)
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(
        f"{reverse('careers:portfolio-recruiter', args=[candidate.username])}?organization_id={organization.id}",
    )

    assert response.status_code == 404


def test_candidate_search_hides_contact_when_disabled(api_client, recruiter_context):
    recruiter, candidate, organization = recruiter_context
    UserPrivacySettings.objects.create(user=candidate, allow_recruiter_contact=False)
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(reverse("jobs:candidate-search", args=[organization.id]))

    assert response.status_code == 200
    assert response.json()["data"][0]["can_contact"] is False
