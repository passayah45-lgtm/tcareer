from django.contrib import admin

from apps.analytics.models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "organization_id", "target_type", "target_id", "occurred_at")
    list_filter = ("name", "target_type", "occurred_at")
    search_fields = ("name", "user__email", "target_type", "target_id")
    readonly_fields = (
        "id",
        "name",
        "user",
        "organization_id",
        "target_type",
        "target_id",
        "metadata",
        "occurred_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
