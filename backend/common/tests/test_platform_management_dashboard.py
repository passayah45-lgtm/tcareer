import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.users.models import UserRole
from apps.users.tests.factories import AdminFactory, UserFactory
from common.permissions import IsAdmin


pytestmark = pytest.mark.django_db


def test_platform_management_dashboard_requires_authentication(api_client):
    response = api_client.get(reverse("platform-management-dashboard"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_platform_management_dashboard_rejects_student(api_client):
    student = UserFactory(role=UserRole.STUDENT)
    api_client.force_authenticate(user=student)

    response = api_client.get(reverse("platform-management-dashboard"))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.PLATFORM_ADMIN, UserRole.SUPER_ADMIN])
def test_platform_management_dashboard_allows_platform_roles(api_client, role):
    user = UserFactory(role=role, is_staff=True, is_verified=True)
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse("platform-management-dashboard"),
        SERVER_NAME="admin.tcareer.test",
        secure=True,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["summary"]["users"] >= 1
    section_labels = {section["label"] for section in response.data["sections"]}
    assert "Django admin" not in section_labels
    assert response.data["sections"][-1]["label"] == "Operations queues"
    assert response.data["sections"][-1]["href"] == "/platform/operations"
    assert {"summary", "learning", "career", "organizations", "trust", "ai", "notifications", "revenue"} <= set(response.data)


def test_platform_management_dashboard_allows_django_superuser(api_client):
    superuser = UserFactory(role=UserRole.STUDENT, is_staff=True, is_superuser=True)
    api_client.force_authenticate(user=superuser)

    response = api_client.get(reverse("platform-management-dashboard"))

    assert response.status_code == status.HTTP_200_OK


def test_is_admin_permission_uses_platform_admin_service():
    factory = APIRequestFactory()
    permission = IsAdmin()

    for user in (
        AdminFactory(),
        UserFactory(role=UserRole.PLATFORM_ADMIN),
        UserFactory(role=UserRole.SUPER_ADMIN),
        UserFactory(role=UserRole.STUDENT, is_superuser=True),
    ):
        request = factory.get("/admin-only/")
        request.user = user
        assert permission.has_permission(request, None)

    denied_request = factory.get("/admin-only/")
    denied_request.user = UserFactory(role=UserRole.STUDENT)
    assert not permission.has_permission(denied_request, None)
