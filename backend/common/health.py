import logging

from celery import current_app
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import connection
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from apps.jobs.models import JobAlert
from apps.notifications.models import EmailDelivery, EmailDeliveryStatus
from common.ops import release_metadata, validate_production_redis_settings

logger = logging.getLogger("tcareer.health")


def _check_database():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return {"status": "ok"}


def _check_cache():
    redis_errors = validate_production_redis_settings(settings)
    if redis_errors:
        raise RuntimeError(" ".join(redis_errors))
    key = "health:cache"
    cache.set(key, "ok", timeout=15)
    if cache.get(key) != "ok":
        raise RuntimeError("Cache read/write check failed.")
    return {
        "status": "ok",
        "backend": settings.CACHES["default"]["BACKEND"].split(".")[-1],
    }


def _check_storage():
    default_storage.get_available_name("healthcheck.tmp")
    return {"status": "ok", "backend": default_storage.__class__.__name__}


def _check_email():
    configured = bool(getattr(settings, "EMAIL_BACKEND", ""))
    provider_ready = False
    backend = getattr(settings, "EMAIL_BACKEND", "")
    if "locmem" in backend:
        provider_ready = True
    elif "console" not in backend:
        provider_ready = bool(getattr(settings, "EMAIL_HOST", "") and getattr(settings, "DEFAULT_FROM_EMAIL", ""))
    return {
        "status": "ok" if configured else "warning",
        "configured": configured,
        "provider_ready": provider_ready,
        "backend": backend.rsplit(".", 1)[-1] if backend else "",
    }


def _check_celery():
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    configured = bool(broker_url)
    return {
        "status": "ok" if configured else "warning",
        "configured": configured,
        "tasks_registered": len(current_app.tasks),
    }


def _celery_inspect_summary():
    try:
        inspector = current_app.control.inspect(timeout=1.0)
        stats = inspector.stats() or {}
        active = inspector.active() or {}
        reserved = inspector.reserved() or {}
        scheduled = inspector.scheduled() or {}
    except Exception as exc:
        logger.warning("celery_inspect_failed", extra={"error": str(exc)[:200]})
        return {
            "status": "unknown",
            "workers_online": 0,
            "active_tasks": 0,
            "reserved_tasks": 0,
            "scheduled_tasks": 0,
        }
    return {
        "status": "ok" if stats else "unknown",
        "workers_online": len(stats),
        "active_tasks": sum(len(tasks) for tasks in active.values()),
        "reserved_tasks": sum(len(tasks) for tasks in reserved.values()),
        "scheduled_tasks": sum(len(tasks) for tasks in scheduled.values()),
    }


def _redis_broker_summary():
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")
    return {
        "status": "configured" if broker_url else "missing",
        "scheme": broker_url.split(":", 1)[0] if broker_url else "",
        "shared_cache": settings.CACHES["default"]["BACKEND"].lower().find("redis") >= 0,
    }


def worker_status_payload():
    delivery_counts = {
        row["status"]: row["count"]
        for row in EmailDelivery.objects.values("status").annotate(count=Count("id"))
    }
    recent_errors = list(
        EmailDelivery.objects.filter(status__in=[EmailDeliveryStatus.FAILED, EmailDeliveryStatus.RETRYING])
        .order_by("-updated_at")
        .values("id", "status", "template_key", "category", "retry_count", "last_error", "updated_at")[:10]
    )
    latest_alert = JobAlert.objects.order_by("-last_run_at", "-updated_at").values(
        "id", "name", "is_active", "last_run_at", "last_matched_count", "total_matched_count"
    ).first()
    return {
        "status": "ok",
        "release": release_metadata(settings),
        "celery": _celery_inspect_summary(),
        "redis_broker": _redis_broker_summary(),
        "email_queue": {
            "pending": delivery_counts.get(EmailDeliveryStatus.PENDING, 0),
            "queued": delivery_counts.get(EmailDeliveryStatus.QUEUED, 0),
            "retrying": delivery_counts.get(EmailDeliveryStatus.RETRYING, 0),
            "failed": delivery_counts.get(EmailDeliveryStatus.FAILED, 0),
            "sent": delivery_counts.get(EmailDeliveryStatus.SENT, 0),
            "cancelled": delivery_counts.get(EmailDeliveryStatus.CANCELLED, 0),
            "backlog": delivery_counts.get(EmailDeliveryStatus.PENDING, 0)
            + delivery_counts.get(EmailDeliveryStatus.QUEUED, 0)
            + delivery_counts.get(EmailDeliveryStatus.RETRYING, 0),
        },
        "job_alerts": {
            "last_run_tracking": "JobAlert.last_run_at",
            "command": "python manage.py run_job_alerts",
            "latest": {
                **latest_alert,
                "id": str(latest_alert["id"]),
            } if latest_alert else None,
        },
        "recent_worker_errors": [
            {
                "id": str(item["id"]),
                "status": item["status"],
                "template_key": item["template_key"],
                "category": item["category"],
                "retry_count": item["retry_count"],
                "last_error": (item["last_error"] or "")[:200],
                "updated_at": item["updated_at"],
            }
            for item in recent_errors
        ],
    }


def _safe_check(name, fn, critical=True):
    try:
        payload = fn()
        return name, payload, True
    except Exception as exc:
        logger.warning("health_check_failed", extra={"component": name, "error": str(exc)[:200]})
        return name, {"status": "error", "error": "check_failed"}, not critical


def health_payload(include_dependencies=True):
    payload = {
        "status": "ok",
        "service": "tcareer-api",
        "version": getattr(settings, "SPECTACULAR_SETTINGS", {}).get("VERSION", "unknown"),
        "release": release_metadata(settings),
    }
    if not include_dependencies:
        return payload

    checks = {}
    healthy = True
    for name, result, ok in [
        _safe_check("database", _check_database, critical=True),
        _safe_check("cache", _check_cache, critical=True),
        _safe_check("storage", _check_storage, critical=True),
        _safe_check("email", _check_email, critical=False),
        _safe_check("celery", _check_celery, critical=False),
    ]:
        checks[name] = result
        healthy = healthy and ok
    payload["status"] = "ok" if healthy else "degraded"
    payload["checks"] = checks
    return payload


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def health(request):
    return Response(health_payload(include_dependencies=True))


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def ready(request):
    payload = health_payload(include_dependencies=True)
    status_code = 200 if payload["status"] == "ok" else 503
    return Response(payload, status=status_code)


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def live(request):
    return Response(health_payload(include_dependencies=False))


@api_view(["GET"])
@permission_classes([IsAdminUser])
@renderer_classes([JSONRenderer])
def ops(request):
    return Response(worker_status_payload())
