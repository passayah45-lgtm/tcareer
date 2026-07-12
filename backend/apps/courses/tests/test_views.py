import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.courses.models import CourseStatus, Enrollment
from apps.courses.tests.factories import (
    CourseFactory, PublishedCourseFactory, FreeCourseFactory,
    LessonFactory,
)
from apps.users.tests.factories import UserFactory, InstructorFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def student(db):
    return UserFactory()


@pytest.fixture
def instructor(db):
    return InstructorFactory()


@pytest.fixture
def student_client(client, student):
    client.force_authenticate(user=student)
    client.user = student
    return client


@pytest.fixture
def instructor_client(client, instructor):
    client.force_authenticate(user=instructor)
    client.user = instructor
    return client


def get_count(response):
    """Helper: extract count from paginated response meta."""
    j = response.json()
    return j.get("meta", {}).get("count", len(j.get("data", [])))


@pytest.mark.django_db
class TestCourseListEndpoint:

    def test_returns_published_courses_only(self, client):
        PublishedCourseFactory()
        PublishedCourseFactory()
        CourseFactory(status=CourseStatus.DRAFT)
        response = client.get(reverse("courses:course-list"))
        assert response.status_code == status.HTTP_200_OK
        assert get_count(response) == 2

    def test_filter_by_level(self, client):
        PublishedCourseFactory(level="beginner")
        PublishedCourseFactory(level="advanced")
        response = client.get(reverse("courses:course-list") + "?level=beginner")
        assert get_count(response) == 1

    def test_search_by_title(self, client):
        PublishedCourseFactory(title="Python Programming")
        PublishedCourseFactory(title="JavaScript Basics")
        response = client.get(reverse("courses:course-list") + "?search=Python")
        assert get_count(response) == 1

    def test_anonymous_access_allowed(self, client):
        response = client.get(reverse("courses:course-list"))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestCourseDetailEndpoint:

    def test_get_published_course(self, client):
        course = PublishedCourseFactory()
        response = client.get(reverse("courses:course-detail", kwargs={"slug": course.slug}))
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["title"] == course.title

    def test_draft_course_returns_404(self, client):
        course = CourseFactory(status=CourseStatus.DRAFT)
        response = client.get(reverse("courses:course-detail", kwargs={"slug": course.slug}))
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCourseCreateEndpoint:

    def test_instructor_can_create_course(self, instructor_client):
        response = instructor_client.post(
            reverse("courses:course-create"),
            {
                "title": "My New Course",
                "short_description": "A great course",
                "level": "beginner",
                "price": "0.00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["title"] == "My New Course"
        assert response.json()["data"]["status"] == "draft"

    def test_student_cannot_create_course(self, student_client):
        response = student_client.post(
            reverse("courses:course-create"),
            {"title": "Unauthorized Course"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create_course(self, client):
        response = client.post(
            reverse("courses:course-create"),
            {"title": "Unauthorized Course"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestEnrollmentEndpoint:

    def test_enroll_in_free_course(self, student_client):
        course = FreeCourseFactory()
        response = student_client.post(
            reverse("courses:enroll", kwargs={"course_id": course.id})
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Enrollment.objects.filter(
            user=student_client.user, course=course
        ).exists()

    def test_cannot_enroll_twice(self, student_client):
        course = FreeCourseFactory()
        student_client.post(reverse("courses:enroll", kwargs={"course_id": course.id}))
        response = student_client.post(
            reverse("courses:enroll", kwargs={"course_id": course.id})
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_my_enrollments_returns_list(self, student_client):
        course1 = FreeCourseFactory()
        course2 = FreeCourseFactory()
        student_client.post(reverse("courses:enroll", kwargs={"course_id": course1.id}))
        student_client.post(reverse("courses:enroll", kwargs={"course_id": course2.id}))
        response = student_client.get(reverse("courses:my-enrollments"))
        assert response.status_code == status.HTTP_200_OK
        assert get_count(response) == 2

    def test_unauthenticated_cannot_enroll(self, client):
        course = FreeCourseFactory()
        response = client.post(reverse("courses:enroll", kwargs={"course_id": course.id}))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProgressEndpoint:

    def test_update_progress(self, student_client):
        from apps.courses.services import EnrollmentService
        course = FreeCourseFactory()
        lesson = LessonFactory(course=course, is_published=True)
        EnrollmentService.enroll(student_client.user, course)
        response = student_client.post(
            reverse("courses:update-progress", kwargs={
                "course_id": course.id,
                "lesson_id": lesson.id,
            }),
            {"watch_percentage": 55, "last_position_seconds": 330},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["watch_percentage"] == 55

    def test_unenrolled_student_cannot_update_progress(self, student_client):
        course = FreeCourseFactory()
        lesson = LessonFactory(course=course, is_published=True)
        response = student_client.post(
            reverse("courses:update-progress", kwargs={
                "course_id": course.id,
                "lesson_id": lesson.id,
            }),
            {"watch_percentage": 50},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
