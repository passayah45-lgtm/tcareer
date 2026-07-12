import pytest
from django.urls import reverse

from apps.ai_platform.models import AIBudgetPolicy, AIFeature, AIFeatureFlag, AIRequest
from apps.analytics.models import AnalyticsEvent
from apps.careers.models import CareerResume, Portfolio, PortfolioSkill, ResumeAIReview, ResumeAIReviewType, VisibilityChoice
from apps.jobs.models import ExperienceLevel, JobListing
from apps.organizations.models import CandidateProfileUnlock, Organization, OrganizationMembership, OrganizationRecruiterEntitlement, OrganizationRole
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def _resume(user):
    return CareerResume.objects.create(
        user=user,
        title="Backend Developer Resume",
        target_role="Backend Django Developer",
        summary="Backend developer building Django APIs and improving reporting workflows for students.",
        skills=["Python", "Django", "SQL", "Git"],
        education=[{"id": "edu-1", "institution": "T-Career University", "degree": "BSc", "field": "Computer Science", "start_year": 2020}],
        experience=[
            {
                "id": "exp-1",
                "company": "TechNova",
                "title": "Junior Developer",
                "location": "Conakry",
                "start_date": "2024-01",
                "end_date": "",
                "is_current": True,
                "description": "Built Django APIs and improved dashboard speed by 20%.",
            }
        ],
        is_default=True,
    )


def _job():
    org = Organization.objects.create(name="TechNova", slug="technova-ai", organization_type="company")
    return JobListing.objects.create(
        organization=org,
        title="Backend Django Developer",
        company_name="TechNova",
        description="Build APIs with Django, PostgreSQL, Docker, and REST.",
        requirements=["Django API experience", "SQL reporting"],
        required_skills=["Python", "Django", "PostgreSQL"],
        preferred_skills=["Docker", "REST API"],
        experience_level=ExperienceLevel.ENTRY,
    )


def test_resume_review_creates_ai_request_and_history(api_client):
    user = UserFactory()
    resume = _resume(user)
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("careers:career-resume-ai-review", args=[resume.id]))

    assert response.status_code == 201, response.json()
    payload = response.json()["data"]
    assert payload["overall_score"] > 0
    assert payload["strengths"]
    assert ResumeAIReview.objects.filter(resume=resume, review_type=ResumeAIReviewType.REVIEW).exists()
    assert AIRequest.objects.filter(user=user, feature=AIFeature.RESUME_REVIEW).exists()
    assert AnalyticsEvent.objects.filter(name="resume_ai_review").exists()


def test_resume_skill_extraction_and_ats(api_client):
    user = UserFactory()
    portfolio = Portfolio.objects.create(user=user, visibility=VisibilityChoice.PUBLIC)
    PortfolioSkill.objects.create(portfolio=portfolio, name="Python")
    resume = _resume(user)
    api_client.force_authenticate(user=user)

    skills = api_client.post(reverse("careers:career-resume-ai-skills", args=[resume.id]))
    ats = api_client.post(reverse("careers:career-resume-ai-ats", args=[resume.id]))

    assert skills.status_code == 201
    assert "Python" in skills.json()["data"]["extracted_skills"]["normalized"]
    assert ats.status_code == 201
    assert ats.json()["data"]["ats_score"] > 0
    assert "compatibility_score" in ats.json()["data"]["report"]["ats"]


def test_resume_job_matching_and_comparison(api_client):
    user = UserFactory()
    resume = _resume(user)
    comparison = CareerResume.objects.create(user=user, title="Old Resume", skills=["Python"], summary="Old summary")
    job = _job()
    api_client.force_authenticate(user=user)

    match = api_client.post(reverse("careers:career-resume-ai-job-match", args=[resume.id]), {"job_id": str(job.id)}, format="json")
    comparison_response = api_client.post(
        reverse("careers:career-resume-ai-comparison", args=[resume.id]),
        {"comparison_resume_id": str(comparison.id)},
        format="json",
    )

    assert match.status_code == 201
    assert match.json()["data"]["match_score"] > 0
    assert "PostgreSQL" in match.json()["data"]["missing_skills"]
    assert comparison_response.status_code == 201
    assert "added_skills" in comparison_response.json()["data"]["report"]["comparison"]


def test_resume_history_and_analytics(api_client):
    user = UserFactory()
    resume = _resume(user)
    api_client.force_authenticate(user=user)
    api_client.post(reverse("careers:career-resume-ai-review", args=[resume.id]))
    api_client.post(reverse("careers:career-resume-ai-ats", args=[resume.id]))

    history = api_client.get(reverse("careers:career-resume-ai-history", args=[resume.id]))
    analytics = api_client.get(reverse("careers:career-resume-ai-analytics", args=[resume.id]))

    assert history.status_code == 200
    assert len(history.json()["data"]) == 2
    assert analytics.status_code == 200
    assert analytics.json()["data"]["review_count"] == 2
    assert analytics.json()["data"]["best_score"] > 0


def test_resume_ai_permissions(api_client):
    owner = UserFactory()
    stranger = UserFactory()
    resume = _resume(owner)
    api_client.force_authenticate(user=stranger)

    response = api_client.post(reverse("careers:career-resume-ai-review", args=[resume.id]))

    assert response.status_code == 404


def test_recruiter_summary_requires_resume_visibility(api_client):
    owner = UserFactory()
    recruiter = UserFactory()
    resume = _resume(owner)
    ResumeAIReview.objects.create(user=owner, resume=resume, review_type=ResumeAIReviewType.REVIEW, overall_score=80, confidence=75)
    organization = Organization.objects.create(name="Hiring Org", slug="hiring-org", organization_type="company")
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationRecruiterEntitlement.objects.create(organization=organization, can_search_candidates=True, can_view_candidate_profiles=True)
    api_client.force_authenticate(user=recruiter)

    denied = api_client.get(reverse("careers:career-resume-ai-recruiter-summary", args=[resume.id]), {"organization_id": str(organization.id)})
    CandidateProfileUnlock.objects.create(organization=organization, candidate=owner, unlocked_by=recruiter)
    allowed = api_client.get(reverse("careers:career-resume-ai-recruiter-summary", args=[resume.id]), {"organization_id": str(organization.id)})

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert "overall_score" in allowed.json()["data"]
    assert "report" not in allowed.json()["data"]


def test_resume_ai_feature_flag_and_budget_are_enforced(api_client):
    user = UserFactory()
    resume = _resume(user)
    AIFeatureFlag.objects.create(feature=AIFeature.RESUME_REVIEW, user=user, is_enabled=False, reason="test")
    api_client.force_authenticate(user=user)

    disabled = api_client.post(reverse("careers:career-resume-ai-review", args=[resume.id]))
    assert disabled.status_code == 403

    AIFeatureFlag.objects.filter(user=user).delete()
    AIBudgetPolicy.objects.create(scope="user", user=user, feature=AIFeature.RESUME_REVIEW, daily_request_limit=0)
    over_budget = api_client.post(reverse("careers:career-resume-ai-review", args=[resume.id]))
    assert over_budget.status_code == 403


def test_resume_ai_stream_endpoint_uses_ai_service(api_client):
    user = UserFactory()
    resume = _resume(user)
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("careers:career-resume-ai-review-stream", args=[resume.id]))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/event-stream")
