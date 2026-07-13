from django.contrib import admin

from .models import CourseRating, QuizAttempt, QuizQuestion


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ["course", "course_instructor", "question_text", "correct_index", "position"]
    list_filter = ["course"]
    search_fields = ["question_text", "course__title", "course__slug", "course__instructor__email"]
    raw_id_fields = ["course"]
    readonly_fields = ["id", "created_at", "updated_at", "course_instructor"]
    ordering = ["course__title", "position"]

    def course_instructor(self, obj):
        return obj.course.instructor.email


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ["enrollment", "percentage", "passed", "attempt_number", "created_at"]
    list_filter = ["passed"]
    readonly_fields = ["id", "created_at", "answers"]


@admin.register(CourseRating)
class CourseRatingAdmin(admin.ModelAdmin):
    list_display = ["user", "course", "stars", "created_at"]
    list_filter = ["stars"]
    search_fields = ["user__email", "course__title"]
