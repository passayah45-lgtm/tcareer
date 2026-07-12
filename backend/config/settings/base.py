"""
Base settings shared across all environments.
Never import this file directly in code - import from the environment-specific module.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 15),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    SECURE_SSL_REDIRECT=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    SECURE_HSTS_SECONDS=(int, 0),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "social_django",
    "django_celery_beat",
    "django_filters",
]

LOCAL_APPS = [
    "apps.users",
    "apps.courses",
    "apps.assessments",
    "apps.certificates",
    "apps.ai_platform",
    "apps.ai_tutor",
    "apps.jobs",
    "apps.payments",
    "apps.tracks",
    "apps.community",
    "apps.notifications",
    "apps.careers",
    "apps.geo",
    "apps.profiles",
    "apps.verification",
    "apps.trust",
    "apps.organizations",
    "apps.audit.apps.AuditConfig",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 60

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHE_BACKEND = env("CACHE_BACKEND", default="django_redis.cache.RedisCache")
DJANGO_CACHE_LOCATION = env("DJANGO_CACHE_LOCATION", default=REDIS_URL)

if CACHE_BACKEND == "django_redis.cache.RedisCache":
    CACHES = {
        "default": {
            "BACKEND": CACHE_BACKEND,
            "LOCATION": DJANGO_CACHE_LOCATION,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            },
            "KEY_PREFIX": "tcareer",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": CACHE_BACKEND,
            "LOCATION": DJANGO_CACHE_LOCATION,
            "KEY_PREFIX": "tcareer",
        }
    }

THROTTLE_CACHE_ALIAS = "default"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = env("REFERRER_POLICY", default="same-origin")

AUTH_REFRESH_COOKIE_NAME = env("AUTH_REFRESH_COOKIE_NAME", default="tcareer_refresh")
AUTH_CSRF_COOKIE_NAME = env("AUTH_CSRF_COOKIE_NAME", default="tcareer_csrf")
AUTH_COOKIE_SECURE = env.bool("AUTH_COOKIE_SECURE", default=not DEBUG)
AUTH_COOKIE_SAMESITE = env("AUTH_COOKIE_SAMESITE", default="Lax")
AUTH_COOKIE_DOMAIN = env("AUTH_COOKIE_DOMAIN", default=None)

MAX_UPLOAD_SIZE_BYTES = env.int("MAX_UPLOAD_SIZE_BYTES", default=25 * 1024 * 1024)
MAX_PRIVATE_DOCUMENT_SIZE_BYTES = env.int(
    "MAX_PRIVATE_DOCUMENT_SIZE_BYTES",
    default=10 * 1024 * 1024,
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "common.renderers.StandardRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON_RATE", default="100/hour"),
        "user": env("THROTTLE_USER_RATE", default="1000/hour"),
        "auth": env("THROTTLE_AUTH_RATE", default="10/minute"),
        "refresh": env("THROTTLE_REFRESH_RATE", default="30/minute"),
        "notification_preferences": env(
            "THROTTLE_NOTIFICATION_PREFERENCES_RATE", default="30/minute"
        ),
        "unsubscribe": env("THROTTLE_UNSUBSCRIBE_RATE", default="20/minute"),
        "candidate_unlock": env("THROTTLE_CANDIDATE_UNLOCK_RATE", default="30/minute"),
        "recruiter_search": env("THROTTLE_RECRUITER_SEARCH_RATE", default="60/minute"),
        "application_submit": env("THROTTLE_APPLICATION_SUBMIT_RATE", default="20/minute"),
        "resume_download": env("THROTTLE_RESUME_DOWNLOAD_RATE", default="30/minute"),
        "invitation_accept": env("THROTTLE_INVITATION_ACCEPT_RATE", default="20/minute"),
        "ai": env("THROTTLE_AI_RATE", default="60/minute"),
    },
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("JWT_REFRESH_TOKEN_LIFETIME_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "apps.users.serializers.CustomTokenObtainPairSerializer",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "T-Career API",
    "DESCRIPTION": "T-Career AI-powered learning and career development platform API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("GOOGLE_OAUTH_CLIENT_ID")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("GOOGLE_OAUTH_CLIENT_SECRET")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ["first_name", "last_name"]

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

SOCIAL_AUTH_USER_MODEL = "users.User"
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_REGION = env("AWS_REGION", default="ap-south-1")
AWS_S3_BUCKET_NAME = env("AWS_S3_BUCKET_NAME", default="")
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")

# Private bucket for verification documents only
AWS_S3_VERIFICATION_BUCKET = env("AWS_S3_VERIFICATION_BUCKET", default="")

OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
AZURE_OPENAI_API_KEY = env("AZURE_OPENAI_API_KEY", default="")
AZURE_OPENAI_ENDPOINT = env("AZURE_OPENAI_ENDPOINT", default="")
AI_DEFAULT_PROVIDER = env("AI_DEFAULT_PROVIDER", default="mock")
AI_ENABLE_REAL_PROVIDERS = env.bool("AI_ENABLE_REAL_PROVIDERS", default=False)
AI_REQUEST_TIMEOUT_SECONDS = env.int("AI_REQUEST_TIMEOUT_SECONDS", default=30)

STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
MEDIACONVERT_WEBHOOK_SECRET = env("MEDIACONVERT_WEBHOOK_SECRET", default="")

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="T-Career <noreply@tcareer.com>")
EMAIL_DELIVERY_MAX_RETRIES = env.int("EMAIL_DELIVERY_MAX_RETRIES", default=3)
EMAIL_DELIVERY_PROCESSING_TIMEOUT_SECONDS = env.int(
    "EMAIL_DELIVERY_PROCESSING_TIMEOUT_SECONDS", default=900
)
EMAIL_WEBHOOK_SECRET = env("EMAIL_WEBHOOK_SECRET", default="")
EMAIL_WEBHOOK_ALLOW_SHARED_SECRET = env.bool("EMAIL_WEBHOOK_ALLOW_SHARED_SECRET", default=DEBUG)
SES_WEBHOOK_SECRET = env("SES_WEBHOOK_SECRET", default="")
SENDGRID_WEBHOOK_SECRET = env("SENDGRID_WEBHOOK_SECRET", default="")
MAILGUN_WEBHOOK_SIGNING_KEY = env("MAILGUN_WEBHOOK_SIGNING_KEY", default="")
AUDIT_RETENTION_DAYS = env.int("AUDIT_RETENTION_DAYS", default=0)
AUDIT_RETENTION_ENABLED = env.bool("AUDIT_RETENTION_ENABLED", default=False)
RETENTION_DEFAULT_DAYS = env.int("RETENTION_DEFAULT_DAYS", default=365)
RETENTION_ANALYTICS_EVENTS_DAYS = env.int("RETENTION_ANALYTICS_EVENTS_DAYS", default=730)
RETENTION_NOTIFICATIONS_DAYS = env.int("RETENTION_NOTIFICATIONS_DAYS", default=365)
RETENTION_EMAIL_DELIVERIES_DAYS = env.int("RETENTION_EMAIL_DELIVERIES_DAYS", default=365)
RETENTION_AI_REQUESTS_DAYS = env.int("RETENTION_AI_REQUESTS_DAYS", default=365)
RETENTION_AI_USAGE_DAYS = env.int("RETENTION_AI_USAGE_DAYS", default=730)
RETENTION_AI_FEEDBACK_DAYS = env.int("RETENTION_AI_FEEDBACK_DAYS", default=730)
RETENTION_AI_EVALUATIONS_DAYS = env.int("RETENTION_AI_EVALUATIONS_DAYS", default=730)
RETENTION_RAG_RETRIEVAL_DAYS = env.int("RETENTION_RAG_RETRIEVAL_DAYS", default=365)
RETENTION_EXPORT_FILES_DAYS = env.int("RETENTION_EXPORT_FILES_DAYS", default=30)
RETENTION_IMPORT_FILES_DAYS = env.int("RETENTION_IMPORT_FILES_DAYS", default=30)
RETENTION_FAILED_WORKER_JOBS_DAYS = env.int("RETENTION_FAILED_WORKER_JOBS_DAYS", default=90)

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
APP_VERSION = env("APP_VERSION", default=SPECTACULAR_SETTINGS["VERSION"])
API_VERSION = env("API_VERSION", default=SPECTACULAR_SETTINGS["VERSION"])
GIT_SHA = env("GIT_SHA", default="")
BUILD_DATE = env("BUILD_DATE", default="")
RELEASE_NOTES_URL = env("RELEASE_NOTES_URL", default="docs/release-candidate-1.0.md")
DEPLOY_ENVIRONMENT = env("DEPLOY_ENVIRONMENT", default="development" if DEBUG else "production")
SENTRY_RELEASE = env("SENTRY_RELEASE", default=APP_VERSION)
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT", default=DEPLOY_ENVIRONMENT)

# Signed URL expiry for verification documents in seconds (15 minutes)
VERIFICATION_SIGNED_URL_EXPIRY = 900

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
