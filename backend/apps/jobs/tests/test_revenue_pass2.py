import pytest
from django.urls import reverse
from django.utils import timezone

from apps.analytics.models import AnalyticsEvent
from apps.audit.models import AuditLog
from apps.careers.models import Portfolio, PortfolioSkill, Resume, VisibilityChoice
from apps.jobs.models import (
    ApplicationStage,
    Interview,
    InterviewStatus,
    JobApplication,
    JobListing,
    SavedCandidate,
)
from apps.notifications.models import Notification
from apps.organizations.models import (
    CandidateProfileUnlock,
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.users.tests.factories import RecruiterFactory, UserFactory


@pytest.fixture
def recruiting_org(db):
    recruiter = RecruiterFactory()
    organization = Organization.objects.create(name="Hiring Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=3,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    job = JobListing.objects.create(
        organization=organization,
        posted_by=recruiter,
        title="Backend Developer",
        company_name="Hiring Co",
        description="Build APIs.",
        requirements=["Python"],
        required_skills=["Python", "Django"],
        is_active=True,
    )
    return recruiter, organization, job


@pytest.mark.django_db
def test_candidate_can_apply_and_withdraw(api_client, recruiting_org):
    _, _, job = recruiting_org
    candidate = UserFactory()
    api_client.force_authenticate(user=candidate)

    response = api_client.post(
        reverse("jobs:job-apply", args=[job.id]),
        {"cover_letter": "I like APIs."},
        format="json",
    )

    assert response.status_code == 201
    application = JobApplication.objects.get(id=response.json()["data"]["id"])
    assert application.stage == ApplicationStage.APPLIED
    assert application.timeline.filter(event_type="application_created").exists()
    assert AuditLog.objects.filter(action="application_created", target_id=str(application.id)).exists()
    assert AnalyticsEvent.objects.filter(name="application_created", target_id=str(application.id)).exists()
    assert Notification.objects.filter(notification_type="application_received").exists()

    response = api_client.post(reverse("jobs:application-withdraw", args=[application.id]))

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == ApplicationStage.WITHDRAWN
    assert application.withdrawn_at is not None


@pytest.mark.django_db
def test_recruiter_can_move_application_and_add_note(api_client, recruiting_org):
    recruiter, organization, job = recruiting_org
    candidate = UserFactory()
    application = JobApplication.objects.create(job=job, organization=organization, candidate=candidate)
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        reverse("jobs:application-stage-update", args=[organization.id, application.id]),
        {"stage": ApplicationStage.SHORTLISTED, "message": "Strong match."},
        format="json",
    )

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == ApplicationStage.SHORTLISTED
    assert application.timeline.filter(event_type="application_stage_changed").exists()
    assert AnalyticsEvent.objects.filter(name="application_stage_changed", target_id=str(application.id)).exists()
    assert Notification.objects.filter(recipient=candidate, notification_type="application_stage_changed").exists()

    response = api_client.post(
        reverse("jobs:application-notes", args=[organization.id, application.id]),
        {"body": "Good portfolio.", "is_internal": True},
        format="json",
    )

    assert response.status_code == 201
    assert application.notes.filter(body="Good portfolio.").exists()


