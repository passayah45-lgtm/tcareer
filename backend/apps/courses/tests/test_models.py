import pytest
from apps.courses.models import Course, CourseStatus, EnrollmentStatus
from apps.courses.tests.factories import (
    CourseFactory, PublishedCourseFactory, LessonFactory,
    EnrollmentFactory, LessonProgressFactory,
)
from apps.users.tests.factories import InstructorFactory


@pytest.mark.django_db
class TestCourseModel:

    def test_course_slug_auto_generated(self):
        course = CourseFactory(title="Python for Beginners")
        assert course.slug == "python-for-beginners"

    def test_course_slug_deduplication(self):
        CourseFactory(title="Python Course")
        course2 = CourseFactory(title="Python Course")
        assert course2.slug == "python-course-1"

    def test_course_is_published_property(self):
        draft = CourseFactory(status=CourseStatus.DRAFT)
        published = PublishedCourseFactory()
        assert draft.is_published is False
        assert published.is_published is True

    def test_course_is_free_property(self):
        from decimal import Decimal
        free = CourseFactory(price=Decimal("0.00"))
        paid = CourseFactory(price=Decimal("19.99"))
        assert free.is_free is True
        assert paid.is_free is False

    def test_course_total_lessons(self):
        course = CourseFactory()
        LessonFactory(course=course, is_published=True)
        LessonFactory(course=course, is_published=True)
        LessonFactory(course=course, is_published=False)
        assert course.total_lessons == 2

    def test_course_str(self):
        course = CourseFactory(title="Test Course")
        assert str(course) == "Test Course"


@pytest.mark.django_db
class TestEnrollmentModel:

    def test_enrollment_is_active(self):
        enrollment = EnrollmentFactory(status=EnrollmentStatus.ACTIVE)
        assert enrollment.is_active is True
        assert enrollment.is_completed is False

    def test_enrollment_is_completed(self):
        enrollment = EnrollmentFactory(status=EnrollmentStatus.COMPLETED)
        assert enrollment.is_completed is True
        assert enrollment.is_active is False

    def test_enrollment_unique_per_user_course(self):
        enrollment = EnrollmentFactory()
        with pytest.raises(Exception):
            EnrollmentFactory(user=enrollment.user, course=enrollment.course)
