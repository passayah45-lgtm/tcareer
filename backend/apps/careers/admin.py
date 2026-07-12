from django.contrib import admin
from .models import CareerResume, Portfolio, PortfolioAIReview, PortfolioSkill, PortfolioProject, Resume, ResumeAIReview


class PortfolioSkillInline(admin.TabularInline):
    model = PortfolioSkill
    extra = 0
    fields = ["name", "category", "source", "position"]
    readonly_fields = ["source"]


class PortfolioProjectInline(admin.TabularInline):
    model = PortfolioProject
    extra = 0
    fields = ["title", "is_featured", "position", "project_url", "github_url"]


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["user", "headline", "desired_role", "experience_level", "visibility", "profile_views", "created_at"]
    list_filter = ["visibility", "experience_level"]
    search_fields = ["user__email", "user__full_name", "desired_role", "headline"]
    readonly_fields = ["profile_views", "created_at", "updated_at"]
    inlines = [PortfolioSkillInline, PortfolioProjectInline]
    raw_id_fields = ["user"]


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "portfolio", "is_featured", "position", "created_at"]
    list_filter = ["is_featured"]
    search_fields = ["title", "portfolio__user__email"]
    raw_id_fields = ["portfolio"]


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "target_role", "last_generated_at", "created_at"]
    search_fields = ["user__email", "user__full_name", "target_role"]
    readonly_fields = ["pdf_url", "last_generated_at", "created_at", "updated_at"]
    raw_id_fields = ["user"]


@admin.register(CareerResume)
class CareerResumeAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "target_role", "is_default", "is_archived", "created_at"]
    list_filter = ["is_default", "is_archived"]
    search_fields = ["user__email", "user__full_name", "title", "target_role"]
    raw_id_fields = ["user"]


@admin.register(ResumeAIReview)
class ResumeAIReviewAdmin(admin.ModelAdmin):
    list_display = ["resume", "user", "review_type", "overall_score", "ats_score", "match_score", "confidence", "created_at"]
    list_filter = ["review_type", "created_at"]
    search_fields = ["resume__title", "user__email", "summary"]
    readonly_fields = [
        "resume",
        "user",
        "review_type",
        "job",
        "comparison_resume",
        "ai_request",
        "ai_response",
        "prompt_version",
        "model_name",
        "estimated_cost",
        "overall_score",
        "ats_score",
        "match_score",
        "confidence",
        "extracted_skills",
        "missing_skills",
        "strengths",
        "weaknesses",
        "suggestions",
        "action_items",
        "report",
        "summary",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["resume", "user", "job", "comparison_resume", "ai_request", "ai_response"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PortfolioAIReview)
class PortfolioAIReviewAdmin(admin.ModelAdmin):
    list_display = ["portfolio", "user", "review_type", "overall_score", "project_score", "github_score", "match_score", "created_at"]
    list_filter = ["review_type", "created_at"]
    search_fields = ["portfolio__user__email", "portfolio__headline", "summary"]
    readonly_fields = [
        "portfolio",
        "user",
        "review_type",
        "project",
        "job",
        "ai_request",
        "ai_response",
        "prompt_version",
        "model_name",
        "estimated_cost",
        "overall_score",
        "project_score",
        "github_score",
        "match_score",
        "confidence",
        "extracted_skills",
        "missing_skills",
        "technology_stack",
        "strengths",
        "weaknesses",
        "suggestions",
        "action_items",
        "report",
        "summary",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["portfolio", "user", "project", "job", "ai_request", "ai_response"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
