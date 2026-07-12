from .base import *  # noqa: F401, F403
from datetime import timedelta

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
AUTH_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=60)  # noqa: F405

# EMAIL_BACKEND is read from .env file

if env("CACHE_BACKEND", default="") == "":  # noqa: F405
    CACHES = {  # noqa: F405
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "tcareer-dev-cache",
            "KEY_PREFIX": "tcareer",
        }
    }
