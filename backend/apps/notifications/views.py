import hashlib
import hmac

from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    EmailDelivery,
    EmailProviderWebhookService,
    EmailSuppression,
    Notification,
    NotificationCategory,
    NotificationPreference,
    NotificationUnsubscribeToken,
)
from common.audit import AuditService
from common.throttles import NotificationPreferenceRateThrottle, UnsubscribeRateThrottle


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "notification_type", "title", "body",
            "action_url", "payload", "category", "is_read", "read_at", "created_at",
        ]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = NotificationPreference
        fields = ["category", "category_display", "in_app_enabled", "email_enabled"]
        read_only_fields = ["category", "category_display"]


class EmailDeliveryHistorySerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = EmailDelivery
        fields = [
            "id",
            "category",
            "category_display",
            "subject",
            "status",
            "created_at",
            "sent_at",
            "failed_at",
            "retry_count",
            "last_error",
        ]
        read_only_fields = fields


def _ensure_preferences(user):
    preferences = []
    for category, _ in NotificationCategory.choices:
        pref, _ = NotificationPreference.objects.get_or_create(user=user, category=category)
        if category == NotificationCategory.SECURITY and (not pref.email_enabled or not pref.in_app_enabled):
            pref.in_app_enabled = True
            pref.email_enabled = True
            pref.save(update_fields=["in_app_enabled", "email_enabled", "updated_at"])
        preferences.append(pref)
    return preferences


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    """
    GET /api/v1/notifications/

    Returns the 20 most recent notifications for the authenticated user.
    Includes unread count.
    """
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")[:20]

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    return Response({
        "unread_count": unread_count,
        "notifications": NotificationSerializer(notifications, many=True).data,
    })


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([NotificationPreferenceRateThrottle])
def notification_preferences(request):
    if request.method == "GET":
        preferences = _ensure_preferences(request.user)
        suppressed = EmailSuppression.objects.filter(
            email__iexact=request.user.email,
            is_active=True,
        ).values_list("category", flat=True)
        return Response({
            "preferences": NotificationPreferenceSerializer(preferences, many=True).data,
            "suppressed_categories": list(suppressed),
        })

    updates = request.data.get("preferences", request.data)
    if isinstance(updates, dict):
        updates = [updates]
    updated = []
    for item in updates:
        category = item.get("category")
        if category not in NotificationCategory.values:
            continue
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user, category=category)
        if category != NotificationCategory.SECURITY:
            if "email_enabled" in item:
                pref.email_enabled = bool(item["email_enabled"])
            if "in_app_enabled" in item:
                pref.in_app_enabled = bool(item["in_app_enabled"])
        pref.save()
        AuditService.record(
            actor=request.user,
            action="notification_preference_changed",
            target=pref,
            request=request,
            metadata={"category": category, "email_enabled": pref.email_enabled, "in_app_enabled": pref.in_app_enabled},
        )
        updated.append(pref)
    return Response({"preferences": NotificationPreferenceSerializer(_ensure_preferences(request.user), many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def delivery_history(request):
    deliveries = EmailDelivery.objects.filter(recipient=request.user).select_related("notification").order_by("-created_at")[:100]
    return Response({"deliveries": EmailDeliveryHistorySerializer(deliveries, many=True).data})


def _webhook_provider(request) -> str:
    return (
        request.query_params.get("provider")
        or request.headers.get("X-TCareer-Email-Provider")
        or ""
    ).lower()


def _hmac_sha256(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _verify_ses(request) -> bool:
    secret = getattr(settings, "SES_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-TCareer-SES-Signature", "")
    return bool(secret and signature and constant_time_compare(signature, _hmac_sha256(secret, request.body)))


def _verify_sendgrid(request) -> bool:
    secret = getattr(settings, "SENDGRID_WEBHOOK_SECRET", "")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp", "")
    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature", "")
    signed_payload = f"{timestamp}.".encode("utf-8") + request.body
    return bool(secret and timestamp and signature and constant_time_compare(signature, _hmac_sha256(secret, signed_payload)))


def _verify_mailgun(request) -> bool:
    signing_key = getattr(settings, "MAILGUN_WEBHOOK_SIGNING_KEY", "")
    timestamp = request.data.get("timestamp") or request.data.get("signature", {}).get("timestamp", "")
    token = request.data.get("token") or request.data.get("signature", {}).get("token", "")
    signature = request.data.get("signature")
    if isinstance(signature, dict):
        signature = signature.get("signature", "")
    expected = hmac.new(signing_key.encode("utf-8"), f"{timestamp}{token}".encode("utf-8"), hashlib.sha256).hexdigest()
    return bool(signing_key and timestamp and token and signature and constant_time_compare(signature, expected))


def _verify_email_webhook(request) -> tuple[bool, str]:
    provider = _webhook_provider(request)
    if provider == "ses":
        return _verify_ses(request), provider
    if provider == "sendgrid":
        return _verify_sendgrid(request), provider
    if provider == "mailgun":
        return _verify_mailgun(request), provider
    if getattr(settings, "DEPLOY_ENVIRONMENT", "") == "production":
        return False, provider or "unknown"
    if not getattr(settings, "EMAIL_WEBHOOK_ALLOW_SHARED_SECRET", False):
        return False, provider or "shared_secret"
    configured_secret = getattr(settings, "EMAIL_WEBHOOK_SECRET", "")
    provided_secret = request.headers.get("X-TCareer-Email-Webhook-Secret", "") or request.headers.get("X-Webhook-Secret", "")
    return bool(configured_secret and provided_secret and constant_time_compare(configured_secret, provided_secret)), provider or "shared_secret"


@api_view(["POST"])
@permission_classes([AllowAny])
def email_provider_webhook(request):
    verified, provider = _verify_email_webhook(request)
    if not verified:
        AuditService.record(
            actor=None,
            action="provider_webhook_rejected",
            target_type="EmailProviderWebhook",
            target_id=request.META.get("REMOTE_ADDR", ""),
            request=request,
            metadata={"reason": "invalid_signature", "provider": provider},
        )
        return Response({"detail": "Invalid webhook signature."}, status=status.HTTP_403_FORBIDDEN)
    try:
        payload = dict(request.data)
        payload.setdefault("provider", provider)
        delivery, processed = EmailProviderWebhookService.process_event(payload)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if delivery is None:
        return Response({"detail": "Delivery not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"detail": "Event processed.", "processed": processed, "delivery_id": str(delivery.id)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UnsubscribeRateThrottle])
def unsubscribe(request):
    category = request.data.get("category", NotificationCategory.MARKETING)
    all_marketing = bool(request.data.get("all_marketing", False))
    if all_marketing:
        category = NotificationCategory.MARKETING
    if category == NotificationCategory.SECURITY:
        return Response({"detail": "Security notifications cannot be disabled."}, status=400)
    if category not in NotificationCategory.values:
        return Response({"detail": "Invalid category."}, status=400)
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user, category=category)
    pref.email_enabled = False
    pref.save(update_fields=["email_enabled", "updated_at"])
    EmailSuppression.objects.update_or_create(
        user=request.user,
        email=request.user.email,
        category=category,
        defaults={"is_active": True, "reason": "user_unsubscribed"},
    )
    AuditService.record(
        actor=request.user,
        action="notification_unsubscribed",
        target_type="EmailSuppression",
        target_id=request.user.email,
        request=request,
        metadata={"category": category},
    )
    return Response({"detail": "Unsubscribed.", "category": category})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UnsubscribeRateThrottle])
def resubscribe(request):
    category = request.data.get("category", "")
    if category and category not in NotificationCategory.values:
        return Response({"detail": "Invalid category."}, status=400)
    suppressions = EmailSuppression.objects.filter(user=request.user, email__iexact=request.user.email, is_active=True)
    if category:
        suppressions = suppressions.filter(category=category)
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user, category=category)
        pref.email_enabled = True
        pref.save(update_fields=["email_enabled", "updated_at"])
    else:
        for pref in _ensure_preferences(request.user):
            if pref.category != NotificationCategory.SECURITY:
                pref.email_enabled = True
                pref.save(update_fields=["email_enabled", "updated_at"])
    suppressions.update(is_active=False)
    AuditService.record(
        actor=request.user,
        action="notification_resubscribed",
        target_type="EmailSuppression",
        target_id=request.user.email,
        request=request,
        metadata={"category": category},
    )
    return Response({"detail": "Resubscribed.", "category": category})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([UnsubscribeRateThrottle])
def unsubscribe_token(request, token):
    token_obj = NotificationUnsubscribeToken.validate_token(token)
    if not token_obj:
        return Response({"detail": "This unsubscribe link is invalid or expired."}, status=400)
    if token_obj.category == NotificationCategory.SECURITY:
        return Response({"detail": "Security notifications cannot be disabled."}, status=400)
    pref, _ = NotificationPreference.objects.get_or_create(user=token_obj.user, category=token_obj.category)
    pref.email_enabled = False
    pref.save(update_fields=["email_enabled", "updated_at"])
    EmailSuppression.objects.update_or_create(
        user=token_obj.user,
        email=token_obj.email,
        category=token_obj.category,
        defaults={"is_active": True, "reason": "token_unsubscribed"},
    )
    token_obj.used_at = timezone.now()
    token_obj.save(update_fields=["used_at", "updated_at"])
    AuditService.record(
        actor=token_obj.user,
        action="notification_unsubscribed",
        target=token_obj,
        request=request,
        metadata={"category": token_obj.category, "source": "token"},
    )
    return Response({"detail": "Unsubscribed.", "category": token_obj.category})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_read(request, notification_id):
    """
    POST /api/v1/notifications/{id}/read/
    Mark a single notification as read.
    """
    try:
        notification = Notification.objects.get(
            id=notification_id, recipient=request.user
        )
        notification.mark_read()
        return Response({"detail": "Marked as read."})
    except Notification.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    """
    POST /api/v1/notifications/read-all/
    Mark all notifications as read.
    """
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())
    return Response({"detail": "All notifications marked as read."})
