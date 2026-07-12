from __future__ import annotations

import json

from celery import current_app
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from apps.ai_platform.services import VectorBackendRegistry
from apps.notifications.models import EmailDeliveryService
from common.ops import release_metadata, validate_production_redis_settings


class Command(BaseCommand):
    help = "Validate production provider configuration without exposing secrets."

    PROVIDERS = ("email", "storage", "redis", "celery", "sentry", "stripe", "ai", "vector")

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Emit JSON output.")
        parser.add_argument(
            "--fail-on-warning", action="store_true", help="Return non-zero on warnings."
        )
        for provider in self.PROVIDERS:
            parser.add_argument(
                f"--{provider}", action="store_true", help=f"Check only {provider}."
            )

    def handle(self, *args, **options):
        selected = [name for name in self.PROVIDERS if options.get(name)] or list(self.PROVIDERS)
        checks = [getattr(self, f"check_{name}")() for name in selected]
        status = self.overall_status(checks, fail_on_warning=options["fail_on_warning"])
        report = {
            "status": status,
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
                self.stdout.write(style(f"{item['provider']}: {item['status']} - {item['detail']}"))
            self.stdout.write(self.style.SUCCESS(f"Provider validation status: {status}"))

        if status == "fail":
            raise CommandError("Provider validation failed.")

    @staticmethod
    def overall_status(checks, *, fail_on_warning: bool) -> str:
        if any(item["status"] == "fail" for item in checks):
            return "fail"
        if any(item["status"] == "warn" for item in checks):
            return "fail" if fail_on_warning else "warn"
        return "ok"

    @staticmethod
    def ok(provider: str, detail: str, **extra):
        return {"provider": provider, "status": "ok", "detail": detail, **extra}

    @staticmethod
    def warn(provider: str, detail: str, **extra):
        return {"provider": provider, "status": "warn", "detail": detail, **extra}

    @staticmethod
    def fail(provider: str, detail: str, **extra):
        return {"provider": provider, "status": "fail", "detail": detail, **extra}

    def check_email(self):
        backend = getattr(settings, "EMAIL_BACKEND", "")
        if not backend:
            return self.fail("email", "EMAIL_BACKEND is missing")
        if EmailDeliveryService.smtp_configured():
            return self.ok(
                "email", "SMTP configuration present", backend=backend.rsplit(".", 1)[-1]
            )
        if settings.DEPLOY_ENVIRONMENT == "production":
            return self.fail(
                "email",
                "SMTP backend is not configured for production sends",
                backend=backend.rsplit(".", 1)[-1],
            )
        return self.warn(
            "email",
            "SMTP not configured; local/dev backend only",
            backend=backend.rsplit(".", 1)[-1],
        )

    def check_storage(self):
        storage_name = default_storage.__class__.__name__
        public_bucket = bool(getattr(settings, "AWS_S3_BUCKET_NAME", ""))
        private_bucket = bool(getattr(settings, "AWS_S3_VERIFICATION_BUCKET", ""))
        if settings.DEPLOY_ENVIRONMENT == "production" and not (public_bucket and private_bucket):
            return self.fail(
                "storage",
                "public and private S3 bucket settings are required in production",
                backend=storage_name,
            )
        default_storage.get_available_name("provider-validation.tmp")
        if public_bucket and private_bucket:
            return self.ok("storage", "S3 bucket settings present", backend=storage_name)
        return self.warn(
            "storage",
            "S3 buckets not fully configured; using local/storage fallback",
            backend=storage_name,
        )

    def check_redis(self):
        errors = validate_production_redis_settings(settings)
        if errors:
            return self.fail("redis", " ".join(errors))
        cache.set("provider-validation:redis", "ok", timeout=15)
        if cache.get("provider-validation:redis") != "ok":
            return self.fail("redis", "cache read/write probe failed")
        backend = settings.CACHES["default"]["BACKEND"].rsplit(".", 1)[-1]
        return self.ok("redis", backend)

    def check_celery(self):
        broker = getattr(settings, "CELERY_BROKER_URL", "")
        result_backend = getattr(settings, "CELERY_RESULT_BACKEND", "")
        if not broker:
            return self.fail("celery", "CELERY_BROKER_URL is missing")
        if settings.DEPLOY_ENVIRONMENT == "production" and "redis" not in broker.lower():
            return self.fail("celery", "production broker must be Redis-backed")
        return self.ok(
            "celery",
            "broker configured",
            result_backend_configured=bool(result_backend),
            task_count=len(current_app.tasks),
        )

    def check_sentry(self):
        dsn = getattr(settings, "SENTRY_DSN", "")
        if not dsn:
            if settings.DEPLOY_ENVIRONMENT == "production":
                return self.warn("sentry", "SENTRY_DSN is not configured")
            return self.warn("sentry", "not configured in local/dev")
        return self.ok(
            "sentry", "DSN configured", environment=getattr(settings, "SENTRY_ENVIRONMENT", "")
        )

    def check_stripe(self):
        secret = bool(getattr(settings, "STRIPE_SECRET_KEY", ""))
        webhook = bool(getattr(settings, "STRIPE_WEBHOOK_SECRET", ""))
        if secret and webhook:
            return self.ok("stripe", "secret and webhook configured")
        if settings.DEPLOY_ENVIRONMENT == "production":
            return self.fail(
                "stripe", "STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET are required in production"
            )
        return self.warn("stripe", "Stripe is configuration-only in this environment")

    def check_ai(self):
        real_enabled = bool(getattr(settings, "AI_ENABLE_REAL_PROVIDERS", False))
        provider = getattr(settings, "AI_DEFAULT_PROVIDER", "mock")
        keys = {
            "openai": bool(getattr(settings, "OPENAI_API_KEY", "")),
            "anthropic": bool(getattr(settings, "ANTHROPIC_API_KEY", "")),
            "google_gemini": bool(getattr(settings, "GEMINI_API_KEY", "")),
            "azure_openai": bool(
                getattr(settings, "AZURE_OPENAI_API_KEY", "")
                and getattr(settings, "AZURE_OPENAI_ENDPOINT", "")
            ),
        }
        if real_enabled and not any(keys.values()):
            return self.fail(
                "ai",
                "real AI providers enabled but no provider credentials are configured",
                default_provider=provider,
            )
        if settings.DEPLOY_ENVIRONMENT == "production" and provider == "mock":
            return self.warn("ai", "AI_DEFAULT_PROVIDER is mock in production")
        return self.ok(
            "ai",
            "AI provider configuration is safe",
            default_provider=provider,
            real_providers_enabled=real_enabled,
        )

    def check_vector(self):
        backend = VectorBackendRegistry.get_backend()
        health = backend.health_check()
        status = health.get("status", "unknown")
        if status in {"ok", "healthy"}:
            return self.ok("vector", f"{backend.name} backend healthy", health=health)
        if settings.DEPLOY_ENVIRONMENT == "production":
            return self.fail("vector", f"{backend.name} backend is not healthy", health=health)
        return self.warn(
            "vector", f"{backend.name} backend is not production-backed", health=health
        )
