from django.apps import AppConfig


class AIPlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_platform"
    verbose_name = "AI Platform"

    def ready(self):
        from apps.ai_platform import signals  # noqa: F401
