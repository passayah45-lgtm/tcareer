from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import UserRole
from apps.users.tests.factories import UserFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def authenticated_client(client):
    user = UserFactory()
    user.set_password("TestPass123!")
    user.save()
    response = client.post(
        reverse("users:login"),
        {"email": user.email, "password": "TestPass123!"},
        format="json",
    )
    # response.json() gives the full envelope; response.data is the pre-render dict
    token = response.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    client.user = user
    return client


@pytest.mark.django_db
class TestRegisterEndpoint:

    def test_register_success(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "New User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "access" in data["data"]
        assert "refresh" not in data["data"]
        assert response.cookies.get("tcareer_refresh") is not None
        assert response.cookies.get("tcareer_csrf") is not None
        assert response.cookies["tcareer_refresh"]["httponly"]
        assert response.cookies["tcareer_refresh"]["path"] == "/api/v1/auth/"
        assert response.cookies["tcareer_csrf"]["path"] == "/"
        assert data["data"]["user"]["email"] == "newuser@example.com"
        assert data["data"]["user"]["role"] == "student"

    def test_register_creates_student_by_default(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "student@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "Student User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["user"]["role"] == UserRole.STUDENT

    def test_register_as_instructor(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "instructor@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "Instructor User",
                "role": "instructor",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["user"]["role"] == UserRole.INSTRUCTOR

    def test_register_as_mentor(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "mentor@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "Mentor User",
                "role": "mentor",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["user"]["role"] == UserRole.MENTOR

    def test_register_as_recruiter(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "recruiter@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "Recruiter User",
                "role": "recruiter",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["user"]["role"] == UserRole.RECRUITER

    def test_register_missing_email(self, client):
        response = client.post(
            reverse("users:register"),
            {"password": "SecurePass123!", "full_name": "Test"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["success"] is False
        assert "email" in response.json()["errors"]

    def test_register_invalid_email(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "not-an-email",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "Test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "test@example.com",
                "password": "SecurePass123!",
                "password_confirm": "DifferentPass123!",
                "full_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, client):
        response = client.post(
            reverse("users:register"),
            {
                "email": "test@example.com",
                "password": "123",
                "password_confirm": "123",
                "full_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, client):
        UserFactory(email="taken@example.com")
        response = client.post(
            reverse("users:register"),
            {
                "email": "taken@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "Second User",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "role",
        [
            UserRole.ADMIN,
            UserRole.COMPANY_ADMIN,
            UserRole.UNIVERSITY_ADMIN,
            UserRole.CONTENT_MODERATOR,
            UserRole.FINANCE_ADMIN,
            UserRole.PLATFORM_ADMIN,
            UserRole.SUPER_ADMIN,
        ],
    )
    def test_register_does_not_accept_admin_roles(self, client, role):
        response = client.post(
            reverse("users:register"),
            {
                "email": f"{role}@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "full_name": "Privileged User",
                "role": role,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginEndpoint:

    def test_login_success(self, client):
        user = UserFactory()
        user.set_password("TestPass123!")
        user.save()
        response = client.post(
            reverse("users:login"),
            {"email": user.email, "password": "TestPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "access" in data
        assert "refresh" not in data
        assert response.cookies.get("tcareer_refresh") is not None
        assert response.cookies.get("tcareer_csrf") is not None
        assert response.cookies["tcareer_refresh"]["httponly"]
        assert response.cookies["tcareer_refresh"]["path"] == "/api/v1/auth/"
        assert response.cookies["tcareer_csrf"]["path"] == "/"
        assert data["user"]["email"] == user.email
        assert data["user"]["role"] == user.role

    def test_login_wrong_password(self, client):
        user = UserFactory()
        user.set_password("CorrectPass123!")
        user.save()
        response = client.post(
            reverse("users:login"),
            {"email": user.email, "password": "WrongPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_email(self, client):
        response = client.post(
            reverse("users:login"),
            {"email": "nobody@example.com", "password": "SomePass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user(self, client):
        user = UserFactory(is_active=False)
        user.set_password("TestPass123!")
        user.save()
        response = client.post(
            reverse("users:login"),
            {"email": user.email, "password": "TestPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_response_includes_user_data(self, client):
        user = UserFactory(full_name="John Doe", role=UserRole.INSTRUCTOR)
        user.set_password("TestPass123!")
        user.save()
        response = client.post(
            reverse("users:login"),
            {"email": user.email, "password": "TestPass123!"},
            format="json",
        )
        user_data = response.json()["data"]["user"]
        assert user_data["full_name"] == "John Doe"
        assert user_data["role"] == UserRole.INSTRUCTOR
        assert "password" not in user_data
        assert "password_hash" not in user_data


@pytest.mark.django_db
class TestTokenRefreshEndpoint:

    def test_refresh_returns_new_access_token(self, client):
        user = UserFactory()
        user.set_password("TestPass123!")
        user.save()
        login_response = client.post(
            reverse("users:login"),
            {"email": user.email, "password": "TestPass123!"},
            format="json",
        )
        refresh_token = login_response.cookies["tcareer_refresh"].value
        csrf_token = login_response.cookies["tcareer_csrf"].value

        response = client.post(
            reverse("users:token-refresh"),
            {"refresh": refresh_token},
            HTTP_X_CSRFTOKEN=csrf_token,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()["data"]
        assert "refresh" not in response.json()["data"]

    def test_refresh_with_invalid_token(self, client):
        response = client.post(
            reverse("users:token-refresh"),
            {"refresh": "this-is-not-a-valid-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogoutEndpoint:

    def test_logout_success(self, authenticated_client):
        user = authenticated_client.user
        user.set_password("TestPass123!")
        user.save()

        login_response = authenticated_client.post(
            reverse("users:login"),
            {"email": user.email, "password": "TestPass123!"},
            format="json",
        )
        refresh_token = login_response.cookies["tcareer_refresh"].value
        csrf_token = login_response.cookies["tcareer_csrf"].value

        response = authenticated_client.post(
            reverse("users:logout"),
            {"refresh": refresh_token},
            HTTP_X_CSRFTOKEN=csrf_token,
            format="json",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_requires_authentication(self, client):
        response = client.post(
            reverse("users:logout"),
            {"refresh": "some-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_requires_refresh_token(self, authenticated_client):
        authenticated_client.cookies.pop("tcareer_refresh", None)
        authenticated_client.cookies.pop("tcareer_csrf", None)
        response = authenticated_client.post(
            reverse("users:logout"),
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMeEndpoint:

    def test_me_returns_user_data(self, authenticated_client):
        response = authenticated_client.get(reverse("users:me"))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["email"] == authenticated_client.user.email
        assert "password" not in data

    def test_me_requires_authentication(self, client):
        response = client.get(reverse("users:me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_expired_token(self, client):
        client.credentials(HTTP_AUTHORIZATION="Bearer expired-or-fake-token")
        response = client.get(reverse("users:me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestGoogleAuthEndpoint:

    @patch("apps.users.services.requests.get")
    def test_google_auth_success_new_user(self, mock_get, client):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "sub": "google-uid-123",
                "email": "google@example.com",
                "name": "Google User",
                "picture": "https://lh3.googleusercontent.com/photo",
                "aud": "test-google-client-id",
                "email_verified": "true",
            },
        )
        response = client.post(
            reverse("users:google-auth"),
            {"id_token": "valid-google-id-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["created"] is True
        assert "access" in data
        assert "refresh" not in data
        assert response.cookies.get("tcareer_refresh") is not None
        assert data["user"]["email"] == "google@example.com"

    @patch("apps.users.services.requests.get")
    def test_google_auth_returns_200_for_existing_user(self, mock_get, client):
        UserFactory(email="existing@example.com")
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "sub": "google-uid-456",
                "email": "existing@example.com",
                "name": "Existing User",
                "picture": "",
                "aud": "test-google-client-id",
                "email_verified": "true",
            },
        )
        response = client.post(
            reverse("users:google-auth"),
            {"id_token": "valid-google-id-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["created"] is False

    @patch("apps.users.services.requests.get")
    def test_google_auth_fails_with_invalid_token(self, mock_get, client):
        mock_get.return_value = MagicMock(status_code=400, json=lambda: {"error": "invalid"})
        response = client.post(
            reverse("users:google-auth"),
            {"id_token": "bad-token"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_google_auth_missing_token(self, client):
        response = client.post(
            reverse("users:google-auth"),
            {},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestChangePasswordEndpoint:

    def test_change_password_success(self, authenticated_client):
        user = authenticated_client.user
        user.set_password("OldPass123!")
        user.save()

        response = authenticated_client.post(
            reverse("users:change-password"),
            {
                "current_password": "OldPass123!",
                "new_password": "NewPass456!",
                "new_password_confirm": "NewPass456!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.check_password("NewPass456!")

    def test_change_password_wrong_current(self, authenticated_client):
        user = authenticated_client.user
        user.set_password("RealPass123!")
        user.save()

        response = authenticated_client.post(
            reverse("users:change-password"),
            {
                "current_password": "WrongPass123!",
                "new_password": "NewPass456!",
                "new_password_confirm": "NewPass456!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_requires_auth(self, client):
        response = client.post(
            reverse("users:change-password"),
            {
                "current_password": "Old",
                "new_password": "New123!",
                "new_password_confirm": "New123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
