from django.conf import settings
from django.db import models
from common.models import BaseModel


# ── Shared enums ──────────────────────────────────────────────────────────────

class VerificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under Review"
    VERIFIED = "verified", "Verified"
    REJECTED = "rejected", "Rejected"
    SUSPENDED = "suspended", "Suspended"
    MORE_INFO_REQUIRED = "more_info_required", "More Information Required"


class VerificationLevel(models.TextChoices):
    BASIC = "basic", "Basic"
    VERIFIED = "verified", "Verified"
    ENTERPRISE = "enterprise", "Enterprise"
    PARTNER = "partner", "Partner"


class OrganizationType(models.TextChoices):
    COMPANY = "company", "Company"
    UNIVERSITY = "university", "University"
    TRAINING_CENTER = "training_center", "Training Center"
    GOVERNMENT = "government", "Government"
    NGO = "ngo", "NGO"
    STARTUP = "startup", "Startup"
    RESEARCH_INSTITUTE = "research_institute", "Research Institute"
    OTHER = "other", "Other"


class OrganizationSize(models.TextChoices):
    MICRO = "1-10", "1-10 employees"
    SMALL = "11-50", "11-50 employees"
    MEDIUM = "51-200", "51-200 employees"
    LARGE = "201-500", "201-500 employees"
    ENTERPRISE = "500+", "500+ employees"


class ProfileVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    RECRUITERS_ONLY = "visible_to_recruiters", "Visible to Recruiters"
    PUBLIC = "public", "Public"


class Availability(models.TextChoices):
    NOT_SPECIFIED = "not_specified", "Not Specified"
    FULL_TIME = "full_time", "Full Time"
    PART_TIME = "part_time", "Part Time"
    INTERNSHIP = "internship", "Internship"
    FREELANCE = "freelance", "Freelance"
    REMOTE_ONLY = "remote_only", "Remote Only"


class WorkMode(models.TextChoices):
    REMOTE = "remote", "Remote"
    HYBRID = "hybrid", "Hybrid"
    ONSITE = "onsite", "On-site"
    FLEXIBLE = "flexible", "Flexible"


class TeachingDemoSource(models.TextChoices):
    UPLOAD = "upload", "Direct Upload"
    YOUTUBE = "youtube", "Private YouTube"
    VIMEO = "vimeo", "Private Vimeo"


# ── Organization ──────────────────────────────────────────────────────────────

class Organization(BaseModel):
    # Generic organization model covering companies, universities,
    # training centers, governments, NGOs, and research institutes.
    # Recruiters always belong to an organization.
    # Organizations own jobs, verification, and trust scores.

    organization_type = models.CharField(
        max_length=30,
        choices=OrganizationType.choices,
        default=OrganizationType.COMPANY,
        db_index=True,
    )
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)
    logo_url = models.URLField(max_length=500, blank=True, default="")
    website_url = models.URLField(max_length=500, blank=True, default="")
    official_email = models.EmailField(blank=True, default="")
    registration_number = models.CharField(max_length=100, blank=True, default="")
    country_code = models.CharField(max_length=2, blank=True, default="", db_index=True)
    city = models.CharField(max_length=100, blank=True, default="")
    industry = models.CharField(max_length=100, blank=True, default="")
    organization_size = models.CharField(
        max_length=20,
        choices=OrganizationSize.choices,
        blank=True,
        default="",
    )
    description = models.TextField(blank=True, default="")

    # Social links
    linkedin_url = models.URLField(max_length=500, blank=True, default="")
    facebook_url = models.URLField(max_length=500, blank=True, default="")
    x_url = models.URLField(max_length=500, blank=True, default="")
    youtube_url = models.URLField(max_length=500, blank=True, default="")

    # Verification
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verification_level = models.CharField(
        max_length=20,
        choices=VerificationLevel.choices,
        default=VerificationLevel.BASIC,
        db_index=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizations_verified",
    )
    verified_until = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    suspension_reason = models.TextField(blank=True, default="")

    # Trust score managed only by backend trust service
    trust_score = models.SmallIntegerField(default=0)
    trust_score_updated_at = models.DateTimeField(null=True, blank=True)
    trust_score_reason_summary = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="organizations_created",
    )

    class Meta:
        db_table = "organizations"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization_type", "verification_status"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["verification_level"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization_type})"

    @property
    def is_verified(self):
        return self.verification_status == VerificationStatus.VERIFIED

    @property
    def can_post_jobs(self):
        return self.verification_status in (
            VerificationStatus.VERIFIED,
        ) and self.is_active


