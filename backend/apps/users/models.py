import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from common.models import BaseModel


class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    INSTRUCTOR = "instructor", "Instructor"
    MENTOR = "mentor", "Mentor"
    RECRUITER = "recruiter", "Recruiter"
    COMPANY_ADMIN = "company_admin", "Company Admin"
    UNIVERSITY_ADMIN = "university_admin", "University Admin"
    CONTENT_MODERATOR = "content_moderator", "Content Moderator"
    FINANCE_ADMIN = "finance_admin", "Finance Admin"
    PLATFORM_ADMIN = "platform_admin", "Platform Admin"
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "Admin"


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", UserRole.STUDENT)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("role", UserRole.ADMIN)
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    # Core fields
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    avatar_url = models.URLField(max_length=500, blank=True, default="")
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # Public profile fields added in Sprint 5
    username = models.SlugField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Public profile URL slug. e.g. john-doe",
    )
    profile_headline = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Short professional tagline shown on profile.",
    )
    profile_bio = models.TextField(blank=True, default="")
    profile_location = models.CharField(max_length=100, blank=True, default="")
    linkedin_url = models.URLField(blank=True, default="")
    github_url = models.URLField(blank=True, default="")
    is_public_profile = models.BooleanField(
        default=True,
        help_text="If true, profile is visible to recruiters and public.",
    )
    is_email_verified = models.BooleanField(
        default=False,
        help_text="True after the user clicks the verification link in their email.",
    )

    # Global locale fields added in Global Foundation
    nationality = models.CharField(
        max_length=2,
        blank=True,
        default="",
        help_text="ISO 3166-1 alpha-2 country code. e.g. GN",
    )
    current_country = models.CharField(
        max_length=2,
        blank=True,
        default="GN",
        help_text="Country where the user currently lives.",
    )
    preferred_language = models.CharField(
        max_length=10,
        blank=True,
        default="fr",
        help_text="BCP 47 language code. e.g. fr, en, ar",
    )
    preferred_currency = models.CharField(
        max_length=3,
        blank=True,
        default="GNF",
        help_text="ISO 4217 currency code. e.g. GNF, USD",
    )
    timezone = models.CharField(
        max_length=50,
        blank=True,
        default="Africa/Conakry",
        help_text="IANA timezone. e.g. Africa/Conakry, Europe/Paris",
    )
    locale = models.CharField(
        max_length=20,
        blank=True,
        default="fr-GN",
        help_text="Full locale string. e.g. fr-GN, en-US",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["username"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["current_country"]),
            models.Index(fields=["preferred_language"]),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"

    @property
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT

    @property
    def is_instructor(self) -> bool:
        return self.role == UserRole.INSTRUCTOR

    @property
    def is_recruiter(self) -> bool:
        return self.role == UserRole.RECRUITER

    @property
    def is_admin_user(self) -> bool:
        return self.role == UserRole.ADMIN

    def get_full_name(self) -> str:
        return self.full_name.strip()

    def get_short_name(self) -> str:
        return self.full_name.split()[0] if self.full_name else self.email

    def generate_username(self) -> str:
        import re
        base = re.sub(r"[^a-z0-9]+", "-", self.full_name.lower()).strip("-")
        base = base[:40] or "user"
        username = base
        counter = 1
        while User.objects.filter(username=username).exclude(pk=self.pk).exists():
            username = f"{base}-{counter}"
            counter += 1
        return username


class OAuthAccount(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="oauth_accounts")
    provider = models.CharField(max_length=50)
    provider_uid = models.CharField(max_length=255)
    access_token = models.TextField(blank=True, default="")
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "oauth_accounts"
        unique_together = [("provider", "provider_uid")]
        indexes = [
            models.Index(fields=["provider", "provider_uid"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_uid} -> {self.user.email}"


class UserPrivacySettings(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="privacy_settings")
    public_profile = models.BooleanField(default=True, db_index=True)
    recruiter_resume_visibility = models.BooleanField(default=True)
    recruiter_portfolio_visibility = models.BooleanField(default=True)
    open_to_work = models.BooleanField(default=False, db_index=True)
    allow_recruiter_contact = models.BooleanField(default=True)
    allow_analytics = models.BooleanField(default=True)
    allow_ai_analysis = models.BooleanField(default=True)

    class Meta:
        db_table = "user_privacy_settings"
        indexes = [
            models.Index(fields=["public_profile", "open_to_work"], name="user_privacy_public_work_idx"),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.user.is_public_profile != self.public_profile:
            self.user.is_public_profile = self.public_profile
            self.user.save(update_fields=["is_public_profile", "updated_at"])
