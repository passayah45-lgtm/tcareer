import uuid

from django.conf import settings
from django.db import models
from common.models import BaseModel


def resume_file_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"private/resumes/{instance.resume.user_id}/{uuid.uuid4().hex}.{ext}"


def portfolio_media_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"portfolio/projects/{instance.project_id}/{uuid.uuid4().hex}.{ext}"


class VisibilityChoice(models.TextChoices):
    PUBLIC = "public", "Public"
    UNLISTED = "unlisted", "Unlisted"
    PRIVATE = "private", "Private"


class ExperienceLevel(models.TextChoices):
    STUDENT = "student", "Student"
    ENTRY = "entry", "Entry Level (0-2 years)"
    MID = "mid", "Mid Level (2-5 years)"
    SENIOR = "senior", "Senior (5+ years)"
    LEAD = "lead", "Lead / Manager"


class SkillSource(models.TextChoices):
    MANUAL = "manual", "Added manually"
    TRACK = "track", "Imported from career track"
    COURSE = "course", "Imported from completed course"


class RelocationWillingness(models.TextChoices):
    NO = "no", "Not willing to relocate"
    LOCAL = "local", "Local only"
    NATIONAL = "national", "Within country"
    REGIONAL = "regional", "Within region"
    GLOBAL = "global", "Open to relocation globally"


class RemotePreference(models.TextChoices):
    ONSITE = "onsite", "On-site only"
    HYBRID = "hybrid", "Hybrid"
    REMOTE = "remote", "Remote only"
    FLEXIBLE = "flexible", "Flexible"


class Portfolio(BaseModel):
    # One portfolio per user. Created automatically on first access.

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolio",
        db_index=True,
    )

    # Career identity
    headline = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Short professional tagline. e.g. Full-Stack Developer | Python and React",
    )
    bio = models.TextField(blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="")
    desired_role = models.CharField(
        max_length=200,
        blank=True,
        default="",
        db_index=True,
        help_text="Target job title for matching. e.g. Backend Developer",
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.STUDENT,
        db_index=True,
    )

    # Social links
    linkedin_url = models.URLField(max_length=500, blank=True, default="")
    github_url = models.URLField(max_length=500, blank=True, default="")
    website_url = models.URLField(max_length=500, blank=True, default="")

    # Visibility and analytics
    visibility = models.CharField(
        max_length=10,
        choices=VisibilityChoice.choices,
        default=VisibilityChoice.PUBLIC,
        db_index=True,
    )
    profile_views = models.PositiveIntegerField(default=0)

    # Global work preferences added in Global Foundation
    preferred_work_country = models.CharField(
        max_length=2,
        blank=True,
        default="GN",
        help_text="ISO 3166-1 alpha-2 code of preferred work country. e.g. GN, FR, US",
        db_index=True,
    )
    relocation_willingness = models.CharField(
        max_length=20,
        choices=RelocationWillingness.choices,
        default=RelocationWillingness.NO,
        db_index=True,
    )
    remote_preference = models.CharField(
        max_length=20,
        choices=RemotePreference.choices,
        default=RemotePreference.FLEXIBLE,
        db_index=True,
    )

    class Meta:
        db_table = "portfolios"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["visibility", "experience_level"]),
            models.Index(fields=["desired_role"]),
            models.Index(fields=["preferred_work_country"]),
            models.Index(fields=["relocation_willingness"]),
            models.Index(fields=["remote_preference"]),
        ]

    def __str__(self):
        return f"Portfolio({self.user.email})"

    @property
    def public_url(self):
        username = self.user.username
        if not username:
            return None
        from django.conf import settings as django_settings
        return f"{django_settings.FRONTEND_URL}/u/{username}"

    @property
    def is_visible_publicly(self):
        return self.visibility in (VisibilityChoice.PUBLIC, VisibilityChoice.UNLISTED)


class PortfolioSkill(BaseModel):
    # A skill displayed on the student's portfolio.
    # Skills can be added manually or auto-imported from completed courses and tracks.

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="skills",
        db_index=True,
    )
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="e.g. Programming Language, Framework, Tool, Soft Skill",
    )
    source = models.CharField(
        max_length=10,
        choices=SkillSource.choices,
        default=SkillSource.MANUAL,
    )
    source_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the track or course this skill was imported from.",
    )
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "portfolio_skills"
        ordering = ["position", "name"]
        indexes = [
            models.Index(fields=["portfolio"]),
            models.Index(fields=["name"]),
        ]
        unique_together = [("portfolio", "name")]

    def __str__(self):
        return f"{self.name} ({self.portfolio.user.email})"


