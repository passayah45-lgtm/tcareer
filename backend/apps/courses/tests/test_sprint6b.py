import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import QuizQuestion
from apps.courses.models import ContentReviewStatus, LessonType
from apps.courses.tests.factories import CourseFactory, LessonFactory
from apps.users.tests.factories import InstructorFactory, UserFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def instructor(db):
    return InstructorFactory()


@pytest.fixture
def other_instructor(db):
    return InstructorFactory()


@pytest.fixture
def student(db):
    return UserFactory()


@pytest.fixture
def instructor_client(client, instructor):
    client.force_authenticate(user=instructor)
    return client


@pytest.fixture
def other_instructor_client(client, other_instructor):
    client.force_authenticate(user=other_instructor)
    return client


@pytest.fixture
def student_client(client, student):
    client.force_authenticate(user=student)
    return client


@pytest.fixture
def course(db, instructor):
    return CourseFactory(instructor=instructor)


@pytest.fixture
def course_with_lessons(db, instructor):
    course = CourseFactory(instructor=instructor)
    lessons = [LessonFactory(course=course, position=(i + 1) * 10) for i in range(4)]
    return course, lessons


@pytest.fixture
def course_with_questions(db, instructor):
    course = CourseFactory(instructor=instructor)
    questions = [
        QuizQuestion.objects.create(
            course=course,
            question_text="Question " + str(i) + "?",
            options=["A", "B", "C", "D"],
            correct_index=0,
            position=i * 10,
        )
        for i in range(1, 4)
    ]
    return course, questions


