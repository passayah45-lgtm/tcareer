from django.conf import settings
from django.db import models

from common.models import BaseModel


class AuditLog(BaseModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=100, db_index=True)
    target_id = models.CharField(max_length=100, db_index=True)
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    ip_address = models.CharField(max_length=45, blank=True, default="")
    user_agent = models.CharField(max_length=500, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"], name="audit_logs_actor_i_497681_idx"),
            models.Index(fields=["action", "created_at"], name="audit_logs_action_722f70_idx"),
            models.Index(fields=["target_type", "target_id"], name="audit_logs_target__99ae91_idx"),
            models.Index(fields=["organization_id", "created_at"], name="audit_logs_organiz_3d53d3_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("AuditLog records are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog records cannot be deleted.")
