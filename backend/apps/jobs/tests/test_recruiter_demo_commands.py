import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.analytics.models import AnalyticsEvent
from apps.careers.models import Portfolio, Resume
from apps.jobs.management.commands.recruiter_demo import SOURCE
from apps.jobs.models import Interview, JobApplication, JobListing, SavedCandidate, TalentPool
from apps.organizations.models import CandidateProfileUnlock, Organization, OrganizationRecruiterEntitlement
from apps.users.models import User, UserRole


pytestmark = pytest.mark.django_db


def enable_demo(monkeypatch):
    monkeypatch.setenv("ALLOW_RECRUITER_DEMO_COMMANDS", "True")
    monkeypatch.setenv("TCAREER_DEMO_PASSWORD", "TestDemoPass123!")


@override_settings(DEBUG=False)
def test_seed_recruiter_demo_creates_expected_records(monkeypatch):
    enable_demo(monkeypatch)

    call_command("seed_recruiter_demo")

    company = Organization.objects.get(slug="technova-africa-demo")
    assert Organization.objects.filter(slug="conakry-digital-university-demo").exists()
    assert User.objects.filter(email="company.admin@tcareer.demo", role=UserRole.COMPANY_ADMIN).exists()
    assert User.objects.filter(email="recruiter@tcareer.demo", role=UserRole.RECRUITER).exists()
    assert User.objects.filter(email="student@tcareer.demo", role=UserRole.STUDENT).exists()
    assert OrganizationRecruiterEntitlement.objects.filter(organization=company, can_post_jobs=True).exists()
    assert JobListing.objects.filter(organization=company).count() == 4
    assert JobApplication.objects.filter(organization=company).count() == 8
    assert Interview.objects.filter(organization=company).count() >= 3
    assert TalentPool.objects.filter(organization=company).exists()
    assert SavedCandidate.objects.filter(organization=company).count() == 3
    assert CandidateProfileUnlock.objects.filter(organization=company).count() == 3
    assert Portfolio.objects.filter(user__email__endswith="@tcareer.demo").count() >= 5
    assert Resume.objects.filter(user__email__endswith="@tcareer.demo").count() >= 5
    assert AnalyticsEvent.objects.filter(metadata__source=SOURCE).exists()


@override_settings(DEBUG=False)
def test_seed_recruiter_demo_is_idempotent(monkeypatch):
    enable_demo(monkeypatch)

    call_command("seed_recruiter_demo")
    counts = {
        "users": User.objects.filter(email__endswith="@tcareer.demo").count(),
        "orgs": Organization.objects.filter(slug__in=["technova-africa-demo", "conakry-digital-university-demo"]).count(),
        "jobs": JobListing.objects.filter(organization__slug="technova-africa-demo").count(),
        "applications": JobApplication.objects.filter(organization__slug="technova-africa-demo").count(),
        "saved": SavedCandidate.objects.filter(organization__slug="technova-africa-demo").count(),
    }

    call_command("seed_recruiter_demo")

    assert User.objects.filter(email__endswith="@tcareer.demo").count() == counts["users"]
    assert Organization.objects.filter(slug__in=["technova-africa-demo", "conakry-digital-university-demo"]).count() == counts["orgs"]
    assert JobListing.objects.filter(organization__slug="technova-africa-demo").count() == counts["jobs"]
    assert JobApplication.objects.filter(organization__slug="technova-africa-demo").count() == counts["applications"]
    assert SavedCandidate.objects.filter(organization__slug="technova-africa-demo").count() == counts["saved"]


@override_settings(DEBUG=False)
def test_reset_recruiter_demo_removes_demo_data(monkeypatch):
    enable_demo(monkeypatch)
    call_command("seed_recruiter_demo")

    call_command("reset_recruiter_demo")

    assert not User.objects.filter(email__endswith="@tcareer.demo").exists()
    assert not Organization.objects.filter(slug__in=["technova-africa-demo", "conakry-digital-university-demo"]).exists()
    assert not JobApplication.objects.filter(source=SOURCE).exists()
    assert not AnalyticsEvent.objects.filter(metadata__source=SOURCE).exists()


@override_settings(DEBUG=False)
def test_reset_recruiter_demo_does_not_delete_non_demo_data(monkeypatch):
    enable_demo(monkeypatch)
    real_user = User.objects.create_user(
        email="real.company@example.com",
        password="RealPass123!",
        full_name="Real Company Admin",
        role=UserRole.COMPANY_ADMIN,
    )
    real_org = Organization.objects.create(
        name="Real Company",
        slug="real-company",
        organization_type="company",
        status="active",
        created_by=real_user,
    )

    call_command("seed_recruiter_demo")
    call_command("reset_recruiter_demo")

    assert User.objects.filter(id=real_user.id).exists()
    assert Organization.objects.filter(id=real_org.id).exists()


@override_settings(DEBUG=False)
def test_demo_users_are_blocked_in_production_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_RECRUITER_DEMO_COMMANDS", raising=False)
    monkeypatch.setenv("TCAREER_DEMO_PASSWORD", "TestDemoPass123!")

    with pytest.raises(CommandError):
        call_command("seed_recruiter_demo")

