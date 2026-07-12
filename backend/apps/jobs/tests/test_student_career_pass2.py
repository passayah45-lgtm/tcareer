import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.analytics.models import AnalyticsEvent
from apps.careers.models import CareerResume, Portfolio, PortfolioSkill, ResumeAnalytics, VisibilityChoice
from apps.jobs.models import Interview, JobAlert, JobApplication, JobApplicationAnswer, JobApplicationQuestion, JobListing
from apps.notifications.models import EmailDelivery, Notification, NotificationType
from apps.organizations.models import (
    CandidateProfileUnlock,
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.users.tests.factories import RecruiterFactory, UserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def student_job_context():
    student = UserFactory(full_name="Student Candidate")
    organization = Organization.objects.create(
        name="Hiring Co",
        organization_type=OrganizationType.COMPANY,
        status="active",
    )
    job = JobListing.objects.create(
        organization=organization,
        title="Junior Data Analyst",
        company_name="Hiring Co",
        description="Analyze product data.",
        requirements=["Use SQL"],
        required_skills=["SQL", "Python"],
        preferred_skills=["Power BI"],
        country_code="GN",
        city="Conakry",
        is_remote=True,
        experience_level="entry",
        is_active=True,
    )
    return student, organization, job


def test_application_can_reference_selected_career_resume(api_client, student_job_context):
    student, _, job = student_job_context
    resume = CareerResume.objects.create(user=student, title="Analyst Resume", is_default=True)
    api_client.force_authenticate(user=student)

    response = api_client.post(
        reverse("jobs:job-apply", args=[job.id]),
        {"cover_letter": "I can help.", "resume_id": str(resume.id)},
        format="json",
    )

    assert response.status_code == 201
    application = JobApplication.objects.get(id=response.json()["data"]["id"])
    assert application.selected_resume == resume
    assert ResumeAnalytics.objects.filter(
        resume=resume,
        event_type=ResumeAnalytics.EventType.USED_FOR_APPLICATION,
    ).exists()
    assert AnalyticsEvent.objects.filter(name="resume_used_for_application").exists()


def test_job_alert_matching_creates_notifications_once(student_job_context):
    student, _, job = student_job_context
    alert = JobAlert.objects.create(user=student, name="Remote SQL", filters={"skills": ["SQL"], "remote": True})

    call_command("run_job_alerts")
    call_command("run_job_alerts")

    notifications = Notification.objects.filter(
        recipient=student,
        notification_type=NotificationType.NEW_JOB_MATCH,
    )
    assert notifications.count() == 1
    assert notifications.first().payload["job_id"] == str(job.id)
    assert AnalyticsEvent.objects.filter(name="job_alert_matched", target_id=str(job.id)).count() == 1
    alert.refresh_from_db()
    assert alert.is_active is True
    assert alert.last_run_at is not None
    assert alert.last_matched_count == 0
    assert alert.total_matched_count == 1
    assert EmailDelivery.objects.filter(notification__notification_type=NotificationType.NEW_JOB_MATCH).count() == 1


def test_job_alert_dry_run_and_limit_do_not_create_records(student_job_context):
    student, _, _ = student_job_context
    JobAlert.objects.create(user=student, name="Remote SQL", filters={"skills": ["SQL"], "remote": True})
    JobAlert.objects.create(user=student, name="Data", filters={"search": "Data"})

    call_command("run_job_alerts", "--dry-run", "--limit", "1")

    assert Notification.objects.filter(notification_type=NotificationType.NEW_JOB_MATCH).count() == 0
    assert EmailDelivery.objects.count() == 0
    assert JobAlert.objects.filter(last_run_at__isnull=False).count() == 0


def test_recommendations_include_scoring_explanations(api_client, student_job_context):
    student, _, job = student_job_context
    portfolio = Portfolio.objects.create(
        user=student,
        visibility=VisibilityChoice.PUBLIC,
        desired_role="Data Analyst",
        remote_preference="remote",
        preferred_work_country="GN",
        experience_level="entry",
    )
    PortfolioSkill.objects.create(portfolio=portfolio, name="SQL")
    CareerResume.objects.create(user=student, title="Analyst Resume", is_default=True)
    api_client.force_authenticate(user=student)

    response = api_client.get(reverse("jobs:student-dashboard"))

    assert response.status_code == 200
    recommended = response.json()["data"]["recommended_jobs"]
    assert recommended[0]["id"] == str(job.id)
    assert recommended[0]["recommendation_score"] > 0
    assert any("skills" in reason for reason in recommended[0]["recommendation_reasons"])


def test_application_preview_returns_selected_resume_and_profile(api_client, student_job_context):
    student, _, job = student_job_context
    portfolio = Portfolio.objects.create(user=student, visibility=VisibilityChoice.PUBLIC, headline="Data learner")
    PortfolioSkill.objects.create(portfolio=portfolio, name="SQL")
    resume = CareerResume.objects.create(user=student, title="Analyst Resume", summary="Ready", is_default=True)
    api_client.force_authenticate(user=student)

    response = api_client.post(
        reverse("jobs:application-preview", args=[job.id]),
        {"cover_letter": "Preview me", "resume_id": str(resume.id), "portfolio_id": str(portfolio.id)},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["job"]["id"] == str(job.id)
    assert payload["selected_resume"]["id"] == str(resume.id)
    assert payload["portfolio"]["headline"] == "Data learner"
    assert payload["cover_letter"] == "Preview me"


def test_application_questions_validate_and_save_answers(api_client, student_job_context):
    student, _, job = student_job_context
    question = JobApplicationQuestion.objects.create(
        job=job,
        question_text="Portfolio URL?",
        question_type="url",
        is_required=True,
    )
    api_client.force_authenticate(user=student)

    response = api_client.post(
        reverse("jobs:job-apply", args=[job.id]),
        {"cover_letter": "Missing answer", "answers": []},
        format="json",
    )
    assert response.status_code == 400

    response = api_client.post(
        reverse("jobs:job-apply", args=[job.id]),
        {"cover_letter": "Answered", "answers": [{"question": str(question.id), "answer": {"value": "https://example.com/me"}}]},
        format="json",
    )
    assert response.status_code == 201
    application = JobApplication.objects.get(id=response.json()["data"]["id"])
    assert JobApplicationAnswer.objects.filter(application=application, question=question).exists()


def test_interview_notifications_create_email_delivery_records(api_client, student_job_context):
    candidate, organization, job = student_job_context
    recruiter = RecruiterFactory()
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    application = JobApplication.objects.create(
        job=job,
        candidate=candidate,
        organization=organization,
        assigned_recruiter=recruiter,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        reverse("jobs:interviews", args=[organization.id]),
        {
            "application_id": str(application.id),
            "interview_type": "online",
            "scheduled_start": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "timezone": "UTC",
        },
        format="json",
    )
    assert response.status_code == 201
    interview = Interview.objects.get(id=response.json()["data"]["id"])
    assert Notification.objects.filter(recipient=candidate, notification_type=NotificationType.INTERVIEW_SCHEDULED).exists()
    assert EmailDelivery.objects.filter(notification__notification_type=NotificationType.INTERVIEW_SCHEDULED).exists()

    response = api_client.patch(
        reverse("jobs:interview-update", args=[organization.id, interview.id]),
        {"status": "rescheduled"},
        format="json",
    )
    assert response.status_code == 200
    assert EmailDelivery.objects.filter(notification__notification_type=NotificationType.INTERVIEW_UPDATED).exists()


def test_student_dashboard_includes_analytics_counts(api_client, student_job_context):
    student, _, job = student_job_context
    Portfolio.objects.create(user=student, visibility=VisibilityChoice.PUBLIC, profile_views=3)
    resume = CareerResume.objects.create(user=student, title="Analyst Resume")
    ResumeAnalytics.objects.create(resume=resume, actor=student, event_type=ResumeAnalytics.EventType.DOWNLOADED)
    JobAlert.objects.create(user=student, name="SQL", filters={"skills": ["SQL"]}, total_matched_count=2)
    JobApplication.objects.create(job=job, candidate=student, organization=job.organization)
    api_client.force_authenticate(user=student)

    response = api_client.get(reverse("jobs:student-dashboard"))

    assert response.status_code == 200
    analytics = response.json()["data"]["student_analytics"]
    assert analytics["profile_views"] == 3
    assert analytics["resume_downloads"] == 1
    assert analytics["job_alert_matches"] == 2
    assert analytics["applications_by_status"]["applied"] == 1


def test_unlocked_recruiter_can_download_private_resume(api_client, student_job_context):
    candidate, organization, _ = student_job_context
    recruiter = RecruiterFactory()
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    CandidateProfileUnlock.objects.create(organization=organization, candidate=candidate, unlocked_by=recruiter)
    resume = CareerResume.objects.create(user=candidate, title="Candidate Resume")
    resume.files.create(
        file_url="https://example.com/resume.pdf",
        file_name="resume.pdf",
        content_type="application/pdf",
        uploaded_by=candidate,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        f"{reverse('careers:career-resume-download', args=[resume.id])}?organization_id={organization.id}",
        {},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["data"]["download_url"] == "https://example.com/resume.pdf"


def test_locked_recruiter_cannot_download_private_resume(api_client, student_job_context):
    candidate, organization, _ = student_job_context
    recruiter = RecruiterFactory()
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    resume = CareerResume.objects.create(user=candidate, title="Candidate Resume")
    resume.files.create(
        file_url="https://example.com/resume.pdf",
        file_name="resume.pdf",
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


def test_recruiter_application_question_crud_permissions(api_client, student_job_context):
    student, organization, job = student_job_context
    recruiter = RecruiterFactory()
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )

    api_client.force_authenticate(user=student)
    denied = api_client.post(
        reverse("jobs:organization-job-questions", args=[organization.id, job.id]),
        {"question_text": "Can you work remotely?", "question_type": "yes_no", "is_required": True},
        format="json",
    )
    assert denied.status_code == 403

    api_client.force_authenticate(user=recruiter)
    created = api_client.post(
        reverse("jobs:organization-job-questions", args=[organization.id, job.id]),
        {
            "question_text": "Which stack do you prefer?",
            "question_type": "multiple_choice",
            "is_required": True,
            "choices": ["Django", "FastAPI"],
            "position": 2,
        },
        format="json",
    )
    assert created.status_code == 201
    question_id = created.json()["data"]["id"]

    listed = api_client.get(reverse("jobs:organization-job-questions", args=[organization.id, job.id]))
    assert listed.status_code == 200
    assert listed.json()["data"][0]["question_text"] == "Which stack do you prefer?"

    updated = api_client.patch(
        reverse("jobs:organization-job-question-detail", args=[organization.id, job.id, question_id]),
        {"position": 1, "is_required": False},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["position"] == 1
    assert updated.json()["data"]["is_required"] is False

    deleted = api_client.delete(reverse("jobs:organization-job-question-detail", args=[organization.id, job.id, question_id]))
    assert deleted.status_code == 200
    assert deleted.json()["data"]["is_active"] is False
