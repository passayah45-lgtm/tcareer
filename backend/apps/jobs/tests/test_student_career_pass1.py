import pytest
from django.urls import reverse

from apps.analytics.models import AnalyticsEvent
from apps.careers.models import Portfolio, PortfolioSkill, Resume, VisibilityChoice
from apps.jobs.models import (
    ApplicationStage,
    JobApplication,
    JobListing,
    RecentlyViewedJob,
    SavedJob,
    SavedJobCollection,
)
from apps.organizations.models import Organization, OrganizationType
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def student_career_data():
    student = UserFactory(full_name="Ada Student", is_public_profile=True)
    organization = Organization.objects.create(
        name="Career Co",
        organization_type=OrganizationType.COMPANY,
        status="active",
    )
    job = JobListing.objects.create(
        organization=organization,
        title="Junior Data Analyst",
        company_name="Career Co",
        description="Analyze learner data.",
        requirements=["SQL"],
        required_skills=["SQL", "Python"],
        preferred_skills=["Power BI"],
        country_code="GN",
        city="Conakry",
        is_remote=True,
        salary_min=1000,
        salary_max=2000,
        is_active=True,
    )
    portfolio = Portfolio.objects.create(
        user=student,
        visibility=VisibilityChoice.PUBLIC,
        headline="Data learner",
        desired_role="Data Analyst",
        location="Conakry",
        remote_preference="remote",
    )
    PortfolioSkill.objects.create(portfolio=portfolio, name="SQL")
    PortfolioSkill.objects.create(portfolio=portfolio, name="Python")
    PortfolioSkill.objects.create(portfolio=portfolio, name="Power BI")
    Resume.objects.create(user=student, title="Ada Resume", summary="Ready", target_role="Data Analyst")
    return student, organization, job


def test_student_dashboard_returns_career_summary(api_client, student_career_data):
    student, organization, job = student_career_data
    JobApplication.objects.create(job=job, candidate=student, organization=organization)
    SavedJob.objects.create(user=student, job=job)
    api_client.force_authenticate(user=student)

    response = api_client.get(reverse("jobs:student-dashboard"))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["profile_completion"] > 0
    assert data["resume_completion"] > 0
    assert data["portfolio_completion"] > 0
    assert data["applications_submitted"] == 1
    assert data["saved_jobs"]
    assert data["recommended_jobs"]


def test_job_discovery_filters_and_tracks_view(api_client, student_career_data):
    student, _, job = student_career_data
    api_client.force_authenticate(user=student)

    response = api_client.get(reverse("jobs:job-list"), {"skills": "SQL", "country": "GN", "remote": "true"})
    assert response.status_code == 200
    payload = response.json()
    count = payload.get("count", payload.get("meta", {}).get("count"))
    if count is None and isinstance(payload.get("data"), dict):
        count = payload["data"].get("count")
    assert count == 1

    response = api_client.get(reverse("jobs:job-detail", args=[job.id]))
    assert response.status_code == 200
    assert RecentlyViewedJob.objects.filter(user=student, job=job).exists()
    assert AnalyticsEvent.objects.filter(name="job_viewed", target_id=str(job.id)).exists()


def test_student_can_save_and_remove_job(api_client, student_career_data):
    student, _, job = student_career_data
    api_client.force_authenticate(user=student)
    collection_response = api_client.post(
        reverse("jobs:student-saved-job-collections"),
        {"name": "Data jobs", "description": "Analyst opportunities"},
        format="json",
    )
    collection = SavedJobCollection.objects.get(id=collection_response.json()["data"]["id"])

    response = api_client.post(
        reverse("jobs:student-saved-jobs"),
        {"job_id": str(job.id), "collection": str(collection.id), "notes": "Strong match."},
        format="json",
    )

    assert response.status_code == 201
    assert SavedJob.objects.filter(user=student, job=job, collection=collection).exists()
    assert AnalyticsEvent.objects.filter(name="job_saved", target_id=str(job.id)).exists()

    response = api_client.delete(reverse("jobs:student-saved-job-delete", args=[job.id]))
    assert response.status_code == 200
    assert not SavedJob.objects.filter(user=student, job=job).exists()


def test_student_can_save_draft_submit_and_withdraw(api_client, student_career_data):
    student, _, job = student_career_data
    api_client.force_authenticate(user=student)

    response = api_client.post(
        reverse("jobs:job-save-draft", args=[job.id]),
        {"cover_letter": "Draft cover letter"},
        format="json",
    )
    assert response.status_code == 201
    application = JobApplication.objects.get(id=response.json()["data"]["id"])
    assert application.stage == ApplicationStage.DRAFT

    response = api_client.post(reverse("jobs:student-application-submit", args=[application.id]))
    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == ApplicationStage.APPLIED
    assert AnalyticsEvent.objects.filter(name="job_applied", target_id=str(application.id)).exists()

    response = api_client.post(reverse("jobs:application-withdraw", args=[application.id]))
    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == ApplicationStage.WITHDRAWN
