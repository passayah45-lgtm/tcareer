import logging

from django.core.cache import cache
from django.utils import timezone

from apps.courses.models import Enrollment, EnrollmentStatus
from common.audit import AuditService
from common.exceptions import ConflictError, PermissionError, ServiceError
from common.permission_service import PermissionService

from .models import (
    CourseRating,
    QuestionReviewDecision,
    QuestionReviewStatus,
    QuizAttempt,
    QuizQuestion,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS_PER_DAY = 3
ATTEMPT_CACHE_TTL = 60 * 60 * 24  # 24 hours


class QuizService:
    @staticmethod
    def get_questions(course):
        """Return all questions for a course quiz in order."""
        return QuizQuestion.objects.filter(course=course).order_by("position")

    @staticmethod
    def get_certificate_questions(course):
        return QuizQuestion.objects.filter(
            course=course,
            review_status=QuestionReviewStatus.APPROVED,
            is_certificate_eligible=True,
        ).order_by("position")

    @staticmethod
    def has_certificate_safe_assessment(course) -> bool:
        return QuizService.get_certificate_questions(course).count() >= 5

    @staticmethod
    def can_attempt(enrollment):
        """
        Check if the student can take the quiz right now.
        Returns (allowed: bool, reason: str).
        """
        # Must have completed all lessons first
        # Exception: if no video lessons exist (text-only or demo course),
        # allow quiz without requiring lesson completion
        total = enrollment.course.lessons.filter(is_published=True, deleted_at=None).count()
        completed = enrollment.lesson_progress.filter(is_completed=True).count()
        has_video_lessons = enrollment.course.lessons.filter(
            lesson_type="video", is_published=True, deleted_at=None
        ).exists()

        if total > 0 and completed < total and has_video_lessons:
            remaining = total - completed
            return False, f"Complete all lessons first. {remaining} lesson(s) remaining."

        # Check daily attempt limit via Redis
        cache_key = f"quiz_attempts:{enrollment.id}:{timezone.now().date()}"
        attempts_today = cache.get(cache_key, 0)

        if attempts_today >= MAX_ATTEMPTS_PER_DAY:
            return False, (
                f"You have used all {MAX_ATTEMPTS_PER_DAY} attempts for today. "
                "Try again tomorrow."
            )

        # Already passed - no need to retake
        if QuizAttempt.objects.filter(enrollment=enrollment, passed=True).exists():
            return False, "You have already passed this quiz."

        return True, ""

    @staticmethod
    def submit_attempt(enrollment, answers: dict) -> QuizAttempt:
        """
        Grade a quiz attempt and return the QuizAttempt record.

        answers: dict mapping question_id (str UUID) to selected_index (int)
        """
        can_attempt, reason = QuizService.can_attempt(enrollment)
        if not can_attempt:
            raise ServiceError(reason)

        questions = QuizService.get_certificate_questions(enrollment.course)
        if not questions.exists():
            raise ServiceError(
                "This course does not have an approved certificate-eligible quiz yet."
            )

        total = questions.count()
        correct = 0

        for question in questions:
            selected = answers.get(str(question.id))
            if selected is not None and int(selected) == question.correct_index:
                correct += 1

        percentage = round((correct / total) * 100)
        passed = percentage >= enrollment.course.pass_threshold

        # Increment daily attempt counter in Redis
        cache_key = f"quiz_attempts:{enrollment.id}:{timezone.now().date()}"
        attempts_today = cache.get(cache_key, 0)
        cache.set(cache_key, attempts_today + 1, timeout=ATTEMPT_CACHE_TTL)

        attempt_number = QuizAttempt.objects.filter(enrollment=enrollment).count() + 1

        attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            answers=answers,
            score=correct,
            total_questions=total,
            percentage=percentage,
            passed=passed,
            attempt_number=attempt_number,
        )

        if passed:
            logger.info(
                "Quiz passed: user=%s course=%s score=%s%%",
                enrollment.user.email,
                enrollment.course.title,
                percentage,
            )
            # Mark enrollment as completed and trigger certificate generation
            from django.utils import timezone as tz

            from apps.courses.models import EnrollmentStatus

            if enrollment.status != EnrollmentStatus.COMPLETED:
                enrollment.status = EnrollmentStatus.COMPLETED
                enrollment.completed_at = tz.now()
                enrollment.save(update_fields=["status", "completed_at", "updated_at"])
                logger.info(
                    "Enrollment completed via quiz pass: user=%s course=%s",
                    enrollment.user.email,
                    enrollment.course.title,
                )

            # Update career track progress if enrolled in a track
            try:
                from apps.tracks.models import UserTrackEnrollment

                track_enrollments = UserTrackEnrollment.objects.filter(user=enrollment.user)
                for te in track_enrollments:
                    course_ids = set(
                        te.track.track_courses.filter(is_required=True).values_list(
                            "course_id", flat=True
                        )
                    )
                    if enrollment.course.id in course_ids:
                        from apps.tracks.views import _update_enrollment_progress

                        _update_enrollment_progress(te)
            except Exception as e:
                logger.warning("Could not update track progress: %s", e)

            # Send quiz passed notification
            try:
                from apps.notifications.models import NotificationService

                NotificationService.quiz_passed(enrollment.user, enrollment.course, percentage)
            except Exception as e:
                logger.warning("Could not send quiz notification: %s", e)

            # Trigger certificate generation
            from tasks.certificates import generate_certificate

            generate_certificate.delay(str(enrollment.id))

        return attempt

    @staticmethod
    def get_attempt_history(enrollment):
        return QuizAttempt.objects.filter(enrollment=enrollment).order_by("-created_at")


