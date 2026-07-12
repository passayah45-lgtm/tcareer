import pytest
from apps.courses.models import CourseStatus, EnrollmentStatus
from apps.courses.services import CourseService, EnrollmentService, ProgressService
from apps.courses.tests.factories import (
    CourseFactory, PublishedCourseFactory, FreeCourseFactory,
    LessonFactory, EnrollmentFactory,
)
from apps.users.tests.factories import UserFactory, InstructorFactory
from common.exceptions import ServiceError, ConflictError, PermissionError


@pytest.mark.django_db
class TestCourseService:

    def test_get_published_courses_returns_only_published(self):
        PublishedCourseFactory()
        PublishedCourseFactory()
        CourseFactory(status=CourseStatus.DRAFT)
        courses = CourseService.get_published_courses()
        assert courses.count() == 2

    def test_get_published_courses_excludes_deleted(self):
        from django.utils import timezone
        PublishedCourseFactory()
        PublishedCourseFactory(deleted_at=timezone.now())
        courses = CourseService.get_published_courses()
        assert courses.count() == 1

    def test_publish_course_requires_lesson(self):
        course = CourseFactory(status=CourseStatus.DRAFT)
        with pytest.raises(ServiceError, match="at least one lesson"):
            CourseService.publish_course(course, course.instructor)

    def test_publish_course_success(self):
        course = CourseFactory(status=CourseStatus.DRAFT)
        LessonFactory(course=course, is_published=True)
        result = CourseService.publish_course(course, course.instructor)
        assert result.status == CourseStatus.PUBLISHED

    def test_publish_course_wrong_instructor(self):
        course = CourseFactory()
        LessonFactory(course=course, is_published=True)
        other = InstructorFactory()
        with pytest.raises(PermissionError):
            CourseService.publish_course(course, other)


@pytest.mark.django_db
class TestEnrollmentService:

    def test_enroll_free_course_success(self):
        user = UserFactory()
        course = FreeCourseFactory()
        enrollment = EnrollmentService.enroll(user, course)
        assert enrollment.status == EnrollmentStatus.ACTIVE
        assert enrollment.amount_paid == 0

    def test_enroll_duplicate_raises_conflict(self):
        user = UserFactory()
        course = FreeCourseFactory()
        EnrollmentService.enroll(user, course)
        with pytest.raises(ConflictError, match="already enrolled"):
            EnrollmentService.enroll(user, course)

    def test_enroll_draft_course_raises_error(self):
        user = UserFactory()
        course = CourseFactory(status=CourseStatus.DRAFT)
        with pytest.raises(ServiceError, match="not available"):
            EnrollmentService.enroll(user, course)

    def test_enroll_paid_course_without_subscription_raises_error(self):
        from decimal import Decimal
        user = UserFactory()
        course = PublishedCourseFactory(price=Decimal("19.99"))
        with pytest.raises(PermissionError, match="subscription"):
            EnrollmentService.enroll(user, course)


@pytest.mark.django_db
class TestProgressService:

    def test_update_progress_saves_percentage(self):
        enrollment = EnrollmentFactory()
        lesson = LessonFactory(course=enrollment.course)
        progress = ProgressService.update_progress(enrollment, lesson, 50, 300)
        assert progress.watch_percentage == 50
        assert progress.last_position_seconds == 300
        assert progress.is_completed is False

    def test_video_lesson_completes_at_90_percent(self):
        enrollment = EnrollmentFactory()
        lesson = LessonFactory(course=enrollment.course)
        progress = ProgressService.update_progress(enrollment, lesson, 90)
        assert progress.is_completed is True
        assert progress.completed_at is not None

    def test_progress_does_not_decrease(self):
        enrollment = EnrollmentFactory()
        lesson = LessonFactory(course=enrollment.course)
        ProgressService.update_progress(enrollment, lesson, 80)
        progress = ProgressService.update_progress(enrollment, lesson, 30)
        assert progress.watch_percentage == 80

    def test_all_lessons_complete_triggers_enrollment_completion(self):
        enrollment = EnrollmentFactory()
        lesson = LessonFactory(course=enrollment.course, is_published=True)
        ProgressService.update_progress(enrollment, lesson, 100)
        enrollment.refresh_from_db()
        assert enrollment.status == EnrollmentStatus.COMPLETED
        assert enrollment.completed_at is not None

    def test_get_course_progress_percentage(self):
        enrollment = EnrollmentFactory()
        lesson1 = LessonFactory(course=enrollment.course, is_published=True)
        lesson2 = LessonFactory(course=enrollment.course, is_published=True)
        ProgressService.update_progress(enrollment, lesson1, 100)
        result = ProgressService.get_course_progress(enrollment)
        assert result["total_lessons"] == 2
        assert result["completed_lessons"] == 1
        assert result["percentage"] == 50
