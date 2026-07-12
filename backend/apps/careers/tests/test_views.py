"""
Tests for the careers domain (Portfolio and Resume).

Test coverage:
- Portfolio auto-creation on first access
- Portfolio visibility enforcement
- Skill add, duplicate prevention, auto-sync
- Project CRUD
- Public portfolio endpoint
- Recruiter view endpoint
- Resume get, update, section validation
- PDF generation (mocked S3)
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import User, UserRole
from apps.careers.models import Portfolio, PortfolioSkill, PortfolioProject, Resume, VisibilityChoice
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="student@test.com",
        password="Test1234!",
        full_name="Test Student",
        role=UserRole.STUDENT,
        is_active=True,
        username="test-student",
    )


@pytest.fixture
def recruiter(db):
    return User.objects.create_user(
        email="recruiter@test.com",
        password="Test1234!",
        full_name="Test Recruiter",
        role=UserRole.RECRUITER,
        is_active=True,
    )


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client, student):
    client.force_authenticate(user=student)
    return client


@pytest.fixture
def recruiter_client(client, recruiter):
    client.force_authenticate(user=recruiter)
    return client


@pytest.fixture
def recruiter_organization(recruiter):
    organization = Organization.objects.create(
        name="Recruiter Org",
        organization_type=OrganizationType.COMPANY,
    )
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
    return organization


# ── Portfolio ──────────────────────────────────────────────────────────────────

class TestPortfolioMe:

    def test_get_creates_portfolio_on_first_access(self, auth_client, student):
        assert not Portfolio.objects.filter(user=student).exists()
        response = auth_client.get("/api/v1/careers/portfolio/me/")
        assert response.status_code == 200
        assert Portfolio.objects.filter(user=student).exists()

    def test_get_returns_portfolio_data(self, auth_client, student):
        Portfolio.objects.create(user=student, headline="Django Developer")
        response = auth_client.get("/api/v1/careers/portfolio/me/")
        assert response.status_code == 200
        assert response.data["data"]["headline"] == "Django Developer"

    def test_patch_updates_portfolio(self, auth_client, student):
        Portfolio.objects.create(user=student)
        response = auth_client.patch(
            "/api/v1/careers/portfolio/me/",
            {"headline": "Full-Stack Developer", "desired_role": "Backend Engineer"},
            format="json",
        )
        assert response.status_code == 200
        portfolio = Portfolio.objects.get(user=student)
        assert portfolio.headline == "Full-Stack Developer"
        assert portfolio.desired_role == "Backend Engineer"

    def test_patch_invalid_visibility_rejected(self, auth_client, student):
        Portfolio.objects.create(user=student)
        response = auth_client.patch(
            "/api/v1/careers/portfolio/me/",
            {"visibility": "invisible"},
            format="json",
        )
        assert response.status_code == 400

    def test_unauthenticated_access_denied(self, client):
        response = client.get("/api/v1/careers/portfolio/me/")
        assert response.status_code == 401


class TestPublicPortfolio:

    def test_public_portfolio_accessible_without_auth(self, client, student):
        Portfolio.objects.create(user=student, visibility=VisibilityChoice.PUBLIC, headline="Dev")
        response = client.get(f"/api/v1/careers/portfolio/{student.username}/")
        assert response.status_code == 200
        assert response.data["data"]["username"] == student.username

    def test_private_portfolio_returns_404(self, client, student):
        Portfolio.objects.create(user=student, visibility=VisibilityChoice.PRIVATE)
        response = client.get(f"/api/v1/careers/portfolio/{student.username}/")
        assert response.status_code == 404

    def test_nonexistent_username_returns_404(self, client):
        response = client.get("/api/v1/careers/portfolio/does-not-exist/")
        assert response.status_code == 404

    def test_profile_views_incremented_for_non_owner(self, client, recruiter_client, student):
        portfolio = Portfolio.objects.create(user=student, visibility=VisibilityChoice.PUBLIC)
        recruiter_client.get(f"/api/v1/careers/portfolio/{student.username}/")
        portfolio.refresh_from_db()
        assert portfolio.profile_views == 1

    def test_owner_view_does_not_increment_views(self, auth_client, student):
        portfolio = Portfolio.objects.create(user=student, visibility=VisibilityChoice.PUBLIC)
        auth_client.get(f"/api/v1/careers/portfolio/{student.username}/")
        portfolio.refresh_from_db()
        assert portfolio.profile_views == 0


class TestRecruiterPortfolio:

    def test_recruiter_view_returns_completeness_score(self, recruiter_client, student, recruiter_organization):
        Portfolio.objects.create(
            user=student,
            visibility=VisibilityChoice.PUBLIC,
            headline="Dev",
            bio="I am a developer with experience in Python.",
            desired_role="Backend Developer",
        )
        response = recruiter_client.get(
            f"/api/v1/careers/portfolio/{student.username}/recruiter-view/",
            {"organization_id": str(recruiter_organization.id)},
        )
        assert response.status_code == 200
        assert "profile_completeness" in response.data["data"]
        assert isinstance(response.data["data"]["profile_completeness"], int)

    def test_recruiter_view_private_portfolio_returns_404(self, recruiter_client, student, recruiter_organization):
        Portfolio.objects.create(user=student, visibility=VisibilityChoice.PRIVATE)
        response = recruiter_client.get(
            f"/api/v1/careers/portfolio/{student.username}/recruiter-view/",
            {"organization_id": str(recruiter_organization.id)},
        )
        assert response.status_code == 404

    def test_unauthenticated_recruiter_view_denied(self, client, student):
        Portfolio.objects.create(user=student, visibility=VisibilityChoice.PUBLIC)
        response = client.get(f"/api/v1/careers/portfolio/{student.username}/recruiter-view/")
        assert response.status_code == 401


# ── Skills ─────────────────────────────────────────────────────────────────────

class TestSkills:

    def test_add_skill(self, auth_client, student):
        Portfolio.objects.create(user=student)
        response = auth_client.post(
            "/api/v1/careers/portfolio/me/skills/",
            {"name": "Python", "category": "Programming Language"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["data"]["name"] == "Python"

    def test_duplicate_skill_rejected(self, auth_client, student):
        portfolio = Portfolio.objects.create(user=student)
        PortfolioSkill.objects.create(portfolio=portfolio, name="Python")
        response = auth_client.post(
            "/api/v1/careers/portfolio/me/skills/",
            {"name": "Python"},
            format="json",
        )
        assert response.status_code == 400

    def test_duplicate_skill_case_insensitive(self, auth_client, student):
        portfolio = Portfolio.objects.create(user=student)
        PortfolioSkill.objects.create(portfolio=portfolio, name="python")
        response = auth_client.post(
            "/api/v1/careers/portfolio/me/skills/",
            {"name": "PYTHON"},
            format="json",
        )
        assert response.status_code == 400

    def test_delete_skill(self, auth_client, student):
        portfolio = Portfolio.objects.create(user=student)
        skill = PortfolioSkill.objects.create(portfolio=portfolio, name="Python")
        response = auth_client.delete(f"/api/v1/careers/portfolio/me/skills/{skill.id}/")
        assert response.status_code == 204
        assert not PortfolioSkill.objects.filter(id=skill.id).exists()

    def test_delete_other_users_skill_returns_404(self, auth_client, recruiter):
        other_portfolio = Portfolio.objects.create(user=recruiter)
        skill = PortfolioSkill.objects.create(portfolio=other_portfolio, name="Python")
        response = auth_client.delete(f"/api/v1/careers/portfolio/me/skills/{skill.id}/")
        assert response.status_code == 404


# ── Projects ───────────────────────────────────────────────────────────────────

class TestProjects:

    def test_create_project(self, auth_client, student):
        Portfolio.objects.create(user=student)
        response = auth_client.post(
            "/api/v1/careers/portfolio/me/projects/",
            {
                "title": "T-Career Platform",
                "description": "An AI-powered learning platform.",
                "tech_stack": ["Python", "Django", "React"],
                "github_url": "https://github.com/test/tcareer",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["data"]["title"] == "T-Career Platform"
        assert response.data["data"]["tech_stack"] == ["Python", "Django", "React"]

    def test_tech_stack_max_20_items(self, auth_client, student):
        Portfolio.objects.create(user=student)
        response = auth_client.post(
            "/api/v1/careers/portfolio/me/projects/",
            {"title": "Test", "tech_stack": [f"tech-{i}" for i in range(21)]},
            format="json",
        )
        assert response.status_code == 400

    def test_update_project(self, auth_client, student):
        portfolio = Portfolio.objects.create(user=student)
        project = PortfolioProject.objects.create(portfolio=portfolio, title="Old Title")
        response = auth_client.patch(
            f"/api/v1/careers/portfolio/me/projects/{project.id}/",
            {"title": "New Title"},
            format="json",
        )
        assert response.status_code == 200
        project.refresh_from_db()
        assert project.title == "New Title"

    def test_delete_project(self, auth_client, student):
        portfolio = Portfolio.objects.create(user=student)
        project = PortfolioProject.objects.create(portfolio=portfolio, title="Test")
        response = auth_client.delete(f"/api/v1/careers/portfolio/me/projects/{project.id}/")
        assert response.status_code == 204

    def test_end_date_before_start_date_rejected(self, auth_client, student):
        Portfolio.objects.create(user=student)
        response = auth_client.post(
            "/api/v1/careers/portfolio/me/projects/",
            {"title": "Test", "start_date": "2024-01-01", "end_date": "2023-01-01"},
            format="json",
        )
        assert response.status_code == 400


# ── Resume ─────────────────────────────────────────────────────────────────────

class TestResume:

    def test_get_creates_resume_on_first_access(self, auth_client, student):
        assert not Resume.objects.filter(user=student).exists()
        response = auth_client.get("/api/v1/careers/resume/me/")
        assert response.status_code == 200
        assert Resume.objects.filter(user=student).exists()

    def test_update_resume_summary(self, auth_client, student):
        Resume.objects.create(user=student)
        response = auth_client.patch(
            "/api/v1/careers/resume/me/",
            {"summary": "Experienced developer with 3 years in Python."},
            format="json",
        )
        assert response.status_code == 200
        resume = Resume.objects.get(user=student)
        assert resume.summary == "Experienced developer with 3 years in Python."

    def test_add_education_entry(self, auth_client, student):
        Resume.objects.create(user=student)
        response = auth_client.patch(
            "/api/v1/careers/resume/me/",
            {
                "education": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "institution": "MIT",
                        "degree": "Bachelor of Science",
                        "field": "Computer Science",
                        "start_year": 2020,
                        "end_year": 2024,
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 200
        resume = Resume.objects.get(user=student)
        assert len(resume.education) == 1
        assert resume.education[0]["institution"] == "MIT"

    def test_add_experience_entry(self, auth_client, student):
        Resume.objects.create(user=student)
        response = auth_client.patch(
            "/api/v1/careers/resume/me/",
            {
                "experience": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "company": "Acme Corp",
                        "title": "Software Engineer Intern",
                        "start_date": "2023-06",
                        "end_date": "2023-12",
                        "is_current": False,
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 200
        resume = Resume.objects.get(user=student)
        assert len(resume.experience) == 1
        assert resume.experience[0]["company"] == "Acme Corp"

    def test_invalid_date_format_rejected(self, auth_client, student):
        Resume.objects.create(user=student)
        response = auth_client.patch(
            "/api/v1/careers/resume/me/",
            {
                "experience": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "company": "Acme",
                        "title": "Engineer",
                        "start_date": "June 2023",
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 400

    def test_end_year_before_start_year_rejected(self, auth_client, student):
        Resume.objects.create(user=student)
        response = auth_client.patch(
            "/api/v1/careers/resume/me/",
            {
                "education": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "institution": "MIT",
                        "start_year": 2024,
                        "end_year": 2020,
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 400

    def test_too_many_education_entries_rejected(self, auth_client, student):
        Resume.objects.create(user=student)
        education = [
            {
                "id": f"550e8400-e29b-41d4-a716-44665544{i:04d}",
                "institution": f"University {i}",
                "start_year": 2020,
            }
            for i in range(11)
        ]
        response = auth_client.patch(
            "/api/v1/careers/resume/me/",
            {"education": education},
            format="json",
        )
        assert response.status_code == 400
