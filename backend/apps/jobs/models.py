from django.conf import settings
from django.db import models
from common.models import BaseModel


class JobType(models.TextChoices):
    FULL_TIME = "full_time", "Full Time"
    PART_TIME = "part_time", "Part Time"
    CONTRACT = "contract", "Contract"
    FREELANCE = "freelance", "Freelance"
    INTERNSHIP = "internship", "Internship"
    REMOTE = "remote", "Remote"


class ExperienceLevel(models.TextChoices):
    STUDENT = "student", "Student"
    ENTRY = "entry", "Entry Level"
    MID = "mid", "Mid Level"
    SENIOR = "senior", "Senior Level"
    LEAD = "lead", "Lead / Manager"


class SalaryCurrency(models.TextChoices):
    GNF = "GNF", "Guinean Franc"
    USD = "USD", "US Dollar"
    EUR = "EUR", "Euro"
    GBP = "GBP", "British Pound"
    XOF = "XOF", "CFA Franc BCEAO"
    NGN = "NGN", "Nigerian Naira"
    GHS = "GHS", "Ghanaian Cedi"
    KES = "KES", "Kenyan Shilling"
    INR = "INR", "Indian Rupee"
    CNY = "CNY", "Chinese Yuan"
    BRL = "BRL", "Brazilian Real"


class JobListing(BaseModel):
    # Core fields
    title = models.CharField(max_length=255, db_index=True)
    company_name = models.CharField(max_length=255)
    company_logo_url = models.URLField(blank=True, default="")
    description = models.TextField()
    requirements = models.JSONField(default=list)

    # Classification
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
        db_index=True,
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.ENTRY,
        db_index=True,
    )

    # Location
    location = models.CharField(max_length=255, blank=True, default="")
    country_code = models.CharField(
        max_length=2,
        blank=True,
        default="GN",
        db_index=True,
        help_text="ISO 3166-1 alpha-2 country code. e.g. GN, FR, US",
    )
    city = models.CharField(max_length=100, blank=True, default="")
    is_remote = models.BooleanField(default=False, db_index=True)
    remote_regions = models.JSONField(
        default=list,
        help_text="Regions where remote candidates are accepted. e.g. ['West Africa', 'Europe']",
    )

    # Salary
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(
        max_length=3,
        choices=SalaryCurrency.choices,
        default=SalaryCurrency.GNF,
    )
    salary_visible = models.BooleanField(default=True)

    # Work authorization fields added in Global Foundation
    work_authorization_required = models.BooleanField(
        default=False,
        help_text="Candidates must have work authorization for the job country.",
    )
    visa_required = models.BooleanField(
        default=False,
        help_text="A visa is required to work in this position.",
    )
    visa_sponsorship = models.BooleanField(
        default=False,
        db_index=True,
        help_text="The employer sponsors visas for this position.",
    )
    citizenship_requirement = models.CharField(
        max_length=2,
        blank=True,
        default="",
        help_text="ISO 3166-1 alpha-2 code if citizenship of a specific country is required.",
    )

    # Languages
    languages_required = models.JSONField(
        default=list,
        help_text="BCP 47 language codes required for this job. e.g. ['fr', 'en']",
    )

    # Application
    apply_url = models.URLField(blank=True, default="")

    # Track requirements
    required_track = models.ForeignKey(
        "tracks.CareerTrack",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_listings",
    )

    # Skills
    required_skills = models.JSONField(
        default=list,
        help_text="List of required skill names. e.g. ['Python', 'Django']",
    )
    preferred_skills = models.JSONField(
        default=list,
        help_text="List of preferred but not required skill names.",
    )

    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)

    # Ownership
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_listings",
        db_index=True,
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_listings",
    )

    class Meta:
        db_table = "job_listings"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["country_code"]),
            models.Index(fields=["is_remote"]),
            models.Index(fields=["visa_sponsorship"]),
            models.Index(fields=["is_active", "expires_at"]),
            models.Index(fields=["organization", "is_active"], name="job_listing_organiz_585f46_idx"),
            models.Index(fields=["experience_level", "job_type"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.company_name}"

    @property
    def salary_display(self):
        if not self.salary_min and not self.salary_max:
            return "Competitive"
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,} - {self.salary_max:,}/yr"
        if self.salary_min:
            return f"From {self.salary_currency} {self.salary_min:,}/yr"
        return f"Up to {self.salary_currency} {self.salary_max:,}/yr"


