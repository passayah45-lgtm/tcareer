from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.notifications.models import EmailDeliveryService
from common.ops import validate_production_redis_settings


class Command(BaseCommand):
    help = "Run non-secret production readiness smoke checks."

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-warning", action="store_true", help="Return a non-zero exit code on warnings.")

    def handle(self, *args, **options):
        checks = [
            self.check_database(),
            self.check_cache(),
            self.check_migrations(),
            self.check_email(),
            self.check_storage(),
            self.check_critical_settings(),
            self.check_celery(),
        ]
        failures = [item for item in checks if item["status"] == "fail"]
        warnings = [item for item in checks if item["status"] == "warn"]
        for item in checks:
            style = self.style.SUCCESS
            if item["status"] == "warn":
                style = self.style.WARNING
            elif item["status"] == "fail":
                style = self.style.ERROR
            self.stdout.write(style(f"{item['name']}: {item['status']} - {item['detail']}"))
        if failures or (options["fail_on_warning"] and warnings):
            raise CommandError("Production smoke check failed.")
        self.stdout.write(self.style.SUCCESS("Production smoke check completed."))

    def check_database(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"name": "database", "status": "ok", "detail": "reachable"}

    def check_cache(self):
        errors = validate_production_redis_settings(settings)
        if errors:
            return {"name": "cache", "status": "fail", "detail": " ".join(errors)}
        cache.set("smoke:cache", "ok", timeout=15)
        if cache.get("smoke:cache") != "ok":
            return {"name": "cache", "status": "fail", "detail": "read/write failed"}
        return {"name": "cache", "status": "ok", "detail": settings.CACHES["default"]["BACKEND"].rsplit(".", 1)[-1]}

    def check_migrations(self):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            return {"name": "migrations", "status": "fail", "detail": f"{len(plan)} unapplied migrations"}
        return {"name": "migrations", "status": "ok", "detail": "no unapplied migrations"}

    def check_email(self):
        if EmailDeliveryService.smtp_configured():
            return {"name": "email", "status": "ok", "detail": "provider configured"}
        return {"name": "email", "status": "warn", "detail": "provider not configured for outbound send"}

    def check_storage(self):
        default_storage.get_available_name("smokecheck.tmp")
        return {"name": "storage", "status": "ok", "detail": default_storage.__class__.__name__}

    def check_critical_settings(self):
        missing = []
        if not settings.SECRET_KEY:
            missing.append("SECRET_KEY")
        if not settings.ALLOWED_HOSTS:
            missing.append("ALLOWED_HOSTS")
        if not getattr(settings, "DATABASES", {}).get("default"):
            missing.append("DATABASE_URL")
        if missing:
            return {"name": "critical_settings", "status": "fail", "detail": ", ".join(missing)}
        if not settings.DEBUG and not settings.SECURE_SSL_REDIRECT:
            return {"name": "critical_settings", "status": "warn", "detail": "SECURE_SSL_REDIRECT is disabled"}
        return {"name": "critical_settings", "status": "ok", "detail": "required settings present"}

    def check_celery(self):
        if not getattr(settings, "CELERY_BROKER_URL", ""):
            return {"name": "celery", "status": "warn", "detail": "broker not configured"}
        return {"name": "celery", "status": "ok", "detail": "broker configured"}
