from django.contrib import admin

from common.audit import AuditService

from .models import (
    EmailDelivery,
    EmailDeliveryService,
    EmailDeliveryStatus,
    EmailSuppression,
    Notification,
    NotificationPreference,
    NotificationUnsubscribeToken,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "title", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("recipient__email", "title", "body")
    readonly_fields = tuple(field.name for field in Notification._meta.fields)


@admin.action(description="Retry selected email deliveries")
def retry_email_deliveries(modeladmin, request, queryset):
    for delivery in queryset.exclude(status="sent"):
        EmailDeliveryService.send_email_delivery(delivery.id)
        AuditService.record(
            actor=request.user,
            action="email_delivery_admin_retry",
            target=delivery,
            request=request,
            metadata={"status": delivery.status},
        )


@admin.action(description="Cancel selected pending email deliveries")
def cancel_email_deliveries(modeladmin, request, queryset):
    for delivery in queryset.exclude(status=EmailDeliveryStatus.SENT):
        delivery.status = EmailDeliveryStatus.CANCELLED
        delivery.last_error = "Cancelled by admin."
        delivery.save(update_fields=["status", "last_error", "updated_at"])
        AuditService.record(
            actor=request.user,
            action="email_delivery_cancelled",
            target=delivery,
            request=request,
            metadata={"category": delivery.category},
        )


@admin.register(EmailDelivery)
class EmailDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "recipient_email",
        "template_key",
        "category",
        "status",
        "retry_count",
        "created_at",
        "sent_at",
        "failed_at",
    )
    list_filter = ("status", "template_key", "category", "created_at", "sent_at", "failed_at")
    search_fields = ("recipient_email", "subject", "last_error", "provider_message_id")
    readonly_fields = tuple(field.name for field in EmailDelivery._meta.fields)
    actions = [retry_email_deliveries, cancel_email_deliveries]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "in_app_enabled", "email_enabled", "updated_at")
    list_filter = ("category", "in_app_enabled", "email_enabled")
    search_fields = ("user__email", "user__full_name")


@admin.register(EmailSuppression)
class EmailSuppressionAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "category", "is_active", "reason", "created_at")
    list_filter = ("category", "is_active", "reason")
    search_fields = ("email", "user__email", "user__full_name")


@admin.register(NotificationUnsubscribeToken)
class NotificationUnsubscribeTokenAdmin(admin.ModelAdmin):
    list_display = ("email", "category", "expires_at", "used_at", "created_at")
    list_filter = ("category", "expires_at", "used_at")
    search_fields = ("email", "user__email")
    readonly_fields = tuple(field.name for field in NotificationUnsubscribeToken._meta.fields)
