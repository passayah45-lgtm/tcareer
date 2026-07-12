import pytest
from django.urls import reverse

from apps.analytics.models import AnalyticsEvent
from apps.audit.models import AuditLog
from apps.jobs.models import JobListing
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.users.tests.factories import RecruiterFactory, UserFactory


def _job_payload(title="Backend Developer"):
    return {
        "title": title,
        "company_name": "Hiring Co",
        "description": "Build APIs.",
        "requirements": ["Python"],
    }


@pytest.fixture
def recruiter_org(db):
    recruiter = RecruiterFactory()
    organization = Organization.objects.create(name="Hiring Co", organization_type=OrganizationType.COMPANY)
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
    return recruiter, organization


@pytest.mark.django_db
def test_recruiter_can_create_publish_archive_and_list_org_job(api_client, recruiter_org):
    recruiter, organization = recruiter_org
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        reverse("jobs:organization-jobs", args=[organization.id]),
        _job_payload(),
        format="json",
    )

    assert response.status_code == 201
    job_id = response.json()["data"]["id"]
    job = JobListing.objects.get(id=job_id)
    assert job.organization == organization
    assert job.posted_by == recruiter
    assert not job.is_active
    assert AuditLog.objects.filter(action="job_created", target_id=str(job.id)).exists()

    response = api_client.post(reverse("jobs:organization-job-publish", args=[organization.id, job.id]))
    assert response.status_code == 200
    job.refresh_from_db()
    assert job.is_active
    assert AuditLog.objects.filter(action="job_published", target_id=str(job.id)).exists()
    assert AnalyticsEvent.objects.filter(name="job_published", target_id=str(job.id)).exists()

    response = api_client.get(reverse("jobs:organization-jobs", args=[organization.id]))
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1

    response = api_client.post(reverse("jobs:organization-job-archive", args=[organization.id, job.id]))
    assert response.status_code == 200
    job.refresh_from_db()
    assert not job.is_active


@pytest.mark.django_db
def test_student_cannot_create_job(api_client, recruiter_org):
    _, organization = recruiter_org
    student = UserFactory()
    api_client.force_authenticate(user=student)

    response = api_client.post(
        reverse("jobs:organization-jobs", args=[organization.id]),
        _job_payload(),
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_recruiter_without_entitlement_cannot_create_job(api_client):
    recruiter = RecruiterFactory()
    organization = Organization.objects.create(name="No Seats Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        reverse("jobs:organization-jobs", args=[organization.id]),
        _job_payload(),
        format="json",
    )

    assert response.status_code == 403
