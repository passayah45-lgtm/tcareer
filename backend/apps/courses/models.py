"""
Course models for T-Career LMS.

Database design decisions:

1. UUID primary keys on all tables - prevents enumeration attacks on course,
   enrollment, and progress endpoints exposed to the public.

2. Soft deletes via deleted_at - courses deleted by an instructor remain
   accessible to enrolled students until their enrollment ends.

3. Course slug - used in URLs for SEO. Unique constraint at DB level.

4. Lesson position - integer for manual ordering. Gaps allowed (10, 20, 30)
   so instructors can insert lessons without reordering every record.

5. VideoLesson separated from Lesson - video metadata lives in its own table.
   Not every lesson is a video. Avoids null columns on text/quiz lessons.

6. Enrollment amount_paid - stored at enrollment time so price changes
   do not affect historical records.

7. LessonProgress watch_percentage - 0-100 integer. More useful than raw
   seconds for completion logic and UI progress bars.

Table relationships:
    User 1--* Course (instructor)
    Course 1--* Lesson
    Course 1--* Enrollment
    User 1--* Enrollment
    Enrollment 1--* LessonProgress
    Lesson 1--1 VideoLesson (optional)
    Lesson 1--* LessonProgress
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from common.models import BaseModel


class CourseLevel(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class CourseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class ContentReviewStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    NEEDS_REVIEW = "needs_review", "Needs Review"
    UNDER_REVIEW = "under_review", "Under Review"
    CHANGES_REQUESTED = "changes_requested", "Changes Requested"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class ReviewerRole(models.TextChoices):
    PLATFORM_ACADEMIC_REVIEWER = "platform_academic_reviewer", "Platform Academic Reviewer"
    ORGANIZATION_ACADEMIC_REVIEWER = (
        "organization_academic_reviewer",
        "Organization Academic Reviewer",
    )
    COURSE_REVIEWER = "course_reviewer", "Course Reviewer"
    SUBJECT_REVIEWER = "subject_reviewer", "Subject Reviewer"
    LEAD_REVIEWER = "lead_reviewer", "Lead Reviewer"


class MalwareScanStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SCANNING = "scanning", "Scanning"
    CLEAN = "clean", "Clean"
    INFECTED = "infected", "Infected"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class AcademicOverrideReason(models.TextChoices):
    REASSIGNMENT = "reassignment", "Reviewer reassignment"
    EMERGENCY_ROLLBACK = "emergency_publication_rollback", "Emergency publication rollback"
    REVIEWER_ABSENCE = "reviewer_absence", "Reviewer absence"
    STUCK_STATE = "incorrect_stuck_state", "Incorrect stuck state"
    SECURITY_ISSUE = "security_issue", "Security issue"
    LEGAL_ISSUE = "legal_issue", "Legal issue"


class ReviewTargetType(models.TextChoices):
    COURSE = "course", "Course"
    LESSON = "lesson", "Lesson"
    ASSESSMENT = "assessment", "Assessment"
    PROJECT = "project", "Final Project"
    RESOURCE = "resource", "Resource"


class ReviewPriority(models.TextChoices):
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class ReviewDecision(models.TextChoices):
    APPROVE = "approve", "Approve"
    APPROVE_MINOR_EDITS = "approve_minor_edits", "Approve With Minor Edits"
    REQUEST_CHANGES = "request_changes", "Request Changes"
    REJECT = "reject", "Reject"
    ESCALATE = "escalate", "Escalate"


class LessonType(models.TextChoices):
    VIDEO = "video", "Video"
    TEXT = "text", "Text"
    QUIZ = "quiz", "Quiz"


class TranscodingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETE = "complete", "Complete"
    FAILED = "failed", "Failed"


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    REFUNDED = "refunded", "Refunded"
    EXPIRED = "expired", "Expired"


class AcademicReviewerProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_reviewer_profile",
    )
    reviewer_role = models.CharField(
        max_length=60,
        choices=ReviewerRole.choices,
        default=ReviewerRole.COURSE_REVIEWER,
        db_index=True,
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="academic_reviewers",
    )
    subject_tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    max_active_assignments = models.PositiveSmallIntegerField(default=25)
    automatic_assignment_enabled = models.BooleanField(default=False)

    class Meta:
        db_table = "academic_reviewer_profiles"
        indexes = [
            models.Index(fields=["reviewer_role", "is_active"]),
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} ({self.reviewer_role})"


class Course(BaseModel):
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses_taught",
        db_index=True,
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, db_index=True)
    short_description = models.CharField(max_length=500, blank=True, default="")
    description = models.TextField(blank=True, default="")
    thumbnail_url = models.URLField(max_length=500, blank=True, default="")
    preview_video_url = models.URLField(max_length=500, blank=True, default="")
    level = models.CharField(
        max_length=20,
        choices=CourseLevel.choices,
        default=CourseLevel.BEGINNER,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
        db_index=True,
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    language = models.CharField(max_length=10, default="en")
    tags = models.JSONField(default=list, blank=True)
    requirements = models.JSONField(default=list, blank=True)
    what_you_learn = models.JSONField(default=list, blank=True)
    pass_threshold = models.PositiveIntegerField(default=70)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "courses"
        indexes = [
            models.Index(fields=["status", "deleted_at"]),
            models.Index(fields=["instructor", "status"]),
            models.Index(fields=["level", "status"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.price == 0

    @property
    def is_published(self):
        return self.status == CourseStatus.PUBLISHED and self.deleted_at is None

    @property
    def total_lessons(self):
        return self.lessons.filter(is_published=True, deleted_at=None).count()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Lesson(BaseModel):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        db_index=True,
    )
    title = models.CharField(max_length=255)
    lesson_type = models.CharField(
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.VIDEO,
        db_index=True,
    )
    content = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    is_free_preview = models.BooleanField(default=False)
    review_status = models.CharField(
        max_length=30,
        choices=ContentReviewStatus.choices,
        default=ContentReviewStatus.DRAFT,
        db_index=True,
    )
    published_version = models.PositiveIntegerField(default=0)
    draft_version = models.PositiveIntegerField(default=1)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lessons"
        indexes = [
            models.Index(fields=["course", "position"]),
            models.Index(fields=["course", "is_published"]),
            models.Index(fields=["course", "review_status"], name="lesson_course_review_idx"),
        ]
        ordering = ["position"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class VideoLesson(BaseModel):
    """
    Video metadata for VIDEO type lessons.

    Upload flow:
    1. Instructor requests presigned S3 URL via POST /upload-url/
    2. Frontend uploads directly to S3 using that URL
    3. Celery task triggers MediaConvert job
    4. MediaConvert outputs HLS to S3 and calls completion webhook
    5. Django updates hls_url and transcoding_status to COMPLETE
    """

    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name="video",
    )
    original_s3_key = models.CharField(max_length=500, blank=True, default="")
    hls_s3_key = models.CharField(max_length=500, blank=True, default="")
    hls_url = models.URLField(max_length=500, blank=True, default="")
    thumbnail_s3_key = models.CharField(max_length=500, blank=True, default="")
    thumbnail_url = models.URLField(max_length=500, blank=True, default="")
    duration_seconds = models.PositiveIntegerField(default=0)
    transcoding_status = models.CharField(
        max_length=20,
        choices=TranscodingStatus.choices,
        default=TranscodingStatus.PENDING,
        db_index=True,
    )
    mediaconvert_job_id = models.CharField(max_length=255, blank=True, default="")
    file_size_bytes = models.BigIntegerField(default=0)

    class Meta:
        db_table = "video_lessons"
        indexes = [
            models.Index(fields=["transcoding_status"]),
        ]

    def __str__(self):
        return f"Video: {self.lesson.title} ({self.transcoding_status})"


class Enrollment(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="enrollments",
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        db_index=True,
    )
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "enrollments"
        unique_together = [("user", "course")]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.course.title}"

    @property
    def is_active(self):
        return self.status == EnrollmentStatus.ACTIVE

    @property
    def is_completed(self):
        return self.status == EnrollmentStatus.COMPLETED


class LessonProgress(BaseModel):
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
        db_index=True,
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="progress_records",
        db_index=True,
    )
    is_completed = models.BooleanField(default=False, db_index=True)
    watch_percentage = models.PositiveSmallIntegerField(default=0)
    last_position_seconds = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lesson_progress"
        unique_together = [("enrollment", "lesson")]
        indexes = [
            models.Index(fields=["enrollment", "is_completed"]),
        ]

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.lesson.title} ({self.watch_percentage}%)"


class CourseReview(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="academic_reviews")
    status = models.CharField(
        max_length=30,
        choices=ContentReviewStatus.choices,
        default=ContentReviewStatus.DRAFT,
        db_index=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academic_course_reviews_completed",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academic_course_reviews_submitted",
    )
    comments = models.TextField(blank=True, default="")
    required_fixes = models.JSONField(default=list, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "course_academic_reviews"
        indexes = [models.Index(fields=["course", "status"], name="course_academic_review_idx")]
        ordering = ["-created_at"]


class ReviewAssignment(BaseModel):
    target_type = models.CharField(
        max_length=30,
        choices=ReviewTargetType.choices,
        db_index=True,
    )
    target_id = models.UUIDField(db_index=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_assignments",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_assignments",
    )
    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="academic_review_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academic_review_assignments_created",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academic_review_assignments",
    )
    subject = models.CharField(max_length=120, blank=True, default="", db_index=True)
    priority = models.CharField(
        max_length=20,
        choices=ReviewPriority.choices,
        default=ReviewPriority.NORMAL,
        db_index=True,
    )
    review_status = models.CharField(
        max_length=30,
        choices=ContentReviewStatus.choices,
        default=ContentReviewStatus.NEEDS_REVIEW,
        db_index=True,
    )
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    reassignment_history = models.JSONField(default=list, blank=True)
    escalation_level = models.PositiveSmallIntegerField(default=0)
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academic_review_escalations",
    )
    escalation_reason = models.TextField(blank=True, default="")
    escalated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "academic_review_assignments"
        indexes = [
            models.Index(fields=["assigned_reviewer", "review_status"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["course", "review_status"]),
            models.Index(fields=["priority", "due_date"]),
        ]
        ordering = ["due_date", "-created_at"]

    def __str__(self):
        return f"{self.target_type}:{self.target_id} -> {self.assigned_reviewer.email}"

    @property
    def is_overdue(self):
        return bool(
            self.due_date
            and not self.completed_at
            and self.due_date < timezone.now()
            and self.review_status
            not in {ContentReviewStatus.APPROVED, ContentReviewStatus.REJECTED}
        )


class LessonStructuredReview(BaseModel):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="structured_reviews",
    )
    assignment = models.ForeignKey(
        ReviewAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lesson_reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lesson_structured_reviews",
    )
    decision = models.CharField(
        max_length=40,
        choices=ReviewDecision.choices,
        db_index=True,
    )
    section_comments = models.JSONField(default=dict, blank=True)
    required_changes = models.JSONField(default=list, blank=True)
    instructor_response = models.TextField(blank=True, default="")
    addressed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lesson_structured_reviews"
        indexes = [
            models.Index(fields=["lesson", "decision"]),
            models.Index(fields=["reviewer", "created_at"]),
        ]
        ordering = ["-created_at"]


class LessonVersion(BaseModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lesson_versions_edited",
    )
    title = models.CharField(max_length=255)
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices)
    content = models.TextField(blank=True, default="")
    summary_of_changes = models.CharField(max_length=500, blank=True, default="")
    is_published_version = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "lesson_versions"
        unique_together = [("lesson", "version_number")]
        indexes = [models.Index(fields=["lesson", "version_number"])]
        ordering = ["-version_number"]


class CourseProject(BaseModel):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="project")
    instructions = models.TextField(blank=True, default="")
    required_deliverables = models.JSONField(default=list, blank=True)
    rubric = models.JSONField(default=list, blank=True)
    evaluation_criteria = models.JSONField(default=list, blank=True)
    passing_score = models.PositiveSmallIntegerField(default=70)
    reviewer_notes = models.TextField(blank=True, default="")
    example_solution = models.TextField(blank=True, default="")
    resources = models.JSONField(default=list, blank=True)
    version = models.PositiveIntegerField(default=1)
    approval_state = models.CharField(
        max_length=30,
        choices=ContentReviewStatus.choices,
        default=ContentReviewStatus.DRAFT,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "course_projects"
        indexes = [models.Index(fields=["approval_state"])]


class CourseProjectReviewDecision(BaseModel):
    project = models.ForeignKey(
        CourseProject,
        on_delete=models.CASCADE,
        related_name="review_decisions",
    )
    assignment = models.ForeignKey(
        ReviewAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="course_project_review_decisions",
    )
    decision = models.CharField(max_length=40, choices=ReviewDecision.choices, db_index=True)
    project_version = models.PositiveIntegerField(default=1)
    review_sections = models.JSONField(default=dict, blank=True)
    required_changes = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "course_project_review_decisions"
        indexes = [
            models.Index(fields=["project", "project_version"]),
            models.Index(fields=["reviewer", "created_at"]),
        ]
        ordering = ["-created_at"]


class ResourceType(models.TextChoices):
    CSV = "csv", "CSV Dataset"
    EXCEL = "excel", "Excel Workbook"
    IMAGE = "image", "Image"
    PDF = "pdf", "PDF"
    POWERPOINT = "powerpoint", "PowerPoint"
    DOCX = "docx", "Word Document"
    NOTEBOOK = "notebook", "Python Notebook"
    SQL = "sql", "SQL Script"
    TXT = "txt", "Text"
    ZIP = "zip", "ZIP Archive"
    TEMPLATE = "template", "Template"
    OTHER = "other", "Other"


class ResourceVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    COURSE = "course", "Course"
    PUBLIC = "public", "Public"


class ResourceLibraryItem(BaseModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="course_resources",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
    )
    title = models.CharField(max_length=255)
    resource_type = models.CharField(
        max_length=30,
        choices=ResourceType.choices,
        default=ResourceType.OTHER,
        db_index=True,
    )
    file_url = models.URLField(max_length=1000, blank=True, default="")
    storage_key = models.CharField(max_length=1000, blank=True, default="")
    file_name = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=120, blank=True, default="")
    file_size_bytes = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=128, blank=True, default="", db_index=True)
    description = models.TextField(blank=True, default="")
    version = models.PositiveIntegerField(default=1)
    visibility = models.CharField(
        max_length=20,
        choices=ResourceVisibility.choices,
        default=ResourceVisibility.PRIVATE,
        db_index=True,
    )
    review_status = models.CharField(
        max_length=30,
        choices=ContentReviewStatus.choices,
        default=ContentReviewStatus.DRAFT,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_course_resources",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default="")
    download_count = models.PositiveIntegerField(default=0)
    malware_scan_status = models.CharField(max_length=40, blank=True, default="pending")
    malware_scanner = models.CharField(max_length=40, blank=True, default="")
    malware_scanned_at = models.DateTimeField(null=True, blank=True)
    malware_scan_result = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "resource_library_items"
        indexes = [
            models.Index(fields=["owner", "resource_type"]),
            models.Index(fields=["course", "visibility"]),
            models.Index(fields=["course", "review_status"]),
            models.Index(fields=["checksum"]),
            models.Index(fields=["malware_scan_status"]),
        ]


class AcademicOverrideLog(BaseModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="academic_overrides",
    )
    target_type = models.CharField(max_length=60, db_index=True)
    target_id = models.UUIDField(db_index=True)
    reason_code = models.CharField(
        max_length=60,
        choices=AcademicOverrideReason.choices,
        db_index=True,
    )
    reason = models.TextField()
    previous_state = models.JSONField(default=dict, blank=True)
    new_state = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "academic_override_logs"
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["reason_code", "created_at"]),
        ]
        ordering = ["-created_at"]
