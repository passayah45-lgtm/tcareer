from django.contrib import admin

from .models import (
    AcademicOverrideLog,
    AcademicReviewerProfile,
    Course,
    CourseProject,
    CourseProjectReviewDecision,
    CourseReview,
    Enrollment,
    Lesson,
    LessonProgress,
    LessonStructuredReview,
    LessonVersion,
    ResourceLibraryItem,
    ReviewAssignment,
    VideoLesson,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "instructor",
        "status",
        "level",
        "price",
        "total_lessons",
        "created_at",
    ]
    list_filter = ["status", "level", "language"]
    search_fields = ["title", "instructor__email"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["instructor"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "course",
        "course_instructor",
        "lesson_type",
        "position",
        "is_published",
    ]
    list_filter = ["course", "lesson_type", "is_published"]
    search_fields = ["title", "course__title", "course__slug", "course__instructor__email"]
    raw_id_fields = ["course"]
    readonly_fields = ["id", "created_at", "updated_at", "course_instructor"]
    ordering = ["course__title", "position"]

    def course_instructor(self, obj):
        return obj.course.instructor.email


@admin.register(VideoLesson)
class VideoLessonAdmin(admin.ModelAdmin):
    list_display = ["lesson", "transcoding_status", "duration_seconds", "file_size_bytes"]
    list_filter = ["transcoding_status"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["user", "course", "status", "amount_paid", "completed_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "course__title"]
    raw_id_fields = ["user", "course"]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ["enrollment", "lesson", "is_completed", "watch_percentage"]
    list_filter = ["is_completed"]


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ["course", "status", "reviewer", "submitted_by", "reviewed_at", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["course__title", "reviewer__email", "submitted_by__email", "comments"]
    raw_id_fields = ["course", "reviewer", "submitted_by"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(LessonVersion)
class LessonVersionAdmin(admin.ModelAdmin):
    list_display = ["lesson", "version_number", "editor", "is_published_version", "created_at"]
    list_filter = ["is_published_version", "lesson__course"]
    search_fields = ["lesson__title", "lesson__course__title", "editor__email"]
    raw_id_fields = ["lesson", "editor"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CourseProject)
class CourseProjectAdmin(admin.ModelAdmin):
    list_display = [
        "course",
        "approval_state",
        "passing_score",
        "version",
        "reviewed_by",
        "reviewed_at",
    ]
    list_filter = ["approval_state"]
    search_fields = ["course__title", "instructions", "reviewer_notes"]
    raw_id_fields = ["course", "reviewed_by"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ResourceLibraryItem)
class ResourceLibraryItemAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "resource_type",
        "visibility",
        "course",
        "owner",
        "version",
        "review_status",
        "download_count",
        "malware_scan_status",
        "malware_scanner",
        "created_at",
    ]
    list_filter = ["resource_type", "visibility", "review_status", "malware_scan_status"]
    search_fields = ["title", "owner__email", "course__title", "description", "checksum"]
    raw_id_fields = ["owner", "course", "reviewed_by"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AcademicReviewerProfile)
class AcademicReviewerProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "reviewer_role",
        "organization",
        "max_active_assignments",
        "automatic_assignment_enabled",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "reviewer_role",
        "is_active",
        "automatic_assignment_enabled",
        "organization",
    ]
    search_fields = ["user__email", "subject_tags"]
    raw_id_fields = ["user", "organization"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ReviewAssignment)
class ReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "target_type",
        "course",
        "assigned_reviewer",
        "priority",
        "review_status",
        "due_date",
        "completed_at",
        "escalation_level",
    ]
    list_filter = ["target_type", "priority", "review_status", "due_date", "escalation_level"]
    search_fields = ["course__title", "assigned_reviewer__email", "subject"]
    raw_id_fields = [
        "course",
        "lesson",
        "assigned_reviewer",
        "assigned_by",
        "organization",
        "escalated_to",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(LessonStructuredReview)
class LessonStructuredReviewAdmin(admin.ModelAdmin):
    list_display = ["lesson", "reviewer", "decision", "completed_at", "created_at"]
    list_filter = ["decision", "created_at"]
    search_fields = ["lesson__title", "reviewer__email"]
    raw_id_fields = ["lesson", "assignment", "reviewer"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CourseProjectReviewDecision)
class CourseProjectReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ["project", "reviewer", "decision", "project_version", "created_at"]
    list_filter = ["decision", "created_at"]
    search_fields = ["project__course__title", "reviewer__email", "notes"]
    raw_id_fields = ["project", "assignment", "reviewer"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AcademicOverrideLog)
class AcademicOverrideLogAdmin(admin.ModelAdmin):
    list_display = ["actor", "target_type", "target_id", "reason_code", "created_at"]
    list_filter = ["reason_code", "target_type", "created_at"]
    search_fields = ["actor__email", "reason", "target_id"]
    raw_id_fields = ["actor"]
    readonly_fields = [
        "id",
        "actor",
        "target_type",
        "target_id",
        "reason_code",
        "reason",
        "previous_state",
        "new_state",
        "metadata",
        "created_at",
        "updated_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