class PortfolioProject(BaseModel):
    # A project the student has built, shown on their portfolio.

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="projects",
        db_index=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    tech_stack = models.JSONField(
        default=list,
        help_text="List of technologies used. e.g. ['Python', 'Django', 'PostgreSQL']",
    )

    # Links
    project_url = models.URLField(max_length=500, blank=True, default="")
    github_url = models.URLField(max_length=500, blank=True, default="")
    demo_video_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Link to a demo video (YouTube, Loom, or HLS URL).",
    )

    # Media
    thumbnail_url = models.URLField(max_length=500, blank=True, default="")
    gallery_urls = models.JSONField(
        default=list,
        help_text="List of screenshot/image URLs for the project gallery.",
    )

    # Display
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Featured projects appear at the top of the portfolio.",
    )
    position = models.PositiveIntegerField(default=0)

    # Date range
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "portfolio_projects"
        ordering = ["-is_featured", "position"]
        indexes = [
            models.Index(fields=["portfolio"]),
            models.Index(fields=["portfolio", "is_featured"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.portfolio.user.email})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("end_date cannot be before start_date.")
        if len(self.gallery_urls) > 10:
            raise ValidationError("A project can have at most 10 gallery images.")
        if len(self.tech_stack) > 20:
            raise ValidationError("A project can list at most 20 technologies.")


class PortfolioProjectMedia(BaseModel):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        DOCUMENT = "document", "Document"

    project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="media",
        db_index=True,
    )
    media_type = models.CharField(max_length=20, choices=MediaType.choices)
    url = models.URLField(max_length=1000, blank=True, default="")
    file = models.FileField(upload_to=portfolio_media_upload_path, blank=True, default="")
    file_name = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=100, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=120, blank=True, default="")
    description = models.TextField(blank=True, default="")
    visibility = models.CharField(
        max_length=10,
        choices=VisibilityChoice.choices,
        default=VisibilityChoice.PUBLIC,
        db_index=True,
    )
    position = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "portfolio_project_media"
        ordering = ["position", "created_at"]
        indexes = [
            models.Index(fields=["project", "visibility"], name="pf_media_proj_vis_idx"),
        ]


class Resume(BaseModel):
    # Student resume. One per user at MVP.
    # Education and experience stored as JSONB to avoid 4 extra tables
    # for simple ordered lists that are never queried independently.

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resume",
        db_index=True,
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="e.g. Software Engineer Resume or Data Analyst CV",
    )
    summary = models.TextField(
        blank=True,
        default="",
        help_text="Professional summary or objective statement.",
    )
    target_role = models.CharField(
        max_length=200,
        blank=True,
        default="",
        db_index=True,
        help_text="Target job title. Used for AI recommendations.",
    )

    # Structured sections stored as JSONB
    education = models.JSONField(
        default=list,
        help_text="List of education entries.",
    )
    experience = models.JSONField(
        default=list,
        help_text="List of experience entries.",
    )

    # Generated PDF
    pdf_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="S3 URL of the last generated PDF.",
    )
    last_generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "resumes"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["target_role"]),
        ]

    def __str__(self):
        return f"Resume({self.user.email})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if len(self.education) > 10:
            raise ValidationError("A resume can have at most 10 education entries.")
        if len(self.experience) > 15:
            raise ValidationError("A resume can have at most 15 experience entries.")


class CareerResume(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="career_resumes",
        db_index=True,
    )
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, default="")
    target_role = models.CharField(max_length=200, blank=True, default="", db_index=True)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False, db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "career_resumes"
        ordering = ["-is_default", "-updated_at"]
        indexes = [
            models.Index(fields=["user", "is_default"], name="career_resume_user_default_idx"),
            models.Index(fields=["user", "is_archived"], name="career_resume_arch_idx"),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            CareerResume.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)


class ResumeVersion(BaseModel):
    resume = models.ForeignKey(CareerResume, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField(default=1)
    snapshot = models.JSONField(default=dict, blank=True)
    change_summary = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "career_resume_versions"
        unique_together = [("resume", "version_number")]
        ordering = ["-version_number"]


class ResumeFile(BaseModel):
    resume = models.ForeignKey(CareerResume, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=resume_file_upload_path, blank=True, default="")
    file_url = models.URLField(max_length=1000, blank=True, default="")
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)
    is_private = models.BooleanField(default=True, db_index=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="career_resume_files_uploaded",
    )

    class Meta:
        db_table = "career_resume_files"
        ordering = ["-created_at"]


