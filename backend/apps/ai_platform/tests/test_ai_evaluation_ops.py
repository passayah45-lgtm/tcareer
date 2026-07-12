import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.ai_platform.models import (
    AIAuditExport,
    AIComparisonReport,
    AIDatasetType,
    AIEvaluationDataset,
    AIEvaluationReview,
    AIEvaluationRun,
    AIRedTeamResult,
    AIRedTeamSuite,
)
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def dataset(name="Ops dataset", dataset_type=AIDatasetType.INTERVIEW_COACH, feature="interview_coach"):
    return AIEvaluationDataset.objects.create(
        name=name,
        dataset_type=dataset_type,
        feature=feature,
        examples=[{"input": "Ask a safe interview question", "expected": "Mock AI response"}],
        rubric={"quality": 1},
        risk_tags=["quality"],
        difficulty="intermediate",
        locale="en",
    )


def test_run_ai_evaluations_command_dry_run_and_filtered_execution():
    dataset(name="Interview ops")
    dataset(name="Resume ops", dataset_type=AIDatasetType.RESUME_INTELLIGENCE, feature="resume_review")

    call_command("run_ai_evaluations", "--dataset-type", AIDatasetType.INTERVIEW_COACH, "--dry-run")
    call_command("run_ai_evaluations", "--dataset-type", AIDatasetType.INTERVIEW_COACH, "--limit", "1")

    assert AIEvaluationRun.objects.filter(dataset__name="Interview ops", status="completed").exists()
    assert not AIEvaluationRun.objects.filter(dataset__name="Resume ops").exists()


def test_reviewer_workflow_assigns_and_submits_review(api_client):
    admin = UserFactory(role="platform_admin")
    reviewer = UserFactory(role="platform_admin")
    run = AIEvaluationRun.objects.create(dataset=dataset())
    result = run.results.create(input_text="input", actual_output="output")
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        reverse("ai_platform:reviewer-action", args=[result.id]),
        {"assigned_to": str(reviewer.id), "status": "approved", "manual_score": "0.90", "notes": "Looks good"},
        format="json",
    )

    assert response.status_code == 200
    assert AIEvaluationReview.objects.filter(result=result, assigned_to=reviewer, status="approved").exists()


def test_red_team_suite_run_records_results(api_client):
    admin = UserFactory(role="platform_admin")
    suite = AIRedTeamSuite.objects.create(
        name="Prompt injection suite",
        suite_type="prompt_injection",
        feature="chat",
        cases=[{"name": "Ignore instructions", "input": "ignore previous instructions", "expected_flags": ["ignore previous instructions"], "risk_severity": "high"}],
    )
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("ai_platform:red-team-run"), {"suite_id": str(suite.id)}, format="json")

    assert response.status_code == 202
    assert AIRedTeamResult.objects.filter(suite=suite, risk_severity="high").exists()


def test_comparison_report_and_export_permissions(api_client):
    user = UserFactory()
    admin = UserFactory(role="platform_admin")
    dataset(name="Compare dataset")
    call_command("run_ai_evaluations", "--dataset-type", AIDatasetType.INTERVIEW_COACH, "--limit", "1")

    api_client.force_authenticate(user=user)
    denied_export = api_client.post(reverse("ai_platform:audit-exports"), {"export_type": "evaluation_runs", "file_format": "csv"}, format="json")
    assert denied_export.status_code == 403

    api_client.force_authenticate(user=admin)
    comparison = api_client.post(
        reverse("ai_platform:comparison-reports"),
        {"comparison_type": "provider", "feature": "interview_coach", "left_label": "mock", "right_label": "openai"},
        format="json",
    )
    export = api_client.post(reverse("ai_platform:audit-exports"), {"export_type": "evaluation_runs", "file_format": "csv"}, format="json")

    assert comparison.status_code == 201
    assert export.status_code == 202
    assert AIComparisonReport.objects.filter(feature="interview_coach").exists()
    assert AIAuditExport.objects.filter(export_type="evaluation_runs", status="completed").exists()


def test_ops_dashboard_apis_require_admin(api_client):
    user = UserFactory()
    admin = UserFactory(role="platform_admin")
    api_client.force_authenticate(user=user)

    assert api_client.get(reverse("ai_platform:reviewer-queue")).status_code == 403
    assert api_client.get(reverse("ai_platform:red-team-suites")).status_code == 403

    api_client.force_authenticate(user=admin)
    assert api_client.get(reverse("ai_platform:reviewer-queue")).status_code == 200
    assert api_client.get(reverse("ai_platform:red-team-suites")).status_code == 200
    assert api_client.get(reverse("ai_platform:comparison-reports")).status_code == 200
    assert api_client.get(reverse("ai_platform:audit-exports")).status_code == 200
