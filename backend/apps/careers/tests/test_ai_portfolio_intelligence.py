import pytest
from django.urls import reverse

from apps.ai_platform.models import AIBudgetPolicy, AIFeature, AIFeatureFlag, AIRequest
from apps.analytics.models import AnalyticsEvent
from apps.careers.models import Portfolio, PortfolioAIReview, PortfolioAIReviewType, PortfolioProject, PortfolioSkill, VisibilityChoice
from apps.jobs.models import ExperienceLevel, JobListing
from apps.organizations.models import CandidateProfileUnlock, Organization, OrganizationMembership, OrganizationRecruiterEntitlement, OrganizationRole
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def _portfolio(user):
    portfolio = Portfolio.objects.create(
        user=user,
        headline="Backend developer with data projects",
        bio="I build Django and analytics projects for operational teams with clear demos and measurable outcomes.",
        desired_role="Backend Django Developer",
        visibility=VisibilityChoice.PUBLIC,
        github_url="https://github.com/demo-user",
    )
    PortfolioSkill.objects.create(portfolio=portfolio, name="Python")
    PortfolioSkill.objects.create(portfolio=portfolio, name="Django")
    project = PortfolioProject.objects.create(
        portfolio=portfolio,
        title="Recruiter Analytics Dashboard",
        description="Built a Django and PostgreSQL dashboard that improved recruiter reporting by 25% with clear deployment notes.",
        tech_stack=["Python", "Django", "PostgreSQL", "Docker"],
        github_url="https://github.com/demo-user/recruiter-dashboard",
        project_url="https://demo.example.com",
        is_featured=True,
    )
    return portfolio, project


def _job():
    org = Organization.objects.create(name="TechNova AI", slug="technova-ai-portfolio", organization_type="company")
    return JobListing.objects.create(
        organization=org,
        title="Backend Django Developer",
        company_name="TechNova",
        description="Build Django APIs, PostgreSQL reports, and Docker-based deployments.",
        requirements=["Django APIs", "PostgreSQL reporting"],
        required_skills=["Python", "Django", "PostgreSQL"],
        preferred_skills=["Docker", "REST API"],
        experience_level=ExperienceLevel.ENTRY,
    )


def test_portfolio_review_creates_ai_request_and_history(api_client):
    user = UserFactory()
    portfolio, _ = _portfolio(user)
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("careers:portfolio-ai-review"))

    assert response.status_code == 201, response.json()
    payload = response.json()["data"]
    assert payload["overall_score"] > 0
    assert payload["strengths"]
    assert PortfolioAIReview.objects.filter(portfolio=portfolio, review_type=PortfolioAIReviewType.PORTFOLIO_REVIEW).exists()
    assert AIRequest.objects.filter(user=user, feature=AIFeature.PORTFOLIO_REVIEW).exists()
    assert AnalyticsEvent.objects.filter(name="portfolio_ai_portfolio_review").exists()


def test_project_github_and_skill_intelligence(api_client):
    user = UserFactory()
    _, project = _portfolio(user)
    api_client.force_authenticate(user=user)

    project_response = api_client.post(reverse("careers:portfolio-ai-project-review"), {"project_id": str(project.id)}, format="json")
    github_response = api_client.post(reverse("careers:portfolio-ai-github"), {"project_id": str(project.id)}, format="json")
    skills_response = api_client.post(reverse("careers:portfolio-ai-skills"))

    assert project_response.status_code == 201
    assert project_response.json()["data"]["project_score"] > 0
    assert github_response.status_code == 201
    assert github_response.json()["data"]["github_score"] > 0
    assert skills_response.status_code == 201
    assert "Python" in skills_response.json()["data"]["extracted_skills"]["normalized"]


def test_portfolio_job_match_and_analytics(api_client):
    user = UserFactory()
    _portfolio(user)
    job = _job()
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("careers:portfolio-ai-job-match"), {"job_id": str(job.id)}, format="json")
    history = api_client.get(reverse("careers:portfolio-ai-history"))
    analytics = api_client.get(reverse("careers:portfolio-ai-analytics"))

    assert response.status_code == 201
    assert response.json()["data"]["match_score"] > 0
    assert history.status_code == 200
    assert len(history.json()["data"]) == 1
    assert analytics.status_code == 200
    assert analytics.json()["data"]["review_count"] == 1


def test_portfolio_ai_permissions(api_client):
    user = UserFactory()
    project_owner = UserFactory()
    _, project = _portfolio(project_owner)
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("careers:portfolio-ai-project-review"), {"project_id": str(project.id)}, format="json")

    assert response.status_code == 404


def test_recruiter_portfolio_summary_requires_visibility(api_client):
    owner = UserFactory(username="candidate-ai-portfolio")
    recruiter = UserFactory()
    portfolio, _ = _portfolio(owner)
    PortfolioAIReview.objects.create(user=owner, portfolio=portfolio, review_type=PortfolioAIReviewType.PORTFOLIO_REVIEW, overall_score=82, confidence=74)
    organization = Organization.objects.create(name="Hiring Portfolio Org", slug="hiring-portfolio-org", organization_type="company")
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    api_client.force_authenticate(user=recruiter)

    denied = api_client.get(reverse("careers:portfolio-ai-recruiter-summary", args=[owner.username]), {"organization_id": str(organization.id)})
    OrganizationRecruiterEntitlement.objects.create(organization=organization, can_search_candidates=True, can_view_candidate_profiles=True)
    CandidateProfileUnlock.objects.create(organization=organization, candidate=owner, unlocked_by=recruiter)
    allowed = api_client.get(reverse("careers:portfolio-ai-recruiter-summary", args=[owner.username]), {"organization_id": str(organization.id)})

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert "overall_score" in allowed.json()["data"]
    assert "report" not in allowed.json()["data"]


def test_portfolio_ai_feature_flag_and_budget_are_enforced(api_client):
    user = UserFactory()
    _portfolio(user)
    AIFeatureFlag.objects.create(feature=AIFeature.PORTFOLIO_REVIEW, user=user, is_enabled=False, reason="test")
    api_client.force_authenticate(user=user)

    disabled = api_client.post(reverse("careers:portfolio-ai-review"))
    assert disabled.status_code == 403

    AIFeatureFlag.objects.filter(user=user).delete()
    AIBudgetPolicy.objects.create(scope="user", user=user, feature=AIFeature.PORTFOLIO_REVIEW, daily_request_limit=0)
    over_budget = api_client.post(reverse("careers:portfolio-ai-review"))
    assert over_budget.status_code == 403


def test_portfolio_ai_stream_endpoint(api_client):
    user = UserFactory()
    _portfolio(user)
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("careers:portfolio-ai-review-stream"))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/event-stream")
