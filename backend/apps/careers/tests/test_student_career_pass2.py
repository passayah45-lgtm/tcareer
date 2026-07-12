import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.analytics.models import AnalyticsEvent
from apps.careers.models import (
    CareerResume,
    Portfolio,
    PortfolioProject,
    PortfolioProjectMedia,
    ResumeAnalytics,
    VisibilityChoice,
)
from apps.users.tests.factories import UserFactory
from apps.users.tests.factories import AdminFactory


pytestmark = pytest.mark.django_db


def test_multi_resume_crud_and_default_rules(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    first = api_client.post(
        reverse("careers:career-resumes"),
        {"title": "Data Resume", "target_role": "Data Analyst", "skills": ["SQL"]},
        format="json",
    )
    second = api_client.post(
        reverse("careers:career-resumes"),
        {"title": "Backend Resume", "target_role": "Django Developer", "is_default": True},
        format="json",
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert CareerResume.objects.get(id=second.json()["data"]["id"]).is_default is True
    assert CareerResume.objects.get(id=first.json()["data"]["id"]).is_default is False

    response = api_client.patch(
        reverse("careers:career-resume-detail", args=[second.json()["data"]["id"]]),
        {"summary": "Updated summary"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["data"]["versions"]
    assert AnalyticsEvent.objects.filter(name="resume_updated").exists()


def test_resume_download_tracking(api_client):
    user = UserFactory()
    resume = CareerResume.objects.create(user=user, title="Private Resume", is_default=True)
    api_client.force_authenticate(user=user)
    api_client.post(
        reverse("careers:career-resume-file-upload", args=[resume.id]),
        {"file_url": "https://example.com/private.pdf", "file_name": "private.pdf", "is_private": True},
        format="json",
    )

    response = api_client.post(reverse("careers:career-resume-download", args=[resume.id]))

    assert response.status_code == 200
    assert ResumeAnalytics.objects.filter(resume=resume, event_type=ResumeAnalytics.EventType.DOWNLOADED).exists()
    assert AnalyticsEvent.objects.filter(name="resume_downloaded").exists()


def test_storage_resume_upload_validates_file_type_and_size(api_client):
    user = UserFactory()
    resume = CareerResume.objects.create(user=user, title="Private Resume", is_default=True)
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("careers:career-resume-file-upload", args=[resume.id]),
        {"file": SimpleUploadedFile("resume.pdf", b"%PDF-1.4", content_type="application/pdf")},
        format="multipart",
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["file_name"] == "resume.pdf"
    assert payload["is_private"] is True

    response = api_client.post(
        reverse("careers:career-resume-file-upload", args=[resume.id]),
        {"file": SimpleUploadedFile("resume.exe", b"bad", content_type="application/x-msdownload")},
        format="multipart",
    )
    assert response.status_code == 400


def test_resume_download_requires_owner_or_admin(api_client):
    owner = UserFactory()
    stranger = UserFactory()
    admin = AdminFactory()
    resume = CareerResume.objects.create(user=owner, title="Private Resume", is_default=True)
    resume.files.create(
        file_url="https://example.com/private.pdf",
        file_name="private.pdf",
        content_type="application/pdf",
        is_private=True,
        uploaded_by=owner,
    )

    api_client.force_authenticate(user=stranger)
    response = api_client.post(reverse("careers:career-resume-download", args=[resume.id]))
    assert response.status_code == 403

    api_client.force_authenticate(user=admin)
    response = api_client.post(reverse("careers:career-resume-download", args=[resume.id]))
    assert response.status_code == 200
    assert response.json()["data"]["download_url"] == "https://example.com/private.pdf"


def test_private_project_media_is_hidden_from_public_portfolio(api_client):
    owner = UserFactory(username="owner")
    viewer = UserFactory()
    portfolio = Portfolio.objects.create(user=owner, visibility=VisibilityChoice.PUBLIC)
    project = PortfolioProject.objects.create(portfolio=portfolio, title="Capstone")
    PortfolioProjectMedia.objects.create(project=project, media_type="image", url="https://example.com/public.png")
    PortfolioProjectMedia.objects.create(
        project=project,
        media_type="image",
        url="https://example.com/private.png",
        visibility=VisibilityChoice.PRIVATE,
    )

    api_client.force_authenticate(user=viewer)
    response = api_client.get(reverse("careers:portfolio-public", args=[owner.username]))

    assert response.status_code == 200
    media = response.json()["data"]["projects"][0]["media"]
    assert [item["url"] for item in media] == ["https://example.com/public.png"]


def test_portfolio_media_upload_validation(api_client):
    owner = UserFactory()
    portfolio = Portfolio.objects.create(user=owner, visibility=VisibilityChoice.PUBLIC)
    project = PortfolioProject.objects.create(portfolio=portfolio, title="Capstone")
    api_client.force_authenticate(user=owner)

    response = api_client.post(
        reverse("careers:project-media-create", args=[project.id]),
        {"file": SimpleUploadedFile("screen.png", b"png", content_type="image/png")},
        format="multipart",
    )
    assert response.status_code == 201
    assert response.json()["data"]["file_name"] == "screen.png"

    response = api_client.post(
        reverse("careers:project-media-create", args=[project.id]),
        {"file": SimpleUploadedFile("clip.mp4", b"video", content_type="video/mp4")},
        format="multipart",
    )
    assert response.status_code == 400
