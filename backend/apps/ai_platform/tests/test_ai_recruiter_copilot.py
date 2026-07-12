import pytest
from django.urls import reverse

from apps.ai_platform.models import AIBudgetPolicy, AIFeature, AIFeatureFlag, AIRecruiterReport, AIRequest
from apps.audit.models import AuditLog
from apps.careers.models import CareerResume, Portfolio, PortfolioSkill, PortfolioProject, VisibilityChoice
from apps.jobs.models import JobApplication, JobListing
from apps.organizations.models import CandidateProfileUnlock, Organization, OrganizationMembership, OrganizationRecruiterEntitlement, OrganizationRole, OrganizationType
from apps.users.tests.factories import RecruiterFactory, UserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def recruiter_copilot_setup():
    recruiter = RecruiterFactory()
    organization = Organization.objects.create(name="Copilot Hiring", slug="copilot-hiring", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
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
        title="Backend Django Developer",
        company_name="Copilot Hiring",
        description="Build Django REST APIs, own PostgreSQL models, and support analytics dashboards.",
        requirements=["Django API experience"],
        required_skills=["Python", "Django", "PostgreSQL"],
        preferred_skills=["Docker", "REST API"],
        is_active=True,
    )
    candidate = UserFactory(full_name="Awa Diallo", profile_headline="Backend learner", is_public_profile=True)
    portfolio = Portfolio.objects.create(user=candidate, visibility=VisibilityChoice.PUBLIC, desired_role="Backend Developer")
    PortfolioSkill.objects.create(portfolio=portfolio, name="Python")
    PortfolioSkill.objects.create(portfolio=portfolio, name="Django")
    PortfolioProject.objects.create(portfolio=portfolio, title="Course analytics API", description="Built API reporting for learners.", tech_stack=["Python", "Django"])
    CareerResume.objects.create(user=candidate, title="Backend Resume", target_role="Backend Developer", summary="Django backend learner.", skills=["Python", "Django"], is_default=True)
    CandidateProfileUnlock.objects.create(organization=organization, candidate=candidate, unlocked_by=recruiter)
    return recruiter, organization, job, candidate


def test_candidate_analysis_uses_ai_service_permissions_audit_and_analytics(api_client, recruiter_copilot_setup):
    recruiter, organization, job, candidate = recruiter_copilot_setup
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        reverse("ai_platform:recruiter-candidate-analysis"),
        {"organization_id": str(organization.id), "job_id": str(job.id), "candidate_id": str(candidate.id)},
        format="json",
    )

    assert response.status_code == 201, response.json()
    payload = response.json()["data"]
    assert payload["report_type"] == AIRecruiterReport.ReportType.CANDIDATE_ANALYSIS
    assert payload["report"]["overall_candidate_score"] > 0
    assert payload["fairness_notes"]
    assert AIRequest.objects.filter(user=recruiter, feature=AIFeature.APPLICATION_REVIEW).exists()
    assert AuditLog.objects.filter(action="ai_recruiter_candidate_analysis").exists()


def test_candidate_ranking_includes_fairness_disclaimer_and_no_auto_reject(api_client, recruiter_copilot_setup):
    recruiter, _, job, candidate = recruiter_copilot_setup
    second = UserFactory(full_name="Mamadou Barry", is_public_profile=True)
    CandidateProfileUnlock.objects.create(organization=job.organization, candidate=second, unlocked_by=recruiter)
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        reverse("ai_platform:recruiter-candidate-ranking"),
        {"job_id": str(job.id), "candidate_ids": [str(candidate.id), str(second.id)], "sort_by": "highest_confidence"},
        format="json",
    )

    assert response.status_code == 201, response.json()
    ranking = response.json()["data"]["report"]["rankings"][0]
    assert "confidence" in ranking
    assert "fairness_warning" in ranking
    assert "disclaimer" in ranking
    assert "reject" not in ranking


def test_comparison_job_analysis_interview_plan_pipeline_history_and_analytics(api_client, recruiter_copilot_setup):
    recruiter, organization, job, candidate = recruiter_copilot_setup
    second = UserFactory(full_name="Fatou Camara", is_public_profile=True)
    CandidateProfileUnlock.objects.create(organization=organization, candidate=second, unlocked_by=recruiter)
    JobApplication.objects.create(job=job, organization=organization, candidate=candidate, stage="under_review")
    api_client.force_authenticate(user=recruiter)

    comparison = api_client.post(
        reverse("ai_platform:recruiter-candidate-comparison"),
        {"organization_id": str(organization.id), "job_id": str(job.id), "candidate_ids": [str(candidate.id), str(second.id)]},
        format="json",
    )
    job_analysis = api_client.post(reverse("ai_platform:recruiter-job-analysis"), {"job_id": str(job.id)}, format="json")
    interview_plan = api_client.post(
        reverse("ai_platform:recruiter-interview-plan"),
        {"organization_id": str(organization.id), "job_id": str(job.id), "candidate_id": str(candidate.id)},
        format="json",
    )
    pipeline = api_client.post(reverse("ai_platform:recruiter-pipeline-insights"), {"organization_id": str(organization.id)}, format="json")
    history = api_client.get(reverse("ai_platform:recruiter-history"))
    analytics = api_client.get(reverse("ai_platform:recruiter-analytics"))

    assert comparison.status_code == 201
    assert "comparison_table" in comparison.json()["data"]["report"]
    assert job_analysis.status_code == 201
    assert "salary_clarity" in job_analysis.json()["data"]["report"]
    assert interview_plan.status_code == 201
    assert "evaluation_rubric" in interview_plan.json()["data"]["report"]
    assert pipeline.status_code == 201
    assert "pipeline_health" in pipeline.json()["data"]["report"]
    assert history.status_code == 200
    assert analytics.status_code == 200
    assert analytics.json()["data"]["reports"] >= 4


def test_candidate_analysis_denies_student_without_recruiter_visibility(api_client, recruiter_copilot_setup):
    _, organization, job, candidate = recruiter_copilot_setup
    student = UserFactory()
    api_client.force_authenticate(user=student)

    response = api_client.post(
        reverse("ai_platform:recruiter-candidate-analysis"),
        {"organization_id": str(organization.id), "job_id": str(job.id), "candidate_id": str(candidate.id)},
        format="json",
    )

    assert response.status_code == 403


def test_feature_flags_and_budget_are_enforced(api_client, recruiter_copilot_setup):
    recruiter, organization, job, candidate = recruiter_copilot_setup
    AIFeatureFlag.objects.create(feature=AIFeature.APPLICATION_REVIEW, user=recruiter, is_enabled=False)
    api_client.force_authenticate(user=recruiter)

    disabled = api_client.post(
        reverse("ai_platform:recruiter-candidate-analysis"),
        {"organization_id": str(organization.id), "job_id": str(job.id), "candidate_id": str(candidate.id)},
        format="json",
    )
    assert disabled.status_code == 403

    AIFeatureFlag.objects.filter(user=recruiter).delete()
    AIBudgetPolicy.objects.create(scope="user", user=recruiter, feature=AIFeature.APPLICATION_REVIEW, daily_request_limit=0)
    over_budget = api_client.post(
        reverse("ai_platform:recruiter-candidate-analysis"),
        {"organization_id": str(organization.id), "job_id": str(job.id), "candidate_id": str(candidate.id)},
        format="json",
    )
    assert over_budget.status_code == 403