class RatingService:
    @staticmethod
    def create_rating(user, course, stars: int, review: str = "") -> CourseRating:
        """
        Submit a course rating. Only allowed after course completion.
        One rating per student per course.
        """
        if not 1 <= stars <= 5:
            raise ServiceError("Rating must be between 1 and 5 stars.")

        try:
            enrollment = Enrollment.objects.get(user=user, course=course)
        except Enrollment.DoesNotExist as exc:
            raise PermissionError("You must be enrolled in this course to rate it.") from exc

        if enrollment.status != EnrollmentStatus.COMPLETED:
            raise PermissionError("Complete the course before leaving a review.")

        if CourseRating.objects.filter(user=user, course=course).exists():
            raise ConflictError("You have already rated this course.")

        rating = CourseRating.objects.create(
            user=user,
            course=course,
            stars=stars,
            review=review.strip(),
        )
        logger.info(
            "Rating submitted: user=%s course=%s stars=%s",
            user.email,
            course.title,
            stars,
        )
        return rating

    @staticmethod
    def get_course_stats(course) -> dict:
        from django.db.models import Avg, Count

        result = CourseRating.objects.filter(course=course).aggregate(
            average=Avg("stars"),
            count=Count("id"),
        )
        return {
            "average": round(result["average"] or 0, 1),
            "count": result["count"] or 0,
        }


class QuizBuilderService:
    @staticmethod
    def bulk_create(course, questions_data, replace, instructor):
        import logging

        from django.db import transaction

        from common.exceptions import PermissionError, ServiceError

        from .models import QuizQuestion

        logger = logging.getLogger(__name__)

        if course.instructor != instructor:
            raise PermissionError("You do not own this course.")

        if replace and not questions_data:
            raise ServiceError("Cannot replace questions with an empty list.")

        with transaction.atomic():
            if replace:
                deleted_count = QuizQuestion.objects.filter(course=course).delete()[0]
                logger.info("Deleted %d questions from course %s", deleted_count, course.id)

            if replace:
                start_position = 0
            else:
                last = (
                    QuizQuestion.objects.filter(course=course)
                    .order_by("-position")
                    .values_list("position", flat=True)
                    .first()
                )
                start_position = (last + 10) if last is not None else 0

            all_default = all(q.get("position", 0) == 0 for q in questions_data)
            to_create = []
            for i, q_data in enumerate(questions_data):
                options = list(q_data["options"])
                while len(options) < 4:
                    options.append("Option " + str(len(options) + 1))
                position = (
                    start_position + (i * 10)
                    if all_default
                    else q_data.get("position", start_position + i * 10)
                )
                review_status = q_data.get("review_status", QuestionReviewStatus.REVIEW_REQUIRED)
                is_certificate_eligible = bool(q_data.get("is_certificate_eligible", False))
                if review_status != QuestionReviewStatus.APPROVED:
                    is_certificate_eligible = False
                to_create.append(
                    QuizQuestion(
                        course=course,
                        question_text=q_data["question_text"],
                        options=options,
                        correct_index=q_data["correct_index"],
                        explanation=q_data.get("explanation", ""),
                        position=position,
                        question_type=q_data.get("question_type", "multiple_choice"),
                        category=q_data.get("category", ""),
                        reusable_key=q_data.get("reusable_key", ""),
                        learning_objective=q_data.get("learning_objective", ""),
                        lesson_mapping=q_data.get("lesson_mapping", ""),
                        difficulty=q_data.get("difficulty", "beginner"),
                        review_status=review_status,
                        review_notes=q_data.get("review_notes", ""),
                        is_certificate_eligible=is_certificate_eligible,
                    )
                )
            QuizQuestion.objects.bulk_create(to_create)

        logger.info(
            "Bulk created %d questions for course %s by %s",
            len(to_create),
            course.id,
            instructor.email,
        )
        return list(QuizQuestion.objects.filter(course=course).order_by("position"))

    @staticmethod
    def get_question_count(course):
        from .models import QuizQuestion

        return QuizQuestion.objects.filter(course=course).count()

    @staticmethod
    def reorder_questions(course, question_data, instructor):
        from django.db import transaction

        from common.exceptions import PermissionError, ServiceError

        from .models import QuizQuestion

        if course.instructor != instructor:
            raise PermissionError("You do not own this course.")

        submitted_ids = {str(item["id"]) for item in question_data}
        existing = list(QuizQuestion.objects.filter(course=course).only("id", "position"))
        existing_ids = {str(q.id) for q in existing}
        extra = submitted_ids - existing_ids
        if extra:
            raise ServiceError("Unknown question IDs: " + ", ".join(extra) + ".")

        position_map = {str(item["id"]): item["position"] for item in question_data}
        with transaction.atomic():
            for q in existing:
                if str(q.id) in position_map:
                    q.position = position_map[str(q.id)]
            QuizQuestion.objects.bulk_update(existing, ["position"])

        return list(QuizQuestion.objects.filter(course=course).order_by("position"))