class ResumeAnalytics(BaseModel):
    class EventType(models.TextChoices):
        VIEWED_BY_RECRUITER = "viewed_by_recruiter", "Viewed by Recruiter"
        DOWNLOADED = "downloaded", "Downloaded"
        USED_FOR_APPLICATION = "used_for_application", "Used for Application"

    resume = models.ForeignKey(CareerResume, on_delete=models.CASCADE, related_name="analytics")
    event_type = models.CharField(max_length=40, choices=EventType.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="career_resume_analytics_events",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "career_resume_analytics"
        ordering = ["-created_at"]


class ResumeAIReviewType(models.TextChoices):
    REVIEW = "review", "Resume Review"
    SKILL_EXTRACTION = "skill_extraction", "Skill Extraction"
    ATS = "ats", "ATS Simulation"
    JOB_MATCH = "job_match", "Job Match"
    COMPARISON = "comparison", "Resume Comparison"


class ResumeAIReview(BaseModel):
    resume = models.ForeignKey(CareerResume, on_delete=models.CASCADE, related_name="ai_reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resume_ai_reviews")
    review_type = models.CharField(max_length=30, choices=ResumeAIReviewType.choices, db_index=True)
    job = models.ForeignKey("jobs.JobListing", on_delete=models.SET_NULL, null=True, blank=True, related_name="resume_ai_reviews")
    comparison_resume = models.ForeignKey(
        CareerResume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comparison_ai_reviews",
    )
    ai_request = models.ForeignKey("ai_platform.AIRequest", on_delete=models.SET_NULL, null=True, blank=True, related_name="resume_reviews")
    ai_response = models.ForeignKey("ai_platform.AIResponse", on_delete=models.SET_NULL, null=True, blank=True, related_name="resume_reviews")
    prompt_version = models.CharField(max_length=40, default="resume-intelligence-v1")
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    overall_score = models.PositiveSmallIntegerField(default=0, db_index=True)
    ats_score = models.PositiveSmallIntegerField(default=0)
    match_score = models.PositiveSmallIntegerField(default=0)
    confidence = models.PositiveSmallIntegerField(default=0)
    extracted_skills = models.JSONField(default=dict, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    report = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True, default="")

    class Meta:
        db_table = "career_resume_ai_reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "review_type", "created_at"], name="resume_ai_user_type_idx"),
            models.Index(fields=["resume", "review_type", "created_at"], name="resume_ai_resume_type_idx"),
        ]


class PortfolioAIReviewType(models.TextChoices):
    PORTFOLIO_REVIEW = "portfolio_review", "Portfolio Review"
    PROJECT_REVIEW = "project_review", "Project Review"
    GITHUB_REVIEW = "github_review", "GitHub Review"
    SKILL_EXTRACTION = "skill_extraction", "Skill Extraction"
    JOB_MATCH = "job_match", "Job Match"


class PortfolioAIReview(BaseModel):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="ai_reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolio_ai_reviews")
    review_type = models.CharField(max_length=30, choices=PortfolioAIReviewType.choices, db_index=True)
    project = models.ForeignKey(PortfolioProject, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_reviews")
    job = models.ForeignKey("jobs.JobListing", on_delete=models.SET_NULL, null=True, blank=True, related_name="portfolio_ai_reviews")
    ai_request = models.ForeignKey("ai_platform.AIRequest", on_delete=models.SET_NULL, null=True, blank=True, related_name="portfolio_reviews")
    ai_response = models.ForeignKey("ai_platform.AIResponse", on_delete=models.SET_NULL, null=True, blank=True, related_name="portfolio_reviews")
    prompt_version = models.CharField(max_length=40, default="portfolio-intelligence-v1")
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    overall_score = models.PositiveSmallIntegerField(default=0, db_index=True)
    project_score = models.PositiveSmallIntegerField(default=0)
    github_score = models.PositiveSmallIntegerField(default=0)
    match_score = models.PositiveSmallIntegerField(default=0)
    confidence = models.PositiveSmallIntegerField(default=0)
    extracted_skills = models.JSONField(default=dict, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    technology_stack = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    report = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True, default="")

    class Meta:
        db_table = "portfolio_ai_reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "review_type", "created_at"], name="portfolio_ai_user_type_idx"),
            models.Index(fields=["portfolio", "review_type", "created_at"], name="portfolio_ai_port_type_idx"),
        ]
