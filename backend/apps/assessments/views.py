import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.courses.models import Course, Enrollment
from common.exceptions import PermissionError
from common.permissions import IsInstructor

from .models import CourseRating, QuestionReviewStatus, QuizQuestion
from .serializers import (
    CourseRatingSerializer,
    CreateRatingSerializer,
    QuestionReviewDecisionSerializer,
    QuizAttemptSerializer,
    QuizQuestionAdminSerializer,
    QuizQuestionCreateSerializer,
    QuizQuestionSerializer,
    QuizSubmitSerializer,
    StructuredQuestionReviewActionSerializer,
)
from .services import QuestionReviewService, QuizService, RatingService

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quiz_questions(request, course_id):
    """
    GET /api/v1/assessments/{course_id}/questions/

    Returns quiz questions for enrolled students (without correct answers).
    Instructors see the full question including correct_index.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    questions = QuizService.get_questions(course)

    is_instructor = request.user == course.instructor or request.user.role == "admin"

    if is_instructor:
        serializer = QuizQuestionAdminSerializer(questions, many=True)
    else:
        enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
        QuizService.can_attempt(enrollment)
        serializer = QuizQuestionSerializer(questions, many=True)

    return Response(
        {
            "questions": serializer.data,
            "total": questions.count(),
            "pass_threshold": course.pass_threshold,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_quiz(request, course_id):
    """
    POST /api/v1/assessments/{course_id}/submit/

    Grades the quiz and returns results.
    Triggers certificate generation on pass.

    Request: { "answers": { "question-uuid": 2, "question-uuid-2": 0 } }
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)

    serializer = QuizSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    attempt = QuizService.submit_attempt(
        enrollment=enrollment,
        answers=serializer.validated_data["answers"],
    )
    return Response(
        QuizAttemptSerializer(attempt).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quiz_attempt_history(request, course_id):
    """
    GET /api/v1/assessments/{course_id}/attempts/

    Returns the student's attempt history for a course.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    attempts = QuizService.get_attempt_history(enrollment)
    return Response(QuizAttemptSerializer(attempts, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def can_attempt_quiz(request, course_id):
    """
    GET /api/v1/assessments/{course_id}/can-attempt/

    Returns whether the student can take the quiz right now.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    can, reason = QuizService.can_attempt(enrollment)
    return Response({"can_attempt": can, "reason": reason})


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def create_question(request, course_id):
    """
    POST /api/v1/assessments/{course_id}/questions/create/

    Instructor adds a quiz question to a course.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if course.instructor != request.user:
        raise PermissionError("You do not own this course.")

    serializer = QuizQuestionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = serializer.save(
        course=course,
        review_status=QuestionReviewStatus.REVIEW_REQUIRED,
        is_certificate_eligible=False,
    )
    return Response(
        QuizQuestionAdminSerializer(question).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsInstructor])
def manage_question(request, course_id, question_id):
    """
    PATCH /api/v1/assessments/{course_id}/questions/{question_id}/
    DELETE /api/v1/assessments/{course_id}/questions/{question_id}/
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if course.instructor != request.user:
        raise PermissionError("You do not own this course.")
    question = get_object_or_404(QuizQuestion, id=question_id, course=course)

    if request.method == "DELETE":
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = QuizQuestionCreateSerializer(question, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    data = dict(serializer.validated_data)
    data.pop("review_status", None)
    data.pop("is_certificate_eligible", None)
    question = serializer.update(question, data)
    if question.review_status == QuestionReviewStatus.APPROVED:
        QuestionReviewService.require_review(
            question,
            request.user,
            notes="Question content changed after approval.",
        )
    return Response(QuizQuestionAdminSerializer(question).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def approve_question(request, course_id, question_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    question = get_object_or_404(QuizQuestion, id=question_id, course=course)
    question = QuestionReviewService.approve(
        question,
        request.user,
        notes=request.data.get("review_notes", ""),
        certificate_eligible=bool(request.data.get("is_certificate_eligible", True)),
    )
    return Response(QuizQuestionAdminSerializer(question).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def structured_question_review(request, course_id, question_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    question = get_object_or_404(QuizQuestion, id=question_id, course=course)
    serializer = StructuredQuestionReviewActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = QuestionReviewService.structured_review(
        question,
        request.user,
        decision=serializer.validated_data["decision"],
        section_comments=serializer.validated_data.get("section_comments", {}),
        required_changes=serializer.validated_data.get("required_changes", []),
        notes=serializer.validated_data.get("notes", ""),
        certificate_eligible=serializer.validated_data.get("certificate_eligible", False),
        marked_reusable=serializer.validated_data.get("marked_reusable", False),
        assignment_id=serializer.validated_data.get("assignment_id"),
    )
    decision = question.review_decisions.order_by("-created_at").first()
    return Response(
        {
            "question": QuizQuestionAdminSerializer(question).data,
            "decision": QuestionReviewDecisionSerializer(decision).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_rating(request, course_id):
    """
    POST /api/v1/assessments/{course_id}/rate/

    Submit a star rating and optional review after course completion.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    serializer = CreateRatingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    rating = RatingService.create_rating(
        user=request.user,
        course=course,
        stars=serializer.validated_data["stars"],
        review=serializer.validated_data.get("review", ""),
    )
    return Response(CourseRatingSerializer(rating).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def course_ratings(request, course_id):
    """
    GET /api/v1/assessments/{course_id}/ratings/

    Public endpoint. Returns ratings and average score for a course.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    ratings = CourseRating.objects.filter(course=course).select_related("user")
    stats = RatingService.get_course_stats(course)
    return Response(
        {
            "stats": stats,
            "ratings": CourseRatingSerializer(ratings, many=True).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def bulk_create_questions(request, course_id):
    from common.exceptions import PermissionError

    from .serializers import QuizQuestionAdminSerializer, QuizQuestionBulkCreateSerializer
    from .services import QuizBuilderService

    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if course.instructor != request.user:
        raise PermissionError("You do not own this course.")
    serializer = QuizQuestionBulkCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    questions = QuizBuilderService.bulk_create(
        course=course,
        questions_data=serializer.validated_data["questions"],
        replace=serializer.validated_data["replace"],
        instructor=request.user,
    )
    return Response(
        {
            "questions": QuizQuestionAdminSerializer(questions, many=True).data,
            "total": len(questions),
            "course_id": str(course.id),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def reorder_questions(request, course_id):
    from common.exceptions import PermissionError

    from .serializers import QuizQuestionAdminSerializer
    from .services import QuizBuilderService

    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if course.instructor != request.user:
        raise PermissionError("You do not own this course.")
    questions_data = request.data.get("questions", [])
    if not isinstance(questions_data, list) or not questions_data:
        return Response(
            {"errors": {"questions": "Provide a non-empty list of question positions."}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    questions = QuizBuilderService.reorder_questions(
        course=course,
        question_data=questions_data,
        instructor=request.user,
    )
    return Response(
        {
            "questions": QuizQuestionAdminSerializer(questions, many=True).data,
            "total": len(questions),
        }
    )
