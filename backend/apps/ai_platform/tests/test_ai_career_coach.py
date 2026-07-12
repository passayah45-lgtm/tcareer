import pytest
from django.urls import reverse

from apps.ai_platform.models import (
    AIBudgetPolicy,
    AICareerAssessment,
    AICareerCoachingSummary,
    AICareerGoal,
    AICareerRoadmap,
    AICareerSkillGap,
    AIFeatureFlag,
)
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def test_career_assessment_roadmap_skill_gap_and_weekly_coaching(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    goal_response = api_client.post(
        reverse("ai_platform:career-goals"),
        {"target_role": "Data Analyst", "target_industry": "Technology", "target_country": "US"},
        format="json",
    )
    assert goal_response.status_code == 201

    goal_id = goal_response.data["id"]
    assessment = api_client.post(reverse("ai_platform:career-assessment"), {"goal_id": goal_id, "current_skills": ["python"]}, format="json")
    roadmap = api_client.post(reverse("ai_platform:career-roadmap"), {"goal_id": goal_id, "horizon": "6_months", "skills": ["python", "sql"]}, format="json")
    gap = api_client.post(reverse("ai_platform:career-skill-gap"), {"goal_id": goal_id, "desired_skills": ["python", "sql", "statistics"]}, format="json")
    coaching = api_client.post(reverse("ai_platform:career-weekly-coaching"), {"goal_id": goal_id, "achievements": ["Finished SQL lesson"]}, format="json")

    assert assessment.status_code == 201
    assert roadmap.status_code == 201
    assert gap.status_code == 201
    assert coaching.status_code == 201
    assert AICareerAssessment.objects.filter(user=user).exists()
    assert AICareerRoadmap.objects.filter(user=user, horizon="6_months").exists()
    assert AICareerSkillGap.objects.filter(user=user).exists()
    assert AICareerCoachingSummary.objects.filter(user=user).exists()


def test_career_goal_update_history_and_analytics(api_client):
    user = UserFactory()
    goal = AICareerGoal.objects.create(user=user, title="Become Backend Engineer", target_role="Backend Engineer")
    api_client.force_authenticate(user=user)

    update = api_client.patch(reverse("ai_platform:career-goal-detail", args=[goal.id]), {"progress_percentage": 40}, format="json")
    history = api_client.get(reverse("ai_platform:career-history"))
    analytics = api_client.get(reverse("ai_platform:career-analytics"))

    assert update.status_code == 200
    assert update.data["progress_percentage"] == 40
    assert history.status_code == 200
    assert analytics.status_code == 200
    assert "active_goals" in analytics.data


def test_learning_recommendations_use_skill_gap(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("ai_platform:career-learning-recommendations"), {"target": "ML Engineer", "desired_skills": ["python", "machine learning"]}, format="json")

    assert response.status_code == 200
    assert "courses" in response.data
    assert AICareerSkillGap.objects.filter(user=user, target="ML Engineer").exists()


def test_career_goal_permissions(api_client):
    owner = UserFactory()
    other = UserFactory()
    goal = AICareerGoal.objects.create(user=owner, title="Become Product Manager", target_role="Product Manager")
    api_client.force_authenticate(user=other)

    response = api_client.patch(reverse("ai_platform:career-goal-detail", args=[goal.id]), {"progress_percentage": 90}, format="json")

    assert response.status_code == 403


def test_career_coach_feature_flag_and_budget_enforced(api_client):
    user = UserFactory()
    AIFeatureFlag.objects.create(feature="career_advice", user=user, is_enabled=False, reason="test")
    api_client.force_authenticate(user=user)

    disabled = api_client.post(reverse("ai_platform:career-assessment"), {"current_skills": ["python"]}, format="json")
    assert disabled.status_code == 403

    AIFeatureFlag.objects.filter(user=user, feature="career_advice").delete()
    AIBudgetPolicy.objects.create(scope="user", user=user, feature="career_advice", daily_request_limit=0, is_active=True)
    blocked = api_client.post(reverse("ai_platform:career-assessment"), {"current_skills": ["python"]}, format="json")

    assert blocked.status_code == 403
