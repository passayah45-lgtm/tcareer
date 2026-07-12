from django.contrib import admin
from .models import (
    ApplicationActivity,
    ApplicationAttachment,
    ApplicationNote,
    ApplicationTimeline,
    Interview,
    InterviewFeedback,
    InterviewParticipant,
    InterviewScorecard,
    JobAlert,
    JobApplication,
    JobListing,
    RecentlyViewedJob,
    RecruiterWaitlist,
    SavedJob,
    SavedJobCollection,
    SavedCandidate,
    TalentPool,
)


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ["title", "company_name", "job_type", "experience_level", "location", "is_active", "created_at"]
    list_filter = ["job_type", "experience_level", "is_active"]
    search_fields = ["title", "company_name", "description"]
    raw_id_fields = ["required_track", "posted_by"]
    readonly_fields = ["id", "views_count", "created_at", "updated_at"]


@admin.register(RecruiterWaitlist)
class RecruiterWaitlistAdmin(admin.ModelAdmin):
    list_display = ["full_name", "company_name", "email", "monthly_hires", "contacted", "created_at"]
    list_filter = ["contacted", "company_size", "monthly_hires"]
    search_fields = ["email", "company_name", "full_name"]
    actions = ["mark_contacted"]

    def mark_contacted(self, request, queryset):
        queryset.update(contacted=True)
    mark_contacted.short_description = "Mark selected as contacted"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ["job", "candidate", "organization", "stage", "is_archived", "created_at"]
    list_filter = ["stage", "is_archived", "organization"]
    search_fields = ["candidate__email", "candidate__full_name", "job__title"]
    raw_id_fields = ["job", "candidate", "organization", "assigned_recruiter", "hiring_manager"]
    readonly_fields = ["id", "created_at", "updated_at", "withdrawn_at", "deleted_at"]


@admin.register(ApplicationTimeline)
class ApplicationTimelineAdmin(admin.ModelAdmin):
    list_display = ["application", "event_type", "from_stage", "to_stage", "actor", "created_at"]
    list_filter = ["event_type", "to_stage"]
    raw_id_fields = ["application", "actor"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    list_display = ["application", "author", "is_internal", "created_at"]
    list_filter = ["is_internal"]
    raw_id_fields = ["application", "author"]


admin.site.register(ApplicationAttachment)
admin.site.register(ApplicationActivity)
admin.site.register(SavedJobCollection)
admin.site.register(SavedJob)
admin.site.register(RecentlyViewedJob)
admin.site.register(JobAlert)
admin.site.register(TalentPool)
admin.site.register(SavedCandidate)
admin.site.register(Interview)
admin.site.register(InterviewParticipant)
admin.site.register(InterviewFeedback)
admin.site.register(InterviewScorecard)
