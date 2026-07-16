"""
Assessment models for T-Career quiz engine.

Design decisions:

1. QuizQuestion belongs to a Course, not a Lesson.
   A course has one quiz taken after all lessons are complete.
   This matches the certificate gating model: finish the course, pass the quiz, earn the cert.

2. options stored as JSONField (list of strings).
   Four options per question is enforced in the service layer, not the DB.
   JSONField avoids a separate QuizOption table which adds joins without adding value at MVP.

3. correct_index is an integer (0-3).
   Simpler than storing the correct answer text. Immune to answer text edits
   breaking grading logic.

4. QuizAttempt stores the full answers as JSON.
   This allows retroactive analysis of which questions students get wrong most,
   which informs course improvement. Storing just pass/fail throws away that data.

5. attempt_number is computed at creation time and stored.
   Avoids a COUNT query on every attempt check.

6. Daily attempt limiting is enforced in the service layer via Redis,
   not the database, for performance.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class QuestionReviewStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEW_REQUIRED = "review_required", "Review Required"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class QuizQuestion(BaseModel):
    """
    A single multiple-choice question belonging to a course quiz.
    Every published course should have at least 5 questions.
    """

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="quiz_questions",
        db_index=True,
    )
    question_text = models.TextField()
    options = models.JSONField(
        help_text="List of 4 answer strings. Example: ['Paris', 'London', 'Berlin', 'Rome']"
    )
    correct_index = models.PositiveSmallIntegerField(
        help_text="Zero-based index of the correct answer in the options list (0-3)."
    )
    explanation = models.TextField(
        blank=True,
        default="",
        help_text="Shown to the student after answering. Explains why the answer is correct.",
    )
    position = models.PositiveIntegerField(default=0, db_index=True)
    question_type = models.CharField(
        max_length=40, blank=True, default="multiple_choice", db_index=True
    )
    category = models.CharField(max_length=120, blank=True, default="", db_index=True)
    reusable_key = models.SlugField(max_length=160, blank=True, default="", db_index=True)
    lesson_mapping = models.CharField(max_length=255, blank=True, default="")
    learning_objective = models.CharField(max_length=500, blank=True, default="")
    difficulty = models.CharField(max_length=30, blank=True, default="beginner", db_index=True)
    review_status = models.CharField(
        max_length=30,
        choices=QuestionReviewStatus.choices,
        default=QuestionReviewStatus.REVIEW_REQUIRED,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_quiz_questions",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default="")
    is_certificate_eligible = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "quiz_questions"
        ordering = ["position"]
        indexes = [
            models.Index(fields=["course", "position"]),
            models.Index(fields=["course", "category"], name="quiz_q_course_category_idx"),
            models.Index(fields=["course", "review_status"], name="quiz_q_course_review_idx"),
            models.Index(
                fields=["course", "is_certificate_eligible"], name="quiz_q_course_cert_idx"
            ),
        ]

    def __str__(self):
        return f"{self.course.title}: {self.question_text[:60]}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if not isinstance(self.options, list) or len(self.options) != 4:
            raise ValidationError("options must be a list of exactly 4 strings.")
        if not 0 <= self.correct_index <= 3:
            raise ValidationError("correct_index must be between 0 and 3.")


class QuizAttempt(BaseModel):
    """
    Records one student attempt at a course quiz.

    A student can attempt the quiz up to 3 times per day.
    Each attempt stores the full answer set so we can analyse
    which questions are causing failures.
    """

    enrollment = models.ForeignKey(
        "courses.Enrollment",
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        db_index=True,
    )
    answers = models.JSONField(
        help_text="Dict mapping question_id (str) to selected_index (int). Example: {'uuid': 2}"
    )
    score = models.PositiveSmallIntegerField(help_text="Number of correct answers.")
    total_questions = models.PositiveSmallIntegerField()
    percentage = models.PositiveSmallIntegerField(
        help_text="Score as a percentage rounded to nearest integer."
    )
    passed = models.BooleanField(default=False, db_index=True)
    attempt_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "quiz_attempts"
        indexes = [
            models.Index(fields=["enrollment", "passed"]),
            models.Index(fields=["enrollment", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.enrollment.user.email} - {self.enrollment.course.title} "
            f"attempt {self.attempt_number}: {self.percentage}%"
        )


class QuestionReviewDecision(BaseModel):
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name="review_decisions",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="question_review_decisions",
    )
    assignment_id = models.UUIDField(null=True, blank=True, db_index=True)
    decision = models.CharField(max_length=40, db_index=True)
    section_comments = models.JSONField(default=dict, blank=True)
    required_changes = models.JSONField(default=list, blank=True)
    certificate_eligible = models.BooleanField(default=False)
    marked_reusable = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "question_review_decisions"
        indexes = [
            models.Index(fields=["question", "decision"]),
            models.Index(fields=["reviewer", "created_at"]),
        ]
        ordering = ["-created_at"]


class CourseRating(BaseModel):
    """
    Student rating and review for a completed course.
    One rating per student per course. Only allowed after course completion.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_ratings",
        db_index=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="ratings",
        db_index=True,
    )
    stars = models.PositiveSmallIntegerField(help_text="Rating from 1 to 5.")
    review = models.TextField(blank=True, default="")

    class Meta:
        db_table = "course_ratings"
        unique_together = [("user", "course")]
        indexes = [
            models.Index(fields=["course", "stars"]),
        ]

    def __str__(self):
        return f"{self.user.email} rated {self.course.title}: {self.stars} stars"
