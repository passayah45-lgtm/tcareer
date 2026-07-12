import pytest
from unittest.mock import patch, MagicMock
from django.core.cache import cache

from apps.users.models import User, UserRole, OAuthAccount
from apps.users.services import AuthService
from apps.users.tests.factories import UserFactory
from common.exceptions import ServiceError, ConflictError


@pytest.mark.django_db
class TestAuthServiceRegister:

    def test_register_creates_user(self):
        user = AuthService.register(
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User",
        )
        assert User.objects.filter(email="newuser@example.com").exists()
        assert user.full_name == "New User"
        assert user.role == UserRole.STUDENT

    def test_register_normalizes_email(self):
        user = AuthService.register(
            email="  NewUser@Example.COM  ",
            password="SecurePass123!",
            full_name="Test",
        )
        assert user.email == "newuser@example.com"

    def test_register_strips_full_name_whitespace(self):
        user = AuthService.register(
            email="test@example.com",
            password="SecurePass123!",
            full_name="  Padded Name  ",
        )
        assert user.full_name == "Padded Name"

    def test_register_with_instructor_role(self):
        user = AuthService.register(
            email="instructor@example.com",
            password="SecurePass123!",
            full_name="Instructor",
            role=UserRole.INSTRUCTOR,
        )
        assert user.role == UserRole.INSTRUCTOR

    def test_register_raises_conflict_for_duplicate_email(self):
        UserFactory(email="existing@example.com")
        with pytest.raises(ConflictError, match="already exists"):
            AuthService.register(
                email="existing@example.com",
                password="SecurePass123!",
                full_name="Duplicate",
            )

    def test_register_hashes_password(self):
        user = AuthService.register(
            email="hash@example.com",
            password="PlainPassword123!",
            full_name="Hash Test",
        )
        assert not user.check_password("wrong-password")
        assert user.check_password("PlainPassword123!")


@pytest.mark.django_db
class TestAuthServiceIssueTokens:

    def test_issue_tokens_returns_access_and_refresh(self):
        user = UserFactory()
        tokens = AuthService.issue_tokens(user)
        assert "access" in tokens
        assert "refresh" in tokens
        assert len(tokens["access"]) > 50
        assert len(tokens["refresh"]) > 50

    def test_issued_token_contains_user_claims(self):
        from rest_framework_simplejwt.tokens import AccessToken
        user = UserFactory(role=UserRole.INSTRUCTOR)
        tokens = AuthService.issue_tokens(user)
        access = AccessToken(tokens["access"])
        assert access["email"] == user.email
        assert access["role"] == UserRole.INSTRUCTOR
        assert access["full_name"] == user.full_name

    def test_tokens_are_different_for_different_users(self):
        user1 = UserFactory()
        user2 = UserFactory()
        tokens1 = AuthService.issue_tokens(user1)
        tokens2 = AuthService.issue_tokens(user2)
        assert tokens1["access"] != tokens2["access"]
        assert tokens1["refresh"] != tokens2["refresh"]


@pytest.mark.django_db
class TestAuthServiceRevokeToken:

    def test_revoke_valid_refresh_token(self):
        user = UserFactory()
        tokens = AuthService.issue_tokens(user)
        # Should not raise
        AuthService.revoke_refresh_token(tokens["refresh"])

    def test_revoke_invalid_token_does_not_raise(self):
        # Revoking an invalid token should fail silently
        AuthService.revoke_refresh_token("totally-invalid-token-string")

    def test_revoke_already_blacklisted_token_does_not_raise(self):
        user = UserFactory()
        tokens = AuthService.issue_tokens(user)
        AuthService.revoke_refresh_token(tokens["refresh"])
        # Revoking again should not raise
        AuthService.revoke_refresh_token(tokens["refresh"])


@pytest.mark.django_db
class TestAuthServiceGoogleAuth:

    def _mock_google_response(self, email="google@example.com", sub="12345", name="Google User"):
        return {
            "sub": sub,
            "email": email,
            "name": name,
            "picture": "https://lh3.googleusercontent.com/photo",
            "aud": "test-google-client-id",
            "email_verified": "true",
        }

    @patch("apps.users.services.requests.get")
    def test_google_auth_creates_new_user(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_google_response(),
        )
        user, created = AuthService.authenticate_google("valid-google-token")
        assert created is True
        assert user.email == "google@example.com"
        assert user.is_verified is True
        assert OAuthAccount.objects.filter(provider="google-oauth2", user=user).exists()

    @patch("apps.users.services.requests.get")
    def test_google_auth_returns_existing_user(self, mock_get):
        existing_user = UserFactory(email="google@example.com")
        OAuthAccount.objects.create(
            user=existing_user,
            provider="google-oauth2",
            provider_uid="12345",
        )
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_google_response(),
        )
        user, created = AuthService.authenticate_google("valid-google-token")
        assert created is False
        assert user.id == existing_user.id

    @patch("apps.users.services.requests.get")
    def test_google_auth_links_existing_email_account(self, mock_get):
        # User already has an account with the same email
        existing_user = UserFactory(email="google@example.com")
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_google_response(sub="new-sub"),
        )
        user, created = AuthService.authenticate_google("valid-google-token")
        assert created is False
        assert user.id == existing_user.id
        # OAuth account should have been created
        assert OAuthAccount.objects.filter(
            provider="google-oauth2",
            provider_uid="new-sub",
        ).exists()

    @patch("apps.users.services.requests.get")
    def test_google_auth_fails_with_invalid_token(self, mock_get):
        mock_get.return_value = MagicMock(status_code=400, json=lambda: {"error": "invalid_token"})
        with pytest.raises(ServiceError, match="Invalid Google token"):
            AuthService.authenticate_google("bad-token")

    @patch("apps.users.services.requests.get")
    def test_google_auth_fails_with_wrong_audience(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {**self._mock_google_response(), "aud": "other-app-client-id"},
        )
        with pytest.raises(ServiceError, match="not issued for T-Career"):
            AuthService.authenticate_google("token-for-other-app")

    @patch("apps.users.services.requests.get")
    def test_google_auth_fails_for_deactivated_user(self, mock_get):
        UserFactory(email="google@example.com", is_active=False)
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: self._mock_google_response(),
        )
        with pytest.raises(ServiceError, match="deactivated"):
            AuthService.authenticate_google("valid-token")


@pytest.mark.django_db
class TestAuthServiceChangePassword:

    def test_change_password_succeeds(self):
        user = UserFactory()
        user.set_password("OldPass123!")
        user.save()
        AuthService.change_password(user, "OldPass123!", "NewPass456!")
        user.refresh_from_db()
        assert user.check_password("NewPass456!")
        assert not user.check_password("OldPass123!")

    def test_change_password_fails_with_wrong_current(self):
        user = UserFactory()
        user.set_password("CorrectOldPass123!")
        user.save()
        with pytest.raises(ServiceError, match="Current password is incorrect"):
            AuthService.change_password(user, "WrongOldPass!", "NewPass456!")
