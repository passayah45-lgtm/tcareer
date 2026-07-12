from django.contrib import admin
from .models import Course, Lesson, VideoLesson, Enrollment, LessonProgress


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "instructor", "status", "level", "price", "total_lessons", "created_at"]
    list_filter = ["status", "level", "language"]
    search_fields = ["title", "instructor__email"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["instructor"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "lesson_type", "position", "is_published"]
    list_filter = ["lesson_type", "is_published"]
    search_fields = ["title", "course__title"]
    raw_id_fields = ["course"]


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
