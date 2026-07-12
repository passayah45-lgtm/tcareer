"""
Career Track models for T-Career.

Design decisions:

1. CareerTrack is independent of Course ordering.
   TrackCourse is the join table with position and stage.
   This lets us reuse courses across multiple tracks without duplication.

2. stages are integers (1, 2, 3) mapping to Foundation, Core Skills, Advanced.
   Easy to extend to stage 4 without migration.

3. UserTrackEnrollment is separate from course Enrollment.
   A student can take courses without being in a track.
   Enrolling in a track is an explicit intent declaration.

4. skills_acquired and target_job_titles stored as JSON arrays.
   At MVP there is no need to normalize these.
   Extracted into proper tables when search by skill is needed.

5. estimated_duration_weeks is stored as a range (min/max).
   This is more honest than a single number since pace varies.
"""

from django.conf import settings
from django.db import models
from common.models import BaseModel


class TrackCategory(models.TextChoices):
    TECH = "tech", "Tech and Engineering"
    DATA_AI = "data_ai", "Data and AI"
    DESIGN = "design", "Design and Product"
    BUSINESS = "business", "Business and Marketing"


class TrackDifficulty(models.TextChoices):
    BEGINNER = "beginner", "Beginner Friendly"
    INTERMEDIATE = "intermediate", "Some Experience Needed"
    ADVANCED = "advanced", "Advanced"


class CareerTrack(BaseModel):
    """
    Defines a career track such as Backend Developer or Data Analyst.
    Each track is a curated sequence of courses leading to a target role.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=TrackCategory.choices,
        default=TrackCategory.TECH,
        db_index=True,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=TrackDifficulty.choices,
        default=TrackDifficulty.BEGINNER,
    )
    icon = models.CharField(
        max_length=50,
        default="code",
        help_text="Icon identifier used in the frontend.",
    )
    color = models.CharField(
        max_length=20,
        default="#4f46e5",
        help_text="Hex color for the track card.",
    )
    target_job_titles = models.JSONField(
        default=list,
        help_text="List of job titles this track prepares students for.",
    )
    skills_acquired = models.JSONField(
        default=list,
        help_text="List of skills students gain by completing this track.",
    )
    estimated_weeks_min = models.PositiveSmallIntegerField(
        default=16,
        help_text="Minimum estimated weeks to complete at 10 hours per week.",
    )
    estimated_weeks_max = models.PositiveSmallIntegerField(
        default=24,
        help_text="Maximum estimated weeks to complete at 10 hours per week.",
    )
    avg_salary_min = models.PositiveIntegerField(
        default=0,
        help_text="Minimum average entry salary in USD.",
    )
    avg_salary_max = models.PositiveIntegerField(
        default=0,
        help_text="Maximum average entry salary in USD.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    position = models.PositiveSmallIntegerField(
        default=0,
        db_index=True,
        help_text="Display order on the tracks page.",
    )

    class Meta:
        db_table = "career_tracks"
        ordering = ["position", "title"]

    def __str__(self):
        return self.title

    @property
    def total_courses(self):
        return self.track_courses.count()

    @property
    def required_courses_count(self):
        return self.track_courses.filter(is_required=True).count()

    @property
    def duration_display(self):
        min_months = round(self.estimated_weeks_min / 4)
        max_months = round(self.estimated_weeks_max / 4)
        if min_months == max_months:
            return f"{min_months} months"
        return f"{min_months} to {max_months} months"


class TrackStage(models.IntegerChoices):
    FOUNDATION = 1, "Foundation"
    CORE = 2, "Core Skills"
    ADVANCED = 3, "Advanced"


class TrackCourse(BaseModel):
    """
    Join table between CareerTrack and Course.
    Defines the sequence and stage of each course within a track.
    """

    track = models.ForeignKey(
        CareerTrack,
        on_delete=models.CASCADE,
        related_name="track_courses",
        db_index=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="track_memberships",
        db_index=True,
    )
    position = models.PositiveSmallIntegerField(
        default=0,
        help_text="Order within the track. Lower numbers come first.",
    )
    stage = models.IntegerField(
        choices=TrackStage.choices,
        default=TrackStage.FOUNDATION,
        help_text="1=Foundation, 2=Core Skills, 3=Advanced",
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Required courses must be completed. Optional courses are recommended.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Guidance shown to the student about this course in the context of the track.",
    )

    class Meta:
        db_table = "track_courses"
        unique_together = [("track", "course")]
        ordering = ["position"]
        indexes = [
            models.Index(fields=["track", "stage", "position"]),
        ]

    def __str__(self):
        return f"{self.track.title} - Stage {self.stage}: {self.course.title}"


class UserTrackEnrollment(BaseModel):
    """
    Records a student's enrollment in a career track.
    Separate from course enrollment - this is intent-level tracking.
    One student can be enrolled in at most one active track at a time.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="track_enrollments",
        db_index=True,
    )
    track = models.ForeignKey(
        CareerTrack,
        on_delete=models.CASCADE,
        related_name="enrollments",
        db_index=True,
    )
    current_stage = models.IntegerField(
        choices=TrackStage.choices,
        default=TrackStage.FOUNDATION,
    )
    courses_completed = models.PositiveSmallIntegerField(default=0)
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_track_enrollments"
        unique_together = [("user", "track")]
        indexes = [
            models.Index(fields=["user", "is_completed"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.track.title}"

    @property
    def progress_percentage(self):
        total = self.track.required_courses_count
        if total == 0:
            return 0
        return min(100, round((self.courses_completed / total) * 100))

    @property
    def next_course(self):
        """Returns the next incomplete required course in the track."""
        from apps.courses.models import Enrollment
        completed_course_ids = Enrollment.objects.filter(
            user=self.user,
            status__in=["active", "completed"],
        ).values_list("course_id", flat=True)

        return TrackCourse.objects.filter(
            track=self.track,
            is_required=True,
        ).exclude(
            course_id__in=completed_course_ids,
        ).order_by("position").first()
