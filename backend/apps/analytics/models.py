from django.conf import settings
from django.db import models

from common.models import BaseModel


class AnalyticsEvent(BaseModel):
    name = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_events",
    )
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    target_type = models.CharField(max_length=100, blank=True, default="", db_index=True)
    target_id = models.CharField(max_length=100, blank=True, default="", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_events"
        indexes = [
            models.Index(fields=["name", "occurred_at"], name="analytics_e_name_928f4a_idx"),
            models.Index(fields=["user", "occurred_at"], name="analytics_e_user_id_661693_idx"),
            models.Index(fields=["organization_id", "occurred_at"], name="analytics_e_organiz_f8d02d_idx"),
            models.Index(fields=["target_type", "target_id"], name="analytics_e_target__40fcc2_idx"),
        ]
