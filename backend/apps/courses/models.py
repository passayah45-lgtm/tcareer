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
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lessons"
        indexes = [
            models.Index(fields=["course", "position"]),
            models.Index(fields=["course", "is_published"]),
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
