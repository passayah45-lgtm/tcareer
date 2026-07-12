import sentry_sdk
import logging
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401, F403
from common.ops import release_metadata, validate_production_redis_settings

DEBUG = False

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)  # noqa: F405
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)  # noqa: F405
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)  # noqa: F405
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)  # noqa: F405
X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = env("REFERRER_POLICY", default="same-origin")  # noqa: F405

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])  # noqa: F405
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

redis_errors = validate_production_redis_settings(globals())
if redis_errors:
    raise ImproperlyConfigured(" ".join(redis_errors))

SENTRY_DSN = env("SENTRY_DSN", default="")  # noqa: F405
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT", default=DEPLOY_ENVIRONMENT)  # noqa: F405
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1)  # noqa: F405
SENTRY_RELEASE = env("SENTRY_RELEASE", default=APP_VERSION)  # noqa: F405
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,
    )

LOGGING["handlers"]["console"]["formatter"] = "verbose"  # noqa: F405

logging.getLogger("tcareer.release").info("application_release_metadata", extra=release_metadata(globals()))
