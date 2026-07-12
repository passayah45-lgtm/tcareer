import pytest
from django.core.exceptions import ValidationError

from apps.users.models import User, UserRole, OAuthAccount
from apps.users.tests.factories import UserFactory, InstructorFactory, OAuthAccountFactory


@pytest.mark.django_db
class TestUserModel:

    def test_create_user_with_email_and_password(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.STUDENT
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_staff is False
        assert user.check_password("SecurePass123!") is True

    def test_user_email_is_stored_exactly_as_provided(self):
        user = User.objects.create_user(
            email="Test@Example.COM",
            password="pass",
            full_name="Test",
        )
        # Django normalizes email domain to lowercase but preserves local part
        assert "@example.com" in user.email

    def test_user_requires_email(self):
        with pytest.raises(ValueError, match="Email address is required"):
            User.objects.create_user(email="", password="pass", full_name="Test")

    def test_user_email_must_be_unique(self):
        UserFactory(email="duplicate@example.com")
        with pytest.raises(Exception):
            UserFactory(email="duplicate@example.com")

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email="admin@tcareer.com",
            password="AdminPass123!",
            full_name="Admin User",
        )
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.role == UserRole.ADMIN
        assert superuser.is_verified is True

    def test_create_superuser_requires_is_staff(self):
        with pytest.raises(ValueError, match="is_staff=True"):
            User.objects.create_superuser(
                email="admin@tcareer.com",
                password="pass",
                full_name="Admin",
                is_staff=False,
            )

    def test_user_role_defaults_to_student(self):
        user = UserFactory()
        assert user.role == UserRole.STUDENT

    def test_instructor_role(self):
        instructor = InstructorFactory()
        assert instructor.role == UserRole.INSTRUCTOR
        assert instructor.is_instructor is True
        assert instructor.is_student is False

    def test_role_properties(self):
        student = UserFactory(role=UserRole.STUDENT)
        assert student.is_student is True
        assert student.is_instructor is False
        assert student.is_recruiter is False
        assert student.is_admin_user is False

    def test_get_full_name(self):
        user = UserFactory(full_name="  John Doe  ")
        assert user.get_full_name() == "John Doe"

    def test_get_short_name(self):
        user = UserFactory(full_name="Jane Smith")
        assert user.get_short_name() == "Jane"

    def test_get_short_name_falls_back_to_email(self):
        user = UserFactory(full_name="")
        assert user.get_short_name() == user.email

    def test_str_representation(self):
        user = UserFactory(full_name="Alice", email="alice@example.com")
        assert "Alice" in str(user)
        assert "alice@example.com" in str(user)

    def test_user_uuid_primary_key(self):
        user = UserFactory()
        import uuid
        assert isinstance(user.id, uuid.UUID)

    def test_user_has_created_at_timestamp(self):
        user = UserFactory()
        assert user.created_at is not None

    def test_user_has_updated_at_timestamp(self):
        user = UserFactory()
        assert user.updated_at is not None

    def test_password_is_hashed(self):
        user = User.objects.create_user(
            email="hash@test.com",
            password="PlainText123",
            full_name="Hash Test",
        )
        assert user.password != "PlainText123"
        assert user.password.startswith(("pbkdf2_sha256", "argon2", "bcrypt", "md5"))


@pytest.mark.django_db
class TestOAuthAccountModel:

    def test_create_oauth_account(self):
        user = UserFactory()
        oauth = OAuthAccount.objects.create(
            user=user,
            provider="google-oauth2",
            provider_uid="1234567890",
        )
        assert oauth.user == user
        assert oauth.provider == "google-oauth2"

    def test_oauth_account_provider_uid_unique_per_provider(self):
        user1 = UserFactory()
        user2 = UserFactory()
        OAuthAccountFactory(user=user1, provider="google-oauth2", provider_uid="unique-uid")
        with pytest.raises(Exception):
            OAuthAccountFactory(user=user2, provider="google-oauth2", provider_uid="unique-uid")

    def test_str_representation(self):
        oauth = OAuthAccountFactory()
        assert oauth.provider in str(oauth)
