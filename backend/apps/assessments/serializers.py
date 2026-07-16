from rest_framework import serializers

from .models import CourseRating, QuestionReviewDecision, QuizAttempt, QuizQuestion


class QuizQuestionSerializer(serializers.ModelSerializer):
    """
    Used when a student is taking the quiz.
    Does NOT include correct_index or explanation to prevent cheating.
    """

    class Meta:
        model = QuizQuestion
        fields = ["id", "question_text", "options", "position"]
        read_only_fields = fields


class QuizQuestionAdminSerializer(serializers.ModelSerializer):
    """
    Used by instructors and admins. Includes correct answer and explanation.
    """

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "question_text",
            "options",
            "correct_index",
            "explanation",
            "position",
            "question_type",
            "category",
            "reusable_key",
            "learning_objective",
            "lesson_mapping",
            "difficulty",
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "is_certificate_eligible",
        ]
        read_only_fields = ["id", "reviewed_by", "reviewed_at"]


class QuestionReviewDecisionSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)

    class Meta:
        model = QuestionReviewDecision
        fields = [
            "id",
            "question",
            "reviewer_email",
            "assignment_id",
            "decision",
            "section_comments",
            "required_changes",
            "certificate_eligible",
            "marked_reusable",
            "notes",
            "created_at",
        ]
        read_only_fields = fields


class StructuredQuestionReviewActionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            "approve",
            "approve_minor_edits",
            "request_changes",
            "reject",
            "escalate",
        ]
    )
    section_comments = serializers.DictField(required=False, default=dict)
    required_changes = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    certificate_eligible = serializers.BooleanField(default=False)
    marked_reusable = serializers.BooleanField(default=False)
    assignment_id = serializers.UUIDField(required=False, allow_null=True)


class QuizQuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = [
            "question_text",
            "options",
            "correct_index",
            "explanation",
            "position",
            "question_type",
            "category",
            "reusable_key",
            "learning_objective",
            "lesson_mapping",
            "difficulty",
            "review_status",
            "review_notes",
            "is_certificate_eligible",
        ]

    def validate_options(self, value):
        if not isinstance(value, list) or len(value) != 4:
            raise serializers.ValidationError("Provide exactly 4 answer options.")
        if any(not str(opt).strip() for opt in value):
            raise serializers.ValidationError("Options cannot be empty strings.")
        return value

    def validate_correct_index(self, value):
        if not 0 <= value <= 3:
            raise serializers.ValidationError("correct_index must be 0, 1, 2, or 3.")
        return value


class QuizSubmitSerializer(serializers.Serializer):
    """
    Receives the student's answers as a dict mapping question UUID to selected index.
    Example: { "answers": { "abc-uuid": 2, "def-uuid": 0 } }
    """

    answers = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=3),
        allow_empty=False,
    )

    def validate_answers(self, value):
        import uuid

        for key in value:
            try:
                uuid.UUID(str(key))
            except ValueError as exc:
                raise serializers.ValidationError(f"Invalid question ID format: {key}") from exc
        return value


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Result returned after grading a quiz attempt."""

    question_results = serializers.SerializerMethodField()
    pass_threshold = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "score",
            "total_questions",
            "percentage",
            "passed",
            "attempt_number",
            "pass_threshold",
            "question_results",
            "created_at",
        ]
        read_only_fields = fields

    def get_pass_threshold(self, obj):
        return obj.enrollment.course.pass_threshold

    def get_question_results(self, obj):
        """
        Return per-question feedback so students know what they got wrong.
        Includes the correct answer and explanation after submission.
        """
        from apps.assessments.models import QuizQuestion

        questions = QuizQuestion.objects.filter(course=obj.enrollment.course).order_by("position")

        results = []
        for q in questions:
            selected = obj.answers.get(str(q.id))
            is_correct = selected is not None and int(selected) == q.correct_index
            results.append(
                {
                    "question_id": str(q.id),
                    "question_text": q.question_text,
                    "options": q.options,
                    "selected_index": selected,
                    "correct_index": q.correct_index,
                    "is_correct": is_correct,
                    "explanation": q.explanation,
                }
            )
        return results


class CourseRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = CourseRating
        fields = ["id", "user_name", "stars", "review", "created_at"]
        read_only_fields = ["id", "user_name", "created_at"]


class CreateRatingSerializer(serializers.Serializer):
    stars = serializers.IntegerField(min_value=1, max_value=5)
    review = serializers.CharField(max_length=2000, allow_blank=True, default="")


class QuizQuestionBulkItemSerializer(serializers.Serializer):
    question_text = serializers.CharField(min_length=5, max_length=2000)
    options = serializers.ListField(
        child=serializers.CharField(max_length=500),
        min_length=2,
        max_length=4,
    )
    correct_index = serializers.IntegerField(min_value=0)
    explanation = serializers.CharField(max_length=2000, allow_blank=True, default="")
    position = serializers.IntegerField(min_value=0, default=0)
    question_type = serializers.CharField(max_length=40, default="multiple_choice")
    category = serializers.CharField(max_length=120, allow_blank=True, default="")
    reusable_key = serializers.SlugField(max_length=160, allow_blank=True, default="")
    learning_objective = serializers.CharField(max_length=500, allow_blank=True, default="")
    lesson_mapping = serializers.CharField(max_length=255, allow_blank=True, default="")
    difficulty = serializers.CharField(max_length=30, allow_blank=True, default="beginner")
    review_status = serializers.CharField(max_length=30, default="review_required")
    review_notes = serializers.CharField(max_length=2000, allow_blank=True, default="")
    is_certificate_eligible = serializers.BooleanField(default=False)

    def validate(self, data):
        options = data.get("options", [])
        correct_index = data.get("correct_index", 0)
        if any(not str(opt).strip() for opt in options):
            raise serializers.ValidationError({"options": "Options cannot be empty strings."})
        if correct_index >= len(options):
            raise serializers.ValidationError(
                {"correct_index": "correct_index must be less than the number of options."}
            )
        while len(options) < 4:
            options.append("Option " + str(len(options) + 1))
        data["options"] = options
        return data


class QuizQuestionBulkCreateSerializer(serializers.Serializer):
    questions = QuizQuestionBulkItemSerializer(many=True, min_length=1)
    replace = serializers.BooleanField(default=False)

    def validate_questions(self, value):
        if len(value) > 50:
            raise serializers.ValidationError(
                "Cannot create more than 50 questions in a single request."
            )
        return value
