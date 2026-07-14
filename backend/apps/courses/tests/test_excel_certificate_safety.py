from __future__ import annotations

import pytest
from django.utils import timezone

from apps.assessments.models import QuestionReviewStatus, QuizAttempt, QuizQuestion
from apps.assessments.services import QuestionReviewService
from apps.certificates.services import CertificateService
from apps.courses.models import (
    Course,
    CourseStatus,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonProgress,
)
from apps.courses.services import CourseService
from apps.users.tests.factories import AdminFactory, InstructorFactory, UserFactory
from common.exceptions import PermissionError, ServiceError


def make_course(instructor, *, status=CourseStatus.DRAFT):
    return Course.objects.create(
        instructor=instructor,
        title="Excel for Data Analysis",
        slug="excel-for-data-analysis",
        short_description="Learn Excel analysis.",
        description="A complete Excel course.",
        status=status,
        requirements=["Basic computer literacy"],
        what_you_learn=["Clean spreadsheet data", "Build pivots and dashboards"],
    )


def add_lesson(course, *, published=True):
    return Lesson.objects.create(
        course=course,
        title="Excel foundations",
        lesson_type="text",
        content="## Excel-specific explanation\nReal content",
        position=10,
        is_published=published,
    )


def add_questions(course, count=5, *, approved=False):
    questions = []
    for index in range(count):
        questions.append(
            QuizQuestion.objects.create(
                course=course,
                question_text=f"Question {index}?",
                options=["A", "B", "C", "D"],
                correct_index=0,
                explanation="Reviewed explanation.",
                position=index * 10,
                review_status=QuestionReviewStatus.APPROVED
                if approved
                else QuestionReviewStatus.REVIEW_REQUIRED,
                is_certificate_eligible=approved,
            )
        )
    return questions


@pytest.mark.django_db
def test_unauthorized_user_cannot_approve_question():
    instructor = InstructorFactory()
    student = UserFactory()
    course = make_course(instructor)
    question = add_questions(course, 1)[0]

    with pytest.raises(PermissionError):
        QuestionReviewService.approve(question, student)

    question.refresh_from_db()
    assert question.review_status == QuestionReviewStatus.REVIEW_REQUIRED
    assert question.is_certificate_eligible is False


@pytest.mark.django_db
def test_authorized_reviewer_can_approve_question_and_audit():
    instructor = InstructorFactory()
    course = make_course(instructor)
    question = add_questions(course, 1)[0]

    QuestionReviewService.approve(question, instructor, notes="Reviewed.")

    question.refresh_from_db()
    assert question.review_status == QuestionReviewStatus.APPROVED
    assert question.reviewed_by == instructor
    assert question.is_certificate_eligible is True


@pytest.mark.django_db
def test_review_marker_blocks_approval():
    instructor = InstructorFactory()
    course = make_course(instructor)
    question = add_questions(course, 1)[0]
    question.explanation = "[REVIEW REQUIRED] Needs review."
    question.save(update_fields=["explanation", "updated_at"])

    with pytest.raises(ServiceError, match="review markers"):
        QuestionReviewService.approve(question, instructor)


@pytest.mark.django_db
def test_draft_course_cannot_issue_certificate_even_after_quiz_pass():
    instructor = InstructorFactory()
    student = UserFactory()
    course = make_course(instructor, status=CourseStatus.DRAFT)
    lesson = add_lesson(course, published=True)
    add_questions(course, 5, approved=True)
    enrollment = Enrollment.objects.create(
        user=student, course=course, status=EnrollmentStatus.COMPLETED, completed_at=timezone.now()
    )
    LessonProgress.objects.create(
        enrollment=enrollment, lesson=lesson, is_completed=True, watch_percentage=100
    )
    QuizAttempt.objects.create(
        enrollment=enrollment, answers={}, score=5, total_questions=5, percentage=100, passed=True
    )

    eligible, reasons = CertificateService.eligibility(enrollment)

    assert eligible is False
    assert any("published" in reason for reason in reasons)


@pytest.mark.django_db
def test_unapproved_assessment_blocks_certificate():
    instructor = InstructorFactory()
    student = UserFactory()
    course = make_course(instructor, status=CourseStatus.PUBLISHED)
    lesson = add_lesson(course, published=True)
    add_questions(course, 5, approved=False)
    enrollment = Enrollment.objects.create(
        user=student, course=course, status=EnrollmentStatus.COMPLETED, completed_at=timezone.now()
    )
    LessonProgress.objects.create(
        enrollment=enrollment, lesson=lesson, is_completed=True, watch_percentage=100
    )
    QuizAttempt.objects.create(
        enrollment=enrollment, answers={}, score=5, total_questions=5, percentage=100, passed=True
    )

    eligible, reasons = CertificateService.eligibility(enrollment)

    assert eligible is False
    assert any("approved certificate-eligible" in reason for reason in reasons)


@pytest.mark.django_db
def test_approved_valid_flow_allows_certificate_eligibility():
    instructor = InstructorFactory()
    student = UserFactory()
    course = make_course(instructor, status=CourseStatus.PUBLISHED)
    lesson = add_lesson(course, published=True)
    add_questions(course, 5, approved=True)
    enrollment = Enrollment.objects.create(
        user=student, course=course, status=EnrollmentStatus.COMPLETED, completed_at=timezone.now()
    )
    LessonProgress.objects.create(
        enrollment=enrollment, lesson=lesson, is_completed=True, watch_percentage=100
    )
    QuizAttempt.objects.create(
        enrollment=enrollment, answers={}, score=5, total_questions=5, percentage=100, passed=True
    )

    eligible, reasons = CertificateService.eligibility(enrollment)

    assert eligible is True
    assert reasons == []


@pytest.mark.django_db
def test_publish_validation_blocks_review_required_assessments():
    instructor = InstructorFactory()
    course = make_course(instructor)
    add_lesson(course, published=True)
    add_questions(course, 5, approved=False)

    errors = CourseService.publish_validation_errors(course)

    assert any("approved certificate-eligible" in error for error in errors)


@pytest.mark.django_db
def test_platform_admin_can_approve_instructor_question():
    instructor = InstructorFactory()
    admin = AdminFactory()
    course = make_course(instructor)
    question = add_questions(course, 1)[0]

    QuestionReviewService.approve(question, admin)

    question.refresh_from_db()
    assert question.review_status == QuestionReviewStatus.APPROVED