class OrganizationOffice(BaseModel):
    # Physical offices for organizations that operate in multiple locations.
    # Future departments will link to offices, not directly to the organization.

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="offices",
    )
    name = models.CharField(max_length=200, help_text="e.g. Conakry HQ, Dakar Office")
    country_code = models.CharField(max_length=2, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    address = models.TextField(blank=True, default="")
    timezone = models.CharField(max_length=50, blank=True, default="")
    is_headquarters = models.BooleanField(default=False)
    is_hiring = models.BooleanField(default=True)
    phone = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        db_table = "organization_offices"
        ordering = ["-is_headquarters", "name"]
        indexes = [
            models.Index(fields=["organization", "is_headquarters"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


# ── Instructor Profile ────────────────────────────────────────────────────────

class InstructorProfile(BaseModel):
    # Extended profile for users with role = instructor.
    # Holds all teaching-specific fields not present on the base User model.
    # verification_status controls whether the instructor can publish paid courses.

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )
    professional_title = models.CharField(max_length=200, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    country_code = models.CharField(max_length=2, blank=True, default="", db_index=True)
    city = models.CharField(max_length=100, blank=True, default="")

    # Language separation: a person may speak several but teach in fewer
    languages_spoken = models.JSONField(
        default=list,
        help_text="BCP 47 codes of languages the instructor speaks.",
    )
    teaching_languages = models.JSONField(
        default=list,
        help_text="BCP 47 codes of languages the instructor teaches in.",
    )

    skills = models.JSONField(default=list, help_text="List of skill names.")
    education = models.JSONField(default=list, help_text="Same structure as Resume.education.")
    work_experience = models.JSONField(default=list, help_text="Same structure as Resume.experience.")

    # Teaching history including pre-platform experience
    years_of_teaching = models.PositiveSmallIntegerField(default=0)
    total_students_taught = models.PositiveIntegerField(default=0)
    total_courses_created = models.PositiveSmallIntegerField(default=0)

    linkedin_url = models.URLField(max_length=500, blank=True, default="")
    portfolio_url = models.URLField(max_length=500, blank=True, default="")

    # Teaching categories stored as slugs for future-proof references
    teaching_category_slugs = models.JSONField(
        default=list,
        help_text="List of category slugs. e.g. ['web-development', 'data-science']",
    )

    # Platform-computed stats
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_ratings = models.PositiveIntegerField(default=0)
    student_count = models.PositiveIntegerField(default=0)
    courses_published = models.PositiveSmallIntegerField(default=0)

    # Teaching demo - private until instructor explicitly publishes it
    teaching_demo_s3_key = models.CharField(max_length=500, blank=True, default="")
    teaching_demo_source = models.CharField(
        max_length=20,
        choices=TeachingDemoSource.choices,
        blank=True,
        default="",
    )
    teaching_demo_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Private YouTube or Vimeo URL if not a direct upload.",
    )
    teaching_demo_is_public = models.BooleanField(default=False)

    # Verification
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instructors_verified",
    )
    verified_until = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    suspension_reason = models.TextField(blank=True, default="")

    # Trust score managed only by backend trust service
    trust_score = models.SmallIntegerField(default=0)
    trust_score_updated_at = models.DateTimeField(null=True, blank=True)
    trust_score_reason_summary = models.TextField(blank=True, default="")

    class Meta:
        db_table = "instructor_profiles"
        indexes = [
            models.Index(fields=["verification_status"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return f"InstructorProfile({self.user.email})"

    @property
    def can_publish_paid_courses(self):
        return self.verification_status == VerificationStatus.VERIFIED


# ── Recruiter Profile ─────────────────────────────────────────────────────────

class RecruiterProfile(BaseModel):
    # Extended profile for users with role = recruiter.
    # Every recruiter belongs to an Organization.
    # Posting jobs requires both recruiter and organization verification.

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter_profile",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="recruiters",
    )
    job_title = models.CharField(max_length=200, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    linkedin_url = models.URLField(max_length=500, blank=True, default="")

    # Organization admin can manage all company recruiters and jobs
    is_company_admin = models.BooleanField(default=False)

    # Explicit permission flags derived from verification but decoupled
    # for simpler authorization checks
    can_post_jobs = models.BooleanField(default=False, db_index=True)
    can_contact_students = models.BooleanField(default=False)

    # Verification
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recruiters_verified",
    )
    verified_until = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    suspension_reason = models.TextField(blank=True, default="")

    # Trust score managed only by backend trust service
    trust_score = models.SmallIntegerField(default=0)
    trust_score_updated_at = models.DateTimeField(null=True, blank=True)
    trust_score_reason_summary = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "recruiter_profiles"
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["verification_status"]),
            models.Index(fields=["can_post_jobs"]),
        ]

    def __str__(self):
        return f"RecruiterProfile({self.user.email} @ {self.organization.name})"


# ── Learner Profile ───────────────────────────────────────────────────────────

class LearnerProfile(BaseModel):
    # Extended profile for students and learners.
    # Holds career preferences and availability for recruiter search.
    # Visibility controls who can see this profile.

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learner_profile",
    )
    bio = models.TextField(blank=True, default="")
    country_code = models.CharField(max_length=2, blank=True, default="GN", db_index=True)
    city = models.CharField(max_length=100, blank=True, default="")

    languages_spoken = models.JSONField(
        default=list,
        help_text="BCP 47 language codes the learner speaks.",
    )
    skills = models.JSONField(default=list)
    education = models.JSONField(default=list)
    work_experience = models.JSONField(default=list)

    # Profile visibility
    profile_visibility = models.CharField(
        max_length=30,
        choices=ProfileVisibility.choices,
        default=ProfileVisibility.PRIVATE,
        db_index=True,
    )

    # Job availability and preferences
    availability = models.CharField(
        max_length=20,
        choices=Availability.choices,
        default=Availability.NOT_SPECIFIED,
        db_index=True,
    )
    open_to_work = models.BooleanField(default=False, db_index=True)
    available_from = models.DateField(null=True, blank=True)
    preferred_work_mode = models.CharField(
        max_length=20,
        choices=WorkMode.choices,
        default=WorkMode.FLEXIBLE,
        db_index=True,
    )
    salary_expectation = models.JSONField(
        default=dict,
        help_text="e.g. {'min': 500000, 'max': 1000000, 'currency': 'GNF', 'period': 'monthly'}",
    )
    job_preferences = models.JSONField(
        default=dict,
        help_text="e.g. {'preferred_job_types': ['full_time'], 'preferred_locations': ['GN', 'remote']}",
    )

    # Trust score managed only by backend trust service
    trust_score = models.SmallIntegerField(default=0)
    trust_score_updated_at = models.DateTimeField(null=True, blank=True)
    trust_score_reason_summary = models.TextField(blank=True, default="")

    class Meta:
        db_table = "learner_profiles"
        indexes = [
            models.Index(fields=["profile_visibility", "open_to_work"]),
            models.Index(fields=["availability"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["preferred_work_mode"]),
        ]

    def __str__(self):
        return f"LearnerProfile({self.user.email})"
