from django.contrib import admin

from .models import CareerTrack, TrackCourse, UserTrackEnrollment


class TrackCourseInline(admin.TabularInline):
    model = TrackCourse
    extra = 0
    fields = [
        "course", "course_status", "course_instructor",
        "stage", "position", "is_required", "notes",
    ]
    readonly_fields = ["course_status", "course_instructor"]
    raw_id_fields = ["course"]
    ordering = ["position"]

    def course_status(self, obj):
        if not obj or not obj.course_id:
            return "-"
        return obj.course.status

    def course_instructor(self, obj):
        if not obj or not obj.course_id:
            return "-"
        return obj.course.instructor.email


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


@admin.register(TrackCourse)
class TrackCourseAdmin(admin.ModelAdmin):
    list_display = [
        "track", "course", "course_status", "course_instructor",
        "stage", "position", "is_required",
    ]
    list_filter = ["track", "stage", "is_required", "course__status"]
    search_fields = ["track__title", "track__slug", "course__title", "course__slug"]
    raw_id_fields = ["track", "course"]
    readonly_fields = ["id", "created_at", "updated_at", "course_status", "course_instructor"]
    ordering = ["track__position", "position"]

    def course_status(self, obj):
        return obj.course.status

    def course_instructor(self, obj):
        return obj.course.instructor.email