class QuestionReviewService:
    @staticmethod
    def can_review(user, question: QuizQuestion) -> bool:
        if question.course.instructor_id == getattr(user, "id", None):
            return False
        return PermissionService.is_academic_reviewer(user)

    @staticmethod
    def approve(
        question: QuizQuestion, reviewer, *, notes: str = "", certificate_eligible: bool = True
    ) -> QuizQuestion:
        if not QuestionReviewService.can_review(reviewer, question):
            raise PermissionError("You cannot review this question.")
        if (
            "[REVIEW REQUIRED]" in question.question_text
            or "[REVIEW REQUIRED]" in question.explanation
        ):
            raise ServiceError("Remove review markers before approving this question.")
        question.review_status = QuestionReviewStatus.APPROVED
        question.reviewed_by = reviewer
        question.reviewed_at = timezone.now()
        question.review_notes = notes
        question.is_certificate_eligible = bool(certificate_eligible)
        question.save(
            update_fields=[
                "review_status",
                "reviewed_by",
                "reviewed_at",
                "review_notes",
                "is_certificate_eligible",
                "updated_at",
            ]
        )
        AuditService.record(
            actor=reviewer,
            action="quiz_question_approved",
            target=question,
            metadata={
                "course_id": str(question.course_id),
                "certificate_eligible": question.is_certificate_eligible,
            },
        )
        return question

    @staticmethod
    def structured_review(
        question: QuizQuestion,
        reviewer,
        *,
        decision: str,
        section_comments=None,
        required_changes=None,
        notes: str = "",
        certificate_eligible: bool = False,
        marked_reusable: bool = False,
        assignment_id=None,
    ) -> QuizQuestion:
        if not QuestionReviewService.can_review(reviewer, question):
            raise PermissionError("You cannot review this question.")
        status_map = {
            "approve": QuestionReviewStatus.APPROVED,
            "approve_minor_edits": QuestionReviewStatus.APPROVED,
            "request_changes": QuestionReviewStatus.REVIEW_REQUIRED,
            "reject": QuestionReviewStatus.REJECTED,
            "escalate": QuestionReviewStatus.REVIEW_REQUIRED,
        }
        if decision not in status_map:
            raise ServiceError("Invalid question review decision.")
        status = status_map[decision]
        if status != QuestionReviewStatus.APPROVED:
            certificate_eligible = False
        question.review_status = status
        question.reviewed_by = reviewer
        question.reviewed_at = timezone.now()
        question.review_notes = notes
        question.is_certificate_eligible = bool(certificate_eligible)
        if marked_reusable and question.reusable_key:
            question.category = question.category or "reusable"
        question.save(
            update_fields=[
                "review_status",
                "reviewed_by",
                "reviewed_at",
                "review_notes",
                "is_certificate_eligible",
                "category",
                "updated_at",
            ]
        )
        decision_record = QuestionReviewDecision.objects.create(
            question=question,
            reviewer=reviewer,
            assignment_id=assignment_id,
            decision=decision,
            section_comments=section_comments or {},
            required_changes=required_changes or [],
            certificate_eligible=question.is_certificate_eligible,
            marked_reusable=marked_reusable,
            notes=notes,
        )
        AuditService.record(
            actor=reviewer,
            action="quiz_question_structured_reviewed",
            target=question,
            metadata={"decision": decision, "decision_id": str(decision_record.id)},
        )
        return question

    @staticmethod
    def require_review(question: QuizQuestion, reviewer=None, *, notes: str = "") -> QuizQuestion:
        if reviewer is not None and not QuestionReviewService.can_review(reviewer, question):
            raise PermissionError("You cannot review this question.")
        question.review_status = QuestionReviewStatus.REVIEW_REQUIRED
        question.reviewed_by = (
            reviewer if reviewer and getattr(reviewer, "is_authenticated", False) else None
        )
        question.reviewed_at = timezone.now() if reviewer else None
        question.review_notes = notes
        question.is_certificate_eligible = False
        question.save(
            update_fields=[
                "review_status",
                "reviewed_by",
                "reviewed_at",
                "review_notes",
                "is_certificate_eligible",
                "updated_at",
            ]
        )
        return question
