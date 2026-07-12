from dataclasses import dataclass


@dataclass(frozen=True)
class OpsCheckResult:
    name: str
    ok: bool
    status: str
    detail: str = ""


def release_metadata(settings_obj):
    getter = settings_obj.get if isinstance(settings_obj, dict) else lambda name, default="": getattr(settings_obj, name, default)
    return {
        "app_version": getter("APP_VERSION", ""),
        "api_version": getter("API_VERSION", ""),
        "git_sha": getter("GIT_SHA", ""),
        "build_date": getter("BUILD_DATE", ""),
        "release": getter("SENTRY_RELEASE", "") or getter("APP_VERSION", ""),
        "environment": getter("DEPLOY_ENVIRONMENT", "") or getter("SENTRY_ENVIRONMENT", ""),
        "release_notes": getter("RELEASE_NOTES_URL", "docs/release-candidate-1.0.md"),
    }


def validate_production_redis_settings(settings_obj):
    getter = settings_obj.get if isinstance(settings_obj, dict) else lambda name, default=None: getattr(settings_obj, name, default)
    environment = getter("DEPLOY_ENVIRONMENT", "") or getter("SENTRY_ENVIRONMENT", "")
    if environment != "production":
        return []

    errors = []
    redis_url = getter("REDIS_URL", "")
    caches = getter("CACHES", {})
    cache_backend = caches.get("default", {}).get("BACKEND", "")
    cache_location = caches.get("default", {}).get("LOCATION", "")

    if not redis_url:
        errors.append("REDIS_URL must be configured in production.")
    if "locmem" in cache_backend.lower():
        errors.append("Production cache backend must not use local memory.")
    if "redis" not in cache_backend.lower():
        errors.append("Production cache backend must use Redis.")
    if not cache_location:
        errors.append("Production cache location must be configured.")
    if getter("THROTTLE_CACHE_ALIAS", "default") != "default":
        errors.append("DRF throttling must use the shared default cache in production.")
    return errors