@pytest.mark.django_db
def test_student_cannot_access_pipeline(api_client, recruiting_org):
    _, organization, _ = recruiting_org
    student = UserFactory()
    api_client.force_authenticate(user=student)

    response = api_client.get(reverse("jobs:pipeline-applications", args=[organization.id]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_recruiter_dashboard_counts_pipeline(api_client, recruiting_org):
    recruiter, organization, job = recruiting_org
    JobApplication.objects.create(job=job, organization=organization, candidate=UserFactory(), stage=ApplicationStage.APPLIED)
    JobApplication.objects.create(job=job, organization=organization, candidate=UserFactory(), stage=ApplicationStage.SHORTLISTED)
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(reverse("jobs:recruiter-dashboard", args=[organization.id]))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_jobs"] == 1
    assert data["published_jobs"] == 1
    assert data["applications_received"] == 2
    assert data["applications_by_stage"][ApplicationStage.APPLIED] == 1
    assert data["seat_usage"]["max_recruiter_seats"] == 3


@pytest.mark.django_db
def test_candidate_search_and_save_candidate(api_client, recruiting_org):
    recruiter, organization, _ = recruiting_org
    candidate = UserFactory(
        full_name="Ada Candidate",
        is_public_profile=True,
        current_country="US",
        preferred_language="en",
    )
    portfolio = Portfolio.objects.create(
        user=candidate,
        visibility=VisibilityChoice.PUBLIC,
        headline="Backend Developer",
        desired_role="Backend Developer",
        location="New York",
        preferred_work_country="US",
        remote_preference="remote",
    )
    PortfolioSkill.objects.create(portfolio=portfolio, name="Python")
    Resume.objects.create(user=candidate, target_role="Backend Developer")
    CandidateProfileUnlock.objects.create(organization=organization, candidate=candidate, unlocked_by=recruiter)
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(
        reverse("jobs:candidate-search", args=[organization.id]),
        {"skills": "Python", "country": "US", "remote_preference": "remote", "resume_available": "true"},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 1
    assert response.json()["data"][0]["full_name"] == "Ada Candidate"

    response = api_client.post(
        reverse("jobs:saved-candidates", args=[organization.id]),
        {"candidate_id": str(candidate.id), "labels": ["backend"], "private_notes": "Strong Django profile."},
        format="json",
    )

    assert response.status_code == 201
    assert SavedCandidate.objects.filter(organization=organization, candidate=candidate).exists()
    assert AnalyticsEvent.objects.filter(name="candidate_saved", target_id=str(candidate.id)).exists()


@pytest.mark.django_db
def test_interview_schedule_and_complete(api_client, recruiting_org):
    recruiter, organization, job = recruiting_org
    candidate = UserFactory()
    application = JobApplication.objects.create(job=job, organization=organization, candidate=candidate)
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        reverse("jobs:interviews", args=[organization.id]),
        {
            "application_id": str(application.id),
            "interview_type": "online",
            "scheduled_start": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "timezone": "UTC",
            "meeting_link": "https://meet.example.com/abc",
        },
        format="json",
    )

    assert response.status_code == 201
    interview = Interview.objects.get(id=response.json()["data"]["id"])
    application.refresh_from_db()
    assert application.stage == ApplicationStage.INTERVIEW_SCHEDULED
    assert interview.participants.filter(user=candidate).exists()
    assert Notification.objects.filter(recipient=candidate, notification_type="interview_scheduled").exists()
    assert AnalyticsEvent.objects.filter(name="interview_scheduled", target_id=str(interview.id)).exists()

    response = api_client.patch(
        reverse("jobs:interview-update", args=[organization.id, interview.id]),
        {"status": InterviewStatus.COMPLETED},
        format="json",
    )

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == ApplicationStage.INTERVIEW_COMPLETED
    assert AnalyticsEvent.objects.filter(name="interview_completed", target_id=str(interview.id)).exists()


@pytest.mark.django_db
def test_recruiter_application_detail_returns_aggregate(api_client, recruiting_org):
    recruiter, organization, job = recruiting_org
    candidate = UserFactory()
    application = JobApplication.objects.create(job=job, organization=organization, candidate=candidate)
    api_client.force_authenticate(user=recruiter)

    response = api_client.get(reverse("jobs:application-detail", args=[organization.id, application.id]))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["application"]["id"] == str(application.id)
    assert data["candidate"]["id"] == str(candidate.id)
    assert data["job"]["id"] == str(job.id)
    assert "timeline" in data
    assert "activity" in data
    assert "audit_history" in data


@pytest.mark.django_db
def test_recruiter_can_unlock_candidate(api_client, recruiting_org):
    recruiter, organization, _ = recruiting_org
    candidate = UserFactory(is_public_profile=True)
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(reverse("jobs:candidate-unlock", args=[organization.id, candidate.id]))

    assert response.status_code == 201
    assert CandidateProfileUnlock.objects.filter(organization=organization, candidate=candidate).exists()
    assert AnalyticsEvent.objects.filter(name="candidate_unlocked", target_id=str(candidate.id)).exists()