class RecruiterWaitlist(BaseModel):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    company_size = models.CharField(max_length=50, default="1-10")
    roles_hiring_for = models.TextField(blank=True, default="")
    monthly_hires = models.CharField(max_length=20, default="1-2")
    contacted = models.BooleanField(default=False)

    class Meta:
        db_table = "recruiter_waitlist"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} at {self.company_name}"


class SavedJobCollection(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_job_collections",
        db_index=True,
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "saved_job_collections"
        unique_together = [("user", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.user_id})"


class SavedJob(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_jobs",
        db_index=True,
    )
    job = models.ForeignKey(
        JobListing,
        on_delete=models.CASCADE,
        related_name="saved_by_students",
        db_index=True,
    )
    collection = models.ForeignKey(
        SavedJobCollection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="saved_jobs",
    )
    notes = models.TextField(blank=True, default="")
    is_favorite_company = models.BooleanField(default=False)

    class Meta:
        db_table = "student_saved_jobs"
        unique_together = [("user", "job")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "job"], name="student_saved_job_user_job_idx"),
        ]


class RecentlyViewedJob(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recently_viewed_jobs",
        db_index=True,
    )
    job = models.ForeignKey(
        JobListing,
        on_delete=models.CASCADE,
        related_name="recent_views",
        db_index=True,
    )
    viewed_count = models.PositiveIntegerField(default=1)
    last_viewed_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "student_recently_viewed_jobs"
        unique_together = [("user", "job")]
        ordering = ["-last_viewed_at"]


class JobAlert(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_alerts",
        db_index=True,
    )
    name = models.CharField(max_length=120)
    filters = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_matched_count = models.PositiveIntegerField(default=0)
    total_matched_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "student_job_alerts"
        ordering = ["-created_at"]


class ApplicationStage(models.TextChoices):
    DRAFT = "draft", "Draft"
    APPLIED = "applied", "Applied"
    UNDER_REVIEW = "under_review", "Under Review"
    SHORTLISTED = "shortlisted", "Shortlisted"
    ASSESSMENT = "assessment", "Assessment"
    INTERVIEW_SCHEDULED = "interview_scheduled", "Interview Scheduled"
    INTERVIEW_COMPLETED = "interview_completed", "Interview Completed"
    OFFER_SENT = "offer_sent", "Offer Sent"
    OFFER_ACCEPTED = "offer_accepted", "Offer Accepted"
    OFFER_DECLINED = "offer_declined", "Offer Declined"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


class JobApplication(BaseModel):
    job = models.ForeignKey(
        JobListing,
        on_delete=models.CASCADE,
        related_name="applications",
        db_index=True,
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
        db_index=True,
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="job_applications",
        db_index=True,
    )
    stage = models.CharField(
        max_length=30,
        choices=ApplicationStage.choices,
        default=ApplicationStage.APPLIED,
        db_index=True,
    )
    cover_letter = models.TextField(blank=True, default="")
    source = models.CharField(max_length=50, blank=True, default="direct")
    assigned_recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_job_applications",
    )
    hiring_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_job_applications",
    )
    selected_resume = models.ForeignKey(
        "careers.CareerResume",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_applications",
    )
    is_archived = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "job_applications"
        unique_together = [("job", "candidate")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "stage"], name="job_app_org_stage_idx"),
            models.Index(fields=["job", "stage"], name="job_app_job_stage_idx"),
            models.Index(fields=["candidate", "stage"], name="job_app_candidate_stage_idx"),
            models.Index(fields=["organization", "is_archived"], name="job_app_org_archive_idx"),
        ]

    def __str__(self):
        return f"{self.candidate_id} -> {self.job_id} ({self.stage})"


class ApplicationQuestionType(models.TextChoices):
    SHORT_TEXT = "short_text", "Short Text"
    LONG_TEXT = "long_text", "Long Text"
    YES_NO = "yes_no", "Yes/No"
    MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
    NUMBER = "number", "Number"
    URL = "url", "URL"


