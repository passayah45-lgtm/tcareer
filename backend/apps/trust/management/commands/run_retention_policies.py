from __future__ import annotations

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.ai_platform.models import (
    AIEvaluationResult,
    AIEvaluationRun,
    AIFeedback,
    AIRequest,
    AIUsage,
    RetrievalEvent,
)
from apps.analytics.models import AnalyticsEvent
from apps.audit.models import AuditLog
from apps.notifications.models import EmailDelivery, Notification
from apps.organizations.models import BulkImportJob, DataExportJob
from common.audit import AuditService


class Command(BaseCommand):
    help = "Run configurable retention policies. Dry-run/report-only unless --delete is provided."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Report eligible records without changing data."
        )
        parser.add_argument(
            "--data-type",
            choices=list(self.policy_registry().keys()),
            help="Run one retention policy.",
        )
        parser.add_argument(
            "--organization-id", help="Limit organization-scoped data where supported."
        )
        parser.add_argument(
            "--limit", type=int, default=1000, help="Maximum rows to act on per data type."
        )
        parser.add_argument(
            "--archive", action="store_true", help="Mark/archive where supported before delete."
        )
        parser.add_argument(
            "--delete", action="store_true", help="Delete eligible non-append-only records."
        )
        parser.add_argument(
            "--fail-on-warning",
            action="store_true",
            help="Return non-zero when warnings are present.",
        )
        parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    def handle(self, *args, **options):
        policies = self.policy_registry()
        selected = [options["data_type"]] if options.get("data_type") else list(policies.keys())
        dry_run = options["dry_run"] or not options["delete"]
        results = [
            self.run_policy(
                name=name,
                policy=policies[name],
                dry_run=dry_run,
                do_delete=options["delete"],
                do_archive=options["archive"],
                organization_id=options.get("organization_id") or "",
                limit=options["limit"],
            )
            for name in selected
        ]
        status = self.overall_status(results, fail_on_warning=options["fail_on_warning"])
        report = {"status": status, "dry_run": dry_run, "results": results}

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, default=str))
        else:
            for item in results:
                style = self.style.SUCCESS
                if item["status"] == "warn":
                    style = self.style.WARNING
                elif item["status"] == "fail":
                    style = self.style.ERROR
                message = (
                    f"{item['data_type']}: {item['status']} - "
                    f"eligible={item['eligible_count']}, "
                    f"archived={item['archived_count']}, "
                    f"deleted={item['deleted_count']} - {item['detail']}"
                )
                self.stdout.write(style(message))
            self.stdout.write(self.style.SUCCESS(f"Retention policy status: {status}"))

        if status == "fail":
            raise CommandError("Retention policies failed.")

    @staticmethod
    def overall_status(results, *, fail_on_warning: bool) -> str:
        if any(item["status"] == "fail" for item in results):
            return "fail"
        if any(item["status"] == "warn" for item in results):
            return "fail" if fail_on_warning else "warn"
        return "ok"

    @staticmethod
    def policy_registry():
        return {
            "audit_logs": {
                "model": AuditLog,
                "days": "AUDIT_RETENTION_DAYS",
                "date_field": "created_at",
                "append_only": True,
            },
            "analytics_events": {
                "model": AnalyticsEvent,
                "days": "RETENTION_ANALYTICS_EVENTS_DAYS",
                "date_field": "occurred_at",
            },
            "notifications": {
                "model": Notification,
                "days": "RETENTION_NOTIFICATIONS_DAYS",
                "date_field": "created_at",
            },
            "email_deliveries": {
                "model": EmailDelivery,
                "days": "RETENTION_EMAIL_DELIVERIES_DAYS",
                "date_field": "created_at",
            },
            "ai_requests": {
                "model": AIRequest,
                "days": "RETENTION_AI_REQUESTS_DAYS",
                "date_field": "created_at",
            },
            "ai_usage": {
                "model": AIUsage,
                "days": "RETENTION_AI_USAGE_DAYS",
                "date_field": "period_date",
            },
            "ai_feedback": {
                "model": AIFeedback,
                "days": "RETENTION_AI_FEEDBACK_DAYS",
                "date_field": "created_at",
            },
            "ai_evaluations": {
                "model": AIEvaluationRun,
                "days": "RETENTION_AI_EVALUATIONS_DAYS",
                "date_field": "created_at",
            },
            "ai_evaluation_results": {
                "model": AIEvaluationResult,
                "days": "RETENTION_AI_EVALUATIONS_DAYS",
                "date_field": "created_at",
            },
            "rag_retrieval_logs": {
                "model": RetrievalEvent,
                "days": "RETENTION_RAG_RETRIEVAL_DAYS",
                "date_field": "created_at",
            },
            "export_files": {
                "model": DataExportJob,
                "days": "RETENTION_EXPORT_FILES_DAYS",
                "date_field": "created_at",
                "organization_field": "organization_id",
                "legal_hold": True,
            },
            "import_files": {
                "model": BulkImportJob,
                "days": "RETENTION_IMPORT_FILES_DAYS",
                "date_field": "created_at",
                "organization_field": "organization_id",
            },
            "failed_worker_jobs": {
                "model": DataExportJob,
                "days": "RETENTION_FAILED_WORKER_JOBS_DAYS",
                "date_field": "failed_at",
                "organization_field": "organization_id",
                "failed_only": True,
            },
        }

    def run_policy(self, *, name, policy, dry_run, do_delete, do_archive, organization_id, limit):
        model = policy["model"]
        days = int(
            getattr(settings, policy["days"], getattr(settings, "RETENTION_DEFAULT_DAYS", 365)) or 0
        )
        if name == "audit_logs" and not getattr(settings, "AUDIT_RETENTION_ENABLED", False):
            return self.result(
                name, "warn", 0, 0, 0, "audit retention disabled; append-only logs retained"
            )
        if days <= 0:
            return self.result(name, "warn", 0, 0, 0, "retention days not configured")

        cutoff = timezone.now() - timezone.timedelta(days=days)
        date_field = policy["date_field"]
        lookup = {f"{date_field}__lt": cutoff}
        queryset = model.objects.filter(**lookup)

        if policy.get("organization_field") and organization_id:
            queryset = queryset.filter(**{policy["organization_field"]: organization_id})
        if policy.get("legal_hold"):
            queryset = queryset.filter(legal_hold=False)
        if policy.get("failed_only"):
            queryset = queryset.filter(status="failed")

        eligible_count = queryset.count()
        ids = list(queryset.order_by(date_field).values_list("id", flat=True)[:limit])

        if dry_run or not ids:
            detail = "dry run" if dry_run else "no eligible records"
            return self.result(name, "ok", eligible_count, 0, 0, detail, cutoff=cutoff)

        if policy.get("append_only"):
            return self.result(
                name,
                "warn",
                eligible_count,
                0,
                0,
                "append-only data cannot be deleted by this command",
                cutoff=cutoff,
            )

        archived_count = 0
        deleted_count = 0
        with transaction.atomic():
            target_qs = model.objects.filter(id__in=ids)
            if do_archive and hasattr(model, "deleted_at"):
                archived_count = target_qs.update(deleted_at=timezone.now())
            if do_delete:
                deleted_count, _ = target_qs.delete()
            AuditService.record(
                action="retention_policy_executed",
                target_type=name,
                target_id="batch",
                metadata={
                    "data_type": name,
                    "eligible_count": eligible_count,
                    "archived_count": archived_count,
                    "deleted_count": deleted_count,
                    "limit": limit,
                    "cutoff": cutoff.isoformat(),
                },
            )

        return self.result(
            name, "ok", eligible_count, archived_count, deleted_count, "completed", cutoff=cutoff
        )

    @staticmethod
    def result(data_type, status, eligible_count, archived_count, deleted_count, detail, **extra):
        return {
            "data_type": data_type,
            "status": status,
            "eligible_count": eligible_count,
            "archived_count": archived_count,
            "deleted_count": deleted_count,
            "detail": detail,
            **extra,
        }
