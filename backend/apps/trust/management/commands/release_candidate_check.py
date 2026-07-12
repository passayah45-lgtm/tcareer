from __future__ import annotations

import json

from django.conf import settings
from django.core.cache import cache
from django.core.checks import run_checks
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.ai_platform.models import AIJobStatus, AIRequest, AIRequestStatus, KnowledgeDocument, KnowledgeIndexStatus, RetrievalEvaluationRun
from apps.notifications.models import EmailDelivery, EmailDeliveryStatus
from apps.organizations.models import BulkImportJob, DataExportJob, EnterpriseReportJob
from common.health import health_payload
from common.ops import release_metadata, validate_production_redis_settings


class Command(BaseCommand):
    help = "Run Version 1.0 release-candidate readiness checks without exposing secrets."

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-warning", action="store_true", help="Return a non-zero exit code on warnings.")
        parser.add_argument("--json", action="store_true", help="Emit a JSON report.")

    def handle(self, *args, **options):
        checks = [
            self.check_release_metadata(),
            self.check_django_system_checks(),
            self.check_migrations(),
            self.check_database(),
            self.check_cache(),
            self.check_storage(),
            self.check_email_configuration(),
            self.check_security_settings(),
            self.check_health_readiness(),
            self.check_background_work(),
            self.check_rag_freshness(),
            self.check_ai_failures(),
        ]

        report = {
            "status": self._overall_status(checks, fail_on_warning=options["fail_on_warning"]),
            "generated_at": timezone.now().isoformat(),
            "release": release_metadata(settings),
            "checks": checks,
        }

        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, default=str))
        else:
            for item in checks:
                style = self.style.SUCCESS
                if item["status"] == "warn":
                    style = self.style.WARNING
                elif item["status"] == "fail":
                    style = self.style.ERROR
                self.stdout.write(style(f"{item['name']}: {item['status']} - {item['detail']}"))
            self.stdout.write(self.style.SUCCESS(f"Release candidate check status: {report['status']}"))

        if report["status"] == "fail":
            raise CommandError("Release candidate check failed.")

    @staticmethod
    def _overall_status(checks, *, fail_on_warning: bool) -> str:
        if any(item["status"] == "fail" for item in checks):
            return "fail"
        if fail_on_warning and any(item["status"] == "warn" for item in checks):
            return "fail"
        if any(item["status"] == "warn" for item in checks):
            return "warn"
        return "ok"

    def ok(self, name: str, detail: str, **extra):
        return {"name": name, "status": "ok", "detail": detail, **extra}

    def warn(self, name: str, detail: str, **extra):
        return {"name": name, "status": "warn", "detail": detail, **extra}

    def fail(self, name: str, detail: str, **extra):
        return {"name": name, "status": "fail", "detail": detail, **extra}

    @staticmethod
    def _tables_exist(*table_names: str) -> bool:
        existing = set(connection.introspection.table_names())
        return all(table_name in existing for table_name in table_names)

    def check_release_metadata(self):
        metadata = release_metadata(settings)
        missing = [key for key in ["app_version", "api_version", "git_sha", "build_date", "environment"] if not metadata.get(key)]
        if missing:
            return self.warn("release_metadata", f"missing optional release metadata: {', '.join(missing)}", metadata=metadata)
        return self.ok("release_metadata", "safe release metadata present", metadata=metadata)

    def check_django_system_checks(self):
        issues = run_checks()
        errors = [issue for issue in issues if issue.is_serious()]
        if errors:
            return self.fail("django_system_checks", f"{len(errors)} serious issue(s)")
        if issues:
            return self.warn("django_system_checks", f"{len(issues)} warning(s)")
        return self.ok("django_system_checks", "no issues")

    def check_migrations(self):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            return self.fail("migrations", f"{len(plan)} unapplied migration(s)")
        return self.ok("migrations", "no unapplied migrations")

    def check_database(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return self.ok("database", "reachable")

    def check_cache(self):
        redis_errors = validate_production_redis_settings(settings)
        if redis_errors:
            return self.fail("cache", " ".join(redis_errors))
        cache.set("release-candidate:cache", "ok", timeout=15)
        if cache.get("release-candidate:cache") != "ok":
            return self.fail("cache", "read/write failed")
        backend = settings.CACHES["default"]["BACKEND"].rsplit(".", 1)[-1]
        return self.ok("cache", backend)

    def check_storage(self):
        default_storage.get_available_name("release-candidate-check.tmp")
        return self.ok("storage", default_storage.__class__.__name__)

    def check_email_configuration(self):
        backend = getattr(settings, "EMAIL_BACKEND", "")
        if not backend:
            return self.fail("email", "EMAIL_BACKEND is not configured")
        if settings.DEPLOY_ENVIRONMENT == "production" and "console" in backend:
            return self.warn("email", "console email backend configured in production")
        return self.ok("email", backend.rsplit(".", 1)[-1])

    def check_security_settings(self):
        warnings = []
        failures = []
        if settings.DEPLOY_ENVIRONMENT == "production":
            if settings.DEBUG:
                failures.append("DEBUG must be False")
            if not settings.ALLOWED_HOSTS:
                failures.append("ALLOWED_HOSTS is empty")
            if not settings.SECURE_SSL_REDIRECT:
                warnings.append("SECURE_SSL_REDIRECT is disabled")
            if not settings.SESSION_COOKIE_SECURE or not settings.CSRF_COOKIE_SECURE or not settings.AUTH_COOKIE_SECURE:
                warnings.append("secure cookies are not fully enabled")
            if getattr(settings, "EMAIL_WEBHOOK_ALLOW_SHARED_SECRET", False):
                failures.append("shared email webhook fallback must be disabled")
        if failures:
            return self.fail("security_settings", "; ".join(failures), warnings=warnings)
        if warnings:
            return self.warn("security_settings", "; ".join(warnings))
        return self.ok("security_settings", "release security settings acceptable")

    def check_health_readiness(self):
        payload = health_payload(include_dependencies=True)
        if payload["status"] != "ok":
            return self.fail("health_readiness", f"health status is {payload['status']}", checks=payload.get("checks", {}))
        return self.ok("health_readiness", "ready")

    def check_background_work(self):
        if not self._tables_exist("organization_data_export_jobs", "organization_bulk_import_jobs", "organization_enterprise_report_jobs", "email_deliveries"):
            return self.warn("background_work", "skipped because one or more background-work tables are missing; run migrations")
        failed_exports = DataExportJob.objects.filter(status=DataExportJob.Status.FAILED).count()
        failed_imports = BulkImportJob.objects.filter(status__in=[BulkImportJob.Status.FAILED, BulkImportJob.Status.FAILED_VALIDATION]).count()
        failed_reports = EnterpriseReportJob.objects.filter(status=EnterpriseReportJob.Status.FAILED).count()
        failed_emails = EmailDelivery.objects.filter(status=EmailDeliveryStatus.FAILED).count()
        pending_emails = EmailDelivery.objects.filter(status__in=[EmailDeliveryStatus.PENDING, EmailDeliveryStatus.QUEUED, EmailDeliveryStatus.RETRYING]).count()
        failures = failed_exports + failed_imports + failed_reports + failed_emails
        detail = (
            f"failed_exports={failed_exports}, failed_imports={failed_imports}, failed_reports={failed_reports}, "
            f"failed_emails={failed_emails}, pending_emails={pending_emails}"
        )
        if failures:
            return self.warn("background_work", detail)
        return self.ok("background_work", detail)

    def check_rag_freshness(self):
        if not self._tables_exist("ai_knowledge_documents"):
            return self.warn("rag_freshness", "skipped because ai_knowledge_documents is missing; run migrations")
        failed = KnowledgeDocument.objects.filter(index_status=KnowledgeIndexStatus.FAILED).count()
        stale = KnowledgeDocument.objects.filter(index_status=KnowledgeIndexStatus.STALE).count()
        queued = KnowledgeDocument.objects.filter(index_status=KnowledgeIndexStatus.QUEUED).count()
        detail = f"failed={failed}, stale={stale}, queued={queued}"
        if failed:
            return self.warn("rag_freshness", detail)
        if stale or queued:
            return self.warn("rag_freshness", detail)
        return self.ok("rag_freshness", detail)

    def check_ai_failures(self):
        if not self._tables_exist("ai_requests", "ai_retrieval_evaluation_runs"):
            return self.warn("ai_failures", "skipped because one or more AI tables are missing; run migrations")
        failed_requests = AIRequest.objects.filter(status=AIRequestStatus.FAILED).count()
        failed_retrieval_runs = RetrievalEvaluationRun.objects.filter(status=AIJobStatus.FAILED).count()
        detail = f"failed_requests={failed_requests}, failed_retrieval_evaluations={failed_retrieval_runs}"
        if failed_requests or failed_retrieval_runs:
            return self.warn("ai_failures", detail)
        return self.ok("ai_failures", detail)
