from django.contrib import admin
from .models import CareerTrack, TrackCourse, UserTrackEnrollment


class TrackCourseInline(admin.TabularInline):
    model = TrackCourse
    extra = 0
    fields = ["course", "stage", "position", "is_required", "notes"]
    raw_id_fields = ["course"]
    ordering = ["position"]


@admin.register(CareerTrack)
class CareerTrackAdmin(admin.ModelAdmin):
    list_display = [
        "title", "category", "difficulty", "total_courses",
        "duration_display", "is_active", "position",
    ]
    list_filter = ["category", "difficulty", "is_active"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [TrackCourseInline]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = [
        ("Basic Info", {
            "fields": ["id", "title", "slug", "short_description", "description"],
        }),
        ("Classification", {
            "fields": ["category", "difficulty", "icon", "color", "position", "is_active"],
        }),
        ("Career Info", {
            "fields": [
                "target_job_titles", "skills_acquired",
                "estimated_weeks_min", "estimated_weeks_max",
                "avg_salary_min", "avg_salary_max",
            ],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]


@admin.register(UserTrackEnrollment)
class UserTrackEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "user", "track", "current_stage", "courses_completed",
        "progress_percentage", "is_completed", "last_activity_at",
    ]
    list_filter = ["is_completed", "current_stage"]
    search_fields = ["user__email", "track__title"]
    readonly_fields = ["id", "created_at", "last_activity_at", "progress_percentage"]
