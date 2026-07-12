import pytest
from django.urls import reverse

from apps.ai_platform.models import (
    AIBudgetPolicy,
    AIFeature,
    AIFeatureFlag,
    AIInterviewAnswerEvaluation,
    AIInterviewQuestion,
    AIInterviewSession,
    AIInterviewTemplate,
    AIRequest,
)
from apps.organizations.models import Organization, OrganizationMembership, OrganizationRole, OrganizationType
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def test_interview_session_lifecycle_uses_ai_service(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)

    created = api_client.post(
        reverse("ai_platform:interview-sessions"),
        {"session_type": "technical", "difficulty": "intermediate", "job_title": "Backend Django Developer", "skills": ["Python", "Django"]},
        format="json",
    )
    assert created.status_code == 201
    session_id = created.json()["data"]["id"]

    question = api_client.post(reverse("ai_platform:interview-next-question", args=[session_id]), {}, format="json")
    assert question.status_code == 201
    question_id = question.json()["data"]["id"]

    evaluation = api_client.post(
        reverse("ai_platform:interview-submit-answer", args=[session_id]),
        {"question_id": question_id, "answer_text": "I built a Django API, measured latency, and improved response time with clear impact."},
        format="json",
    )
    assert evaluation.status_code == 201
    assert evaluation.json()["data"]["overall_score"] > 0

    finished = api_client.post(reverse("ai_platform:interview-finish", args=[session_id]), {}, format="json")
    assert finished.status_code == 200
    assert finished.json()["data"]["status"] == "completed"
    assert AIRequest.objects.filter(user=user, feature=AIFeature.INTERVIEW_COACH).count() >= 3
    assert AIInterviewSession.objects.filter(user=user, overall_score__gt=0).exists()


def test_interview_history_detail_and_analytics(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    session = AIInterviewSession.objects.create(user=user, session_type="behavioral", overall_score=78)
    question = AIInterviewQuestion.objects.create(session=session, sequence=1, question_text="Tell me about yourself.")
    AIInterviewAnswerEvaluation.objects.create(session=session, question=question, answer_text="A structured answer", overall_score=78, clarity=80)

    history = api_client.get(reverse("ai_platform:interview-sessions"))
    detail = api_client.get(reverse("ai_platform:interview-session-detail", args=[session.id]))
    analytics = api_client.get(reverse("ai_platform:interview-analytics"))

    assert history.status_code == 200
    assert detail.status_code == 200
    assert analytics.status_code == 200
    assert analytics.json()["data"]["sessions"] == 1


def test_interview_sessions_are_private(api_client):
    owner = UserFactory()
    other = UserFactory()
    session = AIInterviewSession.objects.create(user=owner)
    api_client.force_authenticate(user=other)

    response = api_client.get(reverse("ai_platform:interview-session-detail", args=[session.id]))

    assert response.status_code == 403


def test_interview_feature_flag_and_budget_are_enforced(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    AIFeatureFlag.objects.create(feature=AIFeature.INTERVIEW_COACH, user=user, is_enabled=False)

    blocked_flag = api_client.post(reverse("ai_platform:interview-sessions"), {"job_title": "Analyst"}, format="json")
    assert blocked_flag.status_code == 201
    session_id = blocked_flag.json()["data"]["id"]
    denied = api_client.post(reverse("ai_platform:interview-next-question", args=[session_id]), {}, format="json")
    assert denied.status_code == 403

    AIFeatureFlag.objects.filter(user=user).update(is_enabled=True)
    AIBudgetPolicy.objects.create(scope="user", user=user, feature=AIFeature.INTERVIEW_COACH, daily_request_limit=0)
    over_budget = api_client.post(reverse("ai_platform:interview-next-question", args=[session_id]), {}, format="json")
    assert over_budget.status_code == 403


def test_interview_template_permissions(api_client):
    recruiter = UserFactory(role="recruiter")
    admin = UserFactory(role="company_admin")
    outsider = UserFactory()
    organization = Organization.objects.create(name="Interview Org", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(organization=organization, user=recruiter, role=OrganizationRole.RECRUITER)
    OrganizationMembership.objects.create(organization=organization, user=admin, role=OrganizationRole.COMPANY_ADMIN)

    api_client.force_authenticate(user=outsider)
    denied = api_client.post(
        reverse("ai_platform:interview-templates"),
        {"organization_id": str(organization.id), "title": "Django pack", "session_type": "technical"},
        format="json",
    )
    assert denied.status_code == 403

    api_client.force_authenticate(user=admin)
    created = api_client.post(
        reverse("ai_platform:interview-templates"),
        {"organization_id": str(organization.id), "title": "Django pack", "session_type": "technical", "skills": ["Django"]},
        format="json",
    )
    assert created.status_code == 201
    assert AIInterviewTemplate.objects.filter(organization=organization, title="Django pack").exists()

    api_client.force_authenticate(user=recruiter)
    listed = api_client.get(reverse("ai_platform:interview-templates"), {"organization_id": str(organization.id)})
    assert listed.status_code == 200
    assert listed.json()["data"][0]["title"] == "Django pack"