class JobApplicationQuestion(BaseModel):
    job = models.ForeignKey(
        JobListing,
        on_delete=models.CASCADE,
        related_name="application_questions",
    )
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(
        max_length=30,
        choices=ApplicationQuestionType.choices,
        default=ApplicationQuestionType.SHORT_TEXT,
    )
    is_required = models.BooleanField(default=False)
    choices = models.JSONField(default=list, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "job_application_questions"
        ordering = ["position", "created_at"]
        indexes = [
            models.Index(fields=["job", "is_active"], name="job_question_job_active_idx"),
        ]


class JobApplicationAnswer(BaseModel):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        JobApplicationQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    answer = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "job_application_answers"
        unique_together = [("application", "question")]
        ordering = ["question__position", "created_at"]


class ApplicationTimeline(BaseModel):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="timeline",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_timeline_entries",
    )
    from_stage = models.CharField(max_length=30, blank=True, default="")
    to_stage = models.CharField(max_length=30, blank=True, default="")
    event_type = models.CharField(max_length=50, db_index=True)
    message = models.CharField(max_length=500, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "application_timeline"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["application", "created_at"], name="app_timeline_app_created_idx"),
        ]


class ApplicationNote(BaseModel):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="application_notes",
    )
    body = models.TextField()
    is_internal = models.BooleanField(default=True)

    class Meta:
        db_table = "application_notes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "created_at"], name="app_notes_app_created_idx"),
        ]


class ApplicationAttachment(BaseModel):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="application_attachments",
    )
    file_url = models.URLField(max_length=1000)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, default="")
    is_private = models.BooleanField(default=False)

    class Meta:
        db_table = "application_attachments"
        ordering = ["-created_at"]


class ApplicationActivity(BaseModel):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_activities",
    )
    activity_type = models.CharField(max_length=50, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "application_activities"
        ordering = ["-created_at"]


class TalentPool(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="talent_pools",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="talent_pools_created",
    )

    class Meta:
        db_table = "talent_pools"
        unique_together = [("organization", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.organization_id})"


class SavedCandidate(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="saved_candidates",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_by_recruiters",
    )
    saved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="saved_candidates",
    )
    talent_pool = models.ForeignKey(
        TalentPool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="saved_candidates",
    )
    labels = models.JSONField(default=list, blank=True)
    private_notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "saved_candidates"
        unique_together = [("organization", "candidate")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "candidate"], name="saved_candidate_org_user_idx"),
        ]


class InterviewType(models.TextChoices):
    ONLINE = "online", "Online"
    PHONE = "phone", "Phone"
    ONSITE = "onsite", "Onsite"


class InterviewStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    RESCHEDULED = "rescheduled", "Rescheduled"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No Show"


class Interview(BaseModel):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    interview_type = models.CharField(max_length=20, choices=InterviewType.choices)
    status = models.CharField(
        max_length=20,
        choices=InterviewStatus.choices,
        default=InterviewStatus.SCHEDULED,
        db_index=True,
    )
    scheduled_start = models.DateTimeField(db_index=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    meeting_link = models.URLField(max_length=1000, blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interviews_created",
    )

    class Meta:
        db_table = "interviews"
        ordering = ["scheduled_start"]
        indexes = [
            models.Index(fields=["organization", "scheduled_start"], name="interview_org_start_idx"),
            models.Index(fields=["application", "status"], name="interview_app_status_idx"),
        ]


class InterviewParticipant(BaseModel):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_participations",
    )
    role = models.CharField(max_length=50, default="interviewer")

    class Meta:
        db_table = "interview_participants"
        unique_together = [("interview", "user")]


class InterviewFeedback(BaseModel):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interview_feedback",
    )
    rating = models.PositiveSmallIntegerField(default=0)
    recommendation = models.CharField(max_length=30, blank=True, default="")
    feedback = models.TextField(blank=True, default="")

    class Meta:
        db_table = "interview_feedback"
        unique_together = [("interview", "author")]


class InterviewScorecard(BaseModel):
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="scorecards",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interview_scorecards",
    )
    criteria = models.JSONField(default=dict, blank=True)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recommendation = models.CharField(max_length=30, blank=True, default="")

    class Meta:
        db_table = "interview_scorecards"
        unique_together = [("interview", "author")]
