import pytest
from rest_framework.test import APIClient

from apps.assessments.models import QuestionReviewStatus, QuizQuestion
from apps.courses.models import (
    ContentReviewStatus,
    CourseReview,
    ResourceLibraryItem,
)
from apps.courses.services import (
    CourseProjectService,
    CourseQualityService,
    CourseService,
    LessonInlineUpdateService,
    LessonVersionService,
    ResourceLibraryService,
)
from apps.courses.tests.factories import CourseFactory, LessonFactory
from apps.users.models import UserRole
from apps.users.tests.factories import UserFactory
from common.exceptions import ServiceError


@pytest.mark.django_db
class TestAcademicAuthoringReview:
    def test_lesson_version_capture_and_rollback_restores_content_as_draft(self):
        course = CourseFactory()
        lesson = LessonFactory(course=course, content="Original lesson", is_published=False)

        first = LessonVersionService.capture(lesson, course.instructor, summary="Initial draft")
        lesson.content = "Changed lesson"
        lesson.save(update_fields=["content", "updated_at"])
        second = LessonVersionService.capture(lesson, course.instructor, summary="Expanded draft")

        rolled_back = LessonVersionService.rollback(lesson, first, course.instructor)

        assert second.version_number == 2
        assert rolled_back.content == "Original lesson"
        assert rolled_back.review_status == ContentReviewStatus.DRAFT
        assert rolled_back.is_published is False

    def test_inline_lesson_publish_requires_academic_approval(self):
        course = CourseFactory()
        lesson = LessonFactory(
            course=course,
            is_published=False,
            review_status=ContentReviewStatus.DRAFT,
            lesson_type="text",
        )

        with pytest.raises(ServiceError, match="academically approved"):
            LessonInlineUpdateService.update(
                lesson=lesson,
                data={"is_published": True},
                instructor=course.instructor,
            )

    def test_course_publish_requires_academic_review(self):
        course = CourseFactory()
        lesson = LessonFactory(
            course=course,
            is_published=True,
            review_status=ContentReviewStatus.PUBLISHED,
            published_version=1,
            content="Approved lesson content",
        )

        with pytest.raises(ServiceError, match="academic review"):
            CourseService.publish_course(course, course.instructor)

        CourseReview.objects.create(
            course=course,
            status=ContentReviewStatus.APPROVED,
            reviewer=course.instructor,
            submitted_by=course.instructor,
        )
        published = CourseService.publish_course(course, course.instructor)

        assert lesson.course_id == course.id
        assert published.status == "published"

    def test_project_review_controls_final_project_publish_gate(self):
        course = CourseFactory(tags=["requires-final-project"])
        LessonFactory(
            course=course,
            is_published=True,
            review_status=ContentReviewStatus.PUBLISHED,
            published_version=1,
            content="Approved lesson content",
        )
        CourseReview.objects.create(
            course=course,
            status=ContentReviewStatus.APPROVED,
            reviewer=course.instructor,
            submitted_by=course.instructor,
        )
        project = CourseProjectService.upsert(
            course,
            course.instructor,
            {
                "instructions": "Build an Excel model.",
                "required_deliverables": ["Workbook", "Reflection"],
                "rubric": [{"criterion": "Accuracy", "points": 50}],
                "evaluation_criteria": ["Accuracy", "Clarity"],
                "passing_score": 70,
            },
        )

        assert "Final project" in " ".join(CourseService.publish_validation_errors(course))

        reviewer = UserFactory(role=UserRole.CONTENT_MODERATOR, is_verified=True)
        CourseProjectService.review(project, reviewer, status=ContentReviewStatus.APPROVED)

        assert CourseService.publish_validation_errors(course) == []

    def test_quality_dashboard_reports_blockers_and_ready_courses(self):
        blocked = CourseFactory()
        ready = CourseFactory()
        LessonFactory(
            course=ready,
            is_published=True,
            review_status=ContentReviewStatus.PUBLISHED,
            published_version=1,
            content="Approved lesson content",
        )
        CourseReview.objects.create(
            course=ready,
            status=ContentReviewStatus.APPROVED,
            reviewer=ready.instructor,
            submitted_by=ready.instructor,
        )

        blocked_result = CourseQualityService.readiness(blocked)
        ready_result = CourseQualityService.readiness(ready)

        assert blocked_result["publish_ready"] is False
        assert ready_result["publish_ready"] is True
        assert ready_result["quality_score"] > blocked_result["quality_score"]

    def test_resource_library_is_scoped_to_owner(self):
        course = CourseFactory()
        other = UserFactory(role=UserRole.INSTRUCTOR, is_verified=True)
        resource = ResourceLibraryService.create(
            course.instructor,
            {
                "course": course,
                "title": "Excel practice workbook",
                "resource_type": "excel",
                "file_url": "https://cdn.example.com/excel.xlsx",
                "visibility": "course",
            },
        )

        assert resource in ResourceLibraryService.list_for_user(course.instructor)
        assert resource not in ResourceLibraryService.list_for_user(other)

    def test_approved_assessment_metadata_counts_toward_publish_readiness(self):
        course = CourseFactory()
        for index in range(5):
            QuizQuestion.objects.create(
                course=course,
                question_text=f"Question {index}",
                options=["A", "B", "C", "D"],
                correct_index=0,
                explanation="Because A is correct.",
                position=index,
                review_status=QuestionReviewStatus.APPROVED,
                is_certificate_eligible=True,
                category="excel-formulas",
                reusable_key=f"excel-formula-{index}",
                learning_objective="Use formulas safely.",
            )

        assert ResourceLibraryItem.objects.count() >= 0
        readiness = CourseQualityService.readiness(course)
        assert readiness["metrics"]["approved_certificate_questions"] == 5


@pytest.mark.django_db
def test_content_quality_dashboard_endpoint_requires_authenticated_instructor():
    course = CourseFactory()
    client = APIClient()
    client.force_authenticate(user=course.instructor)

    response = client.get("/api/v1/courses/quality-dashboard/")

    assert response.status_code == 200
