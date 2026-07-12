from .base import *  # noqa: F401, F403

DEBUG = False
DEPLOY_ENVIRONMENT = "test"
SENTRY_ENVIRONMENT = "test"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="tcareer_test"),  # noqa: F405
        "USER": env("POSTGRES_USER", default="tcareer_test_user"),  # noqa: F405
        "PASSWORD": env("POSTGRES_PASSWORD", default="tcareer_test_pass"),  # noqa: F405
        "HOST": env("POSTGRES_HOST", default="localhost"),  # noqa: F405
        "PORT": env("POSTGRES_PORT", default="5432"),  # noqa: F405
        "TEST": {"NAME": "tcareer_test"},
    }
}

# Use DATABASE_URL if provided (CI environment)
import dj_database_url  # noqa: E402
import os  # noqa: E402

if os.environ.get("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config(default=os.environ["DATABASE_URL"])
    DATABASES["default"]["ATOMIC_REQUESTS"] = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=5)  # noqa: F405

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(  # noqa: F405
    {
        "auth": "10000/minute",
        "refresh": "10000/minute",
        "notification_preferences": "10000/minute",
        "unsubscribe": "10000/minute",
        "candidate_unlock": "10000/minute",
        "recruiter_search": "10000/minute",
        "application_submit": "10000/minute",
        "resume_download": "10000/minute",
        "invitation_accept": "10000/minute",
    }
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"]},
}

GOOGLE_OAUTH_CLIENT_ID = "test-google-client-id"
GOOGLE_OAUTH_CLIENT_SECRET = "test-google-client-secret"
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = GOOGLE_OAUTH_CLIENT_ID
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = GOOGLE_OAUTH_CLIENT_SECRET

OPENAI_API_KEY = "test-openai-key"
STRIPE_SECRET_KEY = "sk_test_placeholder"
STRIPE_WEBHOOK_SECRET = "whsec_test_placeholder"
