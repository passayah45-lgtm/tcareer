import pytest
from django.urls import reverse

from apps.ai_platform.models import (
    AIBudgetPolicy,
    AIFeature,
    AIFeatureFlag,
    AIGeneratedQuiz,
    AILearningTutorSession,
    AILessonIntelligence,
    AIQuizFeedback,
    AIStudyPlan,
    AIRequest,
)
from apps.assessments.models import QuizAttempt
from apps.courses.tests.factories import EnrollmentFactory, LessonFactory, PublishedCourseFactory
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def learning_setup():
    course = PublishedCourseFactory(
        title="Python Data Foundations",
        tags=["Python", "Data"],
        requirements=["Basic computer literacy"],
        what_you_learn=["Write Python scripts", "Analyze data"],
    )
    lesson = LessonFactory(course=course, title="Python variables", content="Variables store reusable values in Python.", is_published=True)
    enrollment = EnrollmentFactory(course=course)
    return enrollment.user, course, lesson, enrollment


def test_course_tutor_uses_ai_service_and_tracks_session(api_client, learning_setup):
    user, course, lesson, _ = learning_setup
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("ai_platform:learning-course-tutor"),
        {"course_id": str(course.id), "lesson_id": str(lesson.id), "question": "Explain variables", "mode": "explain"},
        format="json",
    )

    assert response.status_code == 201, response.json()
    payload = response.json()["data"]
    assert payload["mode"] == "explain"
    assert payload["answer"]
    assert AILearningTutorSession.objects.filter(user=user, course=course, lesson=lesson).exists()
    assert AIRequest.objects.filter(user=user, feature=AIFeature.COURSE_TUTOR).exists()


def test_lesson_intelligence_is_cached_and_can_regenerate(api_client, learning_setup):
    user, course, lesson, _ = learning_setup
    api_client.force_authenticate(user=user)

    first = api_client.post(reverse("ai_platform:learning-lesson-summary"), {"course_id": str(course.id), "lesson_id": str(lesson.id)}, format="json")
    second = api_client.post(reverse("ai_platform:learning-lesson-summary"), {"course_id": str(course.id), "lesson_id": str(lesson.id)}, format="json")
    regenerated = api_client.post(reverse("ai_platform:learning-lesson-summary"), {"course_id": str(course.id), "lesson_id": str(lesson.id), "regenerate": True}, format="json")

    assert first.status_code == 201
    assert second.status_code == 201
    assert regenerated.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert AILessonIntelligence.objects.filter(lesson=lesson, is_current=True).count() == 1


def test_study_plan_and_learning_analytics(api_client, learning_setup):
    user, _, _, _ = learning_setup
    api_client.force_authenticate(user=user)

    plan = api_client.post(
        reverse("ai_platform:learning-study-plan"),
        {"cadence": "weekly", "pace": "balanced", "available_minutes_per_day": 45},
        format="json",
    )
    history = api_client.get(reverse("ai_platform:learning-history"))
    analytics = api_client.get(reverse("ai_platform:learning-analytics"))

    assert plan.status_code == 201
    assert AIStudyPlan.objects.filter(user=user).exists()
    assert history.status_code == 200
    assert analytics.status_code == 200
    assert "ai_usage" in analytics.json()["data"]


def test_instructor_generates_reviewable_quiz_and_tools(api_client, learning_setup):
    _, course, lesson, _ = learning_setup
    instructor = course.instructor
    api_client.force_authenticate(user=instructor)

    quiz = api_client.post(
        reverse("ai_platform:learning-quiz-generation"),
        {"course_id": str(course.id), "lesson_id": str(lesson.id), "difficulty": "beginner", "number_of_questions": 4, "include_coding_foundation": True},
        format="json",
    )
    tool = api_client.post(
        reverse("ai_platform:learning-instructor-tools"),
        {"course_id": str(course.id), "lesson_id": str(lesson.id), "tool": "objectives"},
        format="json",
    )

    assert quiz.status_code == 201, quiz.json()
    assert len(quiz.json()["data"]["questions"]) == 4
    assert not quiz.json()["data"]["is_published_to_students"]
    assert AIGeneratedQuiz.objects.filter(course=course, lesson=lesson).exists()
    assert tool.status_code == 201
    assert "lesson_intelligence" in tool.json()["data"]


def test_quiz_feedback_for_attempt_owner(api_client, learning_setup):
    user, course, _, enrollment = learning_setup
    attempt = QuizAttempt.objects.create(enrollment=enrollment, answers={}, score=1, total_questions=2, percentage=50, passed=False)
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("ai_platform:learning-quiz-feedback"),
        {"course_id": str(course.id), "attempt_id": str(attempt.id)},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["data"]["weak_topics"] == ["Python", "Data"]
    assert AIQuizFeedback.objects.filter(user=user, quiz_attempt=attempt).exists()


def test_learning_permissions_feature_flag_and_budget(api_client, learning_setup):
    user, course, lesson, _ = learning_setup
    outsider = UserFactory()
    api_client.force_authenticate(user=outsider)

    denied = api_client.post(
        reverse("ai_platform:learning-course-tutor"),
        {"course_id": str(course.id), "lesson_id": str(lesson.id), "question": "Help"},
        format="json",
    )
    assert denied.status_code == 403

    api_client.force_authenticate(user=user)
    AIFeatureFlag.objects.create(feature=AIFeature.COURSE_TUTOR, user=user, is_enabled=False)
    disabled = api_client.post(
        reverse("ai_platform:learning-course-tutor"),
        {"course_id": str(course.id), "lesson_id": str(lesson.id), "question": "Help"},
        format="json",
    )
    assert disabled.status_code == 403

    AIFeatureFlag.objects.filter(user=user).delete()
    AIBudgetPolicy.objects.create(scope="user", user=user, feature=AIFeature.COURSE_TUTOR, daily_request_limit=0)
    over_budget = api_client.post(
        reverse("ai_platform:learning-course-tutor"),
        {"course_id": str(course.id), "lesson_id": str(lesson.id), "question": "Help"},
        format="json",
    )
    assert over_budget.status_code == 403