@pytest.mark.django_db
class TestLessonReorderEndpoint:
    def url(self, course_id):
        return "/api/v1/courses/" + str(course_id) + "/lessons/reorder/"

    def test_reorder_success(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        payload = {
            "lessons": [
                {"id": str(lessons[3].id), "position": 10},
                {"id": str(lessons[2].id), "position": 20},
                {"id": str(lessons[1].id), "position": 30},
                {"id": str(lessons[0].id), "position": 40},
            ]
        }
        r = instructor_client.post(self.url(course.id), payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()["data"]
        assert len(data) == 4
        assert data[0]["id"] == str(lessons[3].id)

    def test_reorder_updates_db(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        payload = {
            "lessons": [
                {"id": str(lessons[0].id), "position": 100},
                {"id": str(lessons[1].id), "position": 200},
                {"id": str(lessons[2].id), "position": 300},
                {"id": str(lessons[3].id), "position": 400},
            ]
        }
        instructor_client.post(self.url(course.id), payload, format="json")
        lessons[0].refresh_from_db()
        assert lessons[0].position == 100

    def test_unauthenticated_rejected(self, client, course_with_lessons):
        course, lessons = course_with_lessons
        r = client.post(self.url(course.id), {"lessons": []}, format="json")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_forbidden(self, student_client, course_with_lessons):
        course, lessons = course_with_lessons
        r = student_client.post(self.url(course.id), {"lessons": []}, format="json")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_wrong_instructor_forbidden(self, other_instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        payload = {
            "lessons": [
                {"id": str(lesson.id), "position": index * 10}
                for index, lesson in enumerate(lessons)
            ]
        }
        r = other_instructor_client.post(self.url(course.id), payload, format="json")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_missing_lessons_rejected(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        payload = {
            "lessons": [
                {"id": str(lessons[0].id), "position": 10},
                {"id": str(lessons[1].id), "position": 20},
                {"id": str(lessons[2].id), "position": 30},
            ]
        }
        r = instructor_client.post(self.url(course.id), payload, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_positions_rejected(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        payload = {
            "lessons": [
                {"id": str(lessons[0].id), "position": 10},
                {"id": str(lessons[1].id), "position": 10},
                {"id": str(lessons[2].id), "position": 30},
                {"id": str(lessons[3].id), "position": 40},
            ]
        }
        r = instructor_client.post(self.url(course.id), payload, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_unknown_lesson_ids_rejected(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        payload = {
            "lessons": [
                {"id": str(lessons[0].id), "position": 10},
                {"id": str(lessons[1].id), "position": 20},
                {"id": str(lessons[2].id), "position": 30},
                {"id": str(uuid.uuid4()), "position": 40},
            ]
        }
        r = instructor_client.post(self.url(course.id), payload, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLessonInlineUpdateEndpoint:
    def url(self, lesson_id):
        return "/api/v1/courses/lessons/" + str(lesson_id) + "/"

    def test_update_title(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        r = instructor_client.patch(self.url(lessons[0].id), {"title": "New title"}, format="json")
        assert r.status_code == status.HTTP_200_OK
        assert r.json()["data"]["title"] == "New title"
        lessons[0].refresh_from_db()
        assert lessons[0].title == "New title"

    def test_update_content(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        r = instructor_client.patch(
            self.url(lessons[0].id), {"content": "New content here"}, format="json"
        )
        assert r.status_code == status.HTTP_200_OK
        lessons[0].refresh_from_db()
        assert lessons[0].content == "New content here"

    def test_update_free_preview(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        r = instructor_client.patch(
            self.url(lessons[0].id), {"is_free_preview": True}, format="json"
        )
        assert r.status_code == status.HTTP_200_OK
        lessons[0].refresh_from_db()
        assert lessons[0].is_free_preview is True

    def test_position_ignored(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        original = lessons[0].position
        instructor_client.patch(self.url(lessons[0].id), {"position": 999}, format="json")
        lessons[0].refresh_from_db()
        assert lessons[0].position == original

    def test_unauthenticated_rejected(self, client, course_with_lessons):
        course, lessons = course_with_lessons
        r = client.patch(self.url(lessons[0].id), {"title": "X"}, format="json")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_wrong_instructor_forbidden(self, other_instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        r = other_instructor_client.patch(self.url(lessons[0].id), {"title": "X"}, format="json")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden(self, student_client, course_with_lessons):
        course, lessons = course_with_lessons
        r = student_client.patch(self.url(lessons[0].id), {"title": "X"}, format="json")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_nonexistent_lesson_404(self, instructor_client):
        r = instructor_client.patch(
            "/api/v1/courses/lessons/" + str(uuid.uuid4()) + "/", {"title": "X"}, format="json"
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_publish_text_lesson(self, instructor_client, course_with_lessons):
        course, lessons = course_with_lessons
        text = LessonFactory(
            course=course,
            lesson_type=LessonType.TEXT,
            is_published=False,
            position=50,
            review_status=ContentReviewStatus.APPROVED,
        )
        r = instructor_client.patch(self.url(text.id), {"is_published": True}, format="json")
        assert r.status_code == status.HTTP_200_OK
        text.refresh_from_db()
        assert text.is_published is True


@pytest.mark.django_db
class TestQuizBulkCreateEndpoint:
    def url(self, course_id):
        return "/api/v1/assessments/" + str(course_id) + "/questions/bulk/"

    def q(self, text="What is Python?"):
        if len(text) < 5:
            text = text + " here"
        return {
            "question_text": text,
            "options": ["A language", "A snake", "A tool", "An IDE"],
            "correct_index": 0,
        }

    def test_bulk_create_success(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id),
            {"questions": [self.q("Q1?"), self.q("Q2?")], "replace": False},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        data = r.json()["data"]
        assert data["total"] == 2
        assert len(data["questions"]) == 2

    def test_persists_to_db(self, instructor_client, course):
        instructor_client.post(
            self.url(course.id),
            {"questions": [self.q("Q1?"), self.q("Q2?")], "replace": False},
            format="json",
        )
        assert QuizQuestion.objects.filter(course=course).count() == 2

    def test_append_by_default(self, instructor_client, course_with_questions):
        course, _ = course_with_questions
        instructor_client.post(
            self.url(course.id), {"questions": [self.q("New?")], "replace": False}, format="json"
        )
        assert QuizQuestion.objects.filter(course=course).count() == 4

    def test_replace_deletes_existing(self, instructor_client, course_with_questions):
        course, _ = course_with_questions
        r = instructor_client.post(
            self.url(course.id), {"questions": [self.q("Only?")], "replace": True}, format="json"
        )
        assert r.status_code == status.HTTP_201_CREATED
        data = r.json()["data"]
        assert data["total"] == 1
        assert QuizQuestion.objects.filter(course=course).count() == 1

    def test_wrong_instructor_forbidden(self, other_instructor_client, course):
        r = other_instructor_client.post(
            self.url(course.id), {"questions": [self.q()], "replace": False}, format="json"
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_student_forbidden(self, student_client, course):
        r = student_client.post(
            self.url(course.id), {"questions": [self.q()], "replace": False}, format="json"
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_rejected(self, client, course):
        r = client.post(self.url(course.id), {"questions": [], "replace": False}, format="json")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_questions_rejected(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id), {"questions": [], "replace": False}, format="json"
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_too_many_questions_rejected(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id),
            {"questions": [self.q("Q" + str(i) + "?") for i in range(51)], "replace": False},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_correct_index(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id),
            {
                "questions": [
                    {"question_text": "Which?", "options": ["A", "B", "C", "D"], "correct_index": 5}
                ],
                "replace": False,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_correct_index_beyond_options(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id),
            {
                "questions": [
                    {"question_text": "Which?", "options": ["A", "B"], "correct_index": 3}
                ],
                "replace": False,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_single_option_rejected(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id),
            {
                "questions": [{"question_text": "Which?", "options": ["Only"], "correct_index": 0}],
                "replace": False,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_short_question_text_rejected(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id),
            {
                "questions": [
                    {"question_text": "OK", "options": ["A", "B", "C", "D"], "correct_index": 0}
                ],
                "replace": False,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_positions_auto_assigned(self, instructor_client, course):
        r = instructor_client.post(
            self.url(course.id),
            {"questions": [self.q("Q1?"), self.q("Q2?"), self.q("Q3?")], "replace": False},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        qs = list(QuizQuestion.objects.filter(course=course).order_by("position"))
        assert qs[0].position == 0
        assert qs[1].position == 10
        assert qs[2].position == 20


@pytest.mark.django_db
class TestQuizQuestionReorderEndpoint:
    def url(self, course_id):
        return "/api/v1/assessments/" + str(course_id) + "/questions/reorder/"

    def test_reorder_success(self, instructor_client, course_with_questions):
        course, questions = course_with_questions
        payload = {
            "questions": [
                {"id": str(questions[2].id), "position": 10},
                {"id": str(questions[1].id), "position": 20},
                {"id": str(questions[0].id), "position": 30},
            ]
        }
        r = instructor_client.post(self.url(course.id), payload, format="json")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()["data"]
        assert data["questions"][0]["id"] == str(questions[2].id)

    def test_wrong_instructor_forbidden(self, other_instructor_client, course_with_questions):
        course, questions = course_with_questions
        r = other_instructor_client.post(
            self.url(course.id),
            {"questions": [{"id": str(questions[0].id), "position": 10}]},
            format="json",
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_unknown_question_id(self, instructor_client, course_with_questions):
        course, _ = course_with_questions
        r = instructor_client.post(
            self.url(course.id),
            {"questions": [{"id": str(uuid.uuid4()), "position": 10}]},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_list_rejected(self, instructor_client, course_with_questions):
        course, _ = course_with_questions
        r = instructor_client.post(self.url(course.id), {"questions": []}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST
