import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.CharField(db_index=True, max_length=100)),
                ("target_type", models.CharField(db_index=True, max_length=100)),
                ("target_id", models.CharField(db_index=True, max_length=100)),
                ("organization_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("ip_address", models.CharField(blank=True, default="", max_length=45)),
                ("user_agent", models.CharField(blank=True, default="", max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "audit_logs", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="auditlog", index=models.Index(fields=["actor", "created_at"], name="audit_logs_actor_i_497681_idx")),
        migrations.AddIndex(model_name="auditlog", index=models.Index(fields=["action", "created_at"], name="audit_logs_action_722f70_idx")),
        migrations.AddIndex(model_name="auditlog", index=models.Index(fields=["target_type", "target_id"], name="audit_logs_target__99ae91_idx")),
        migrations.AddIndex(model_name="auditlog", index=models.Index(fields=["organization_id", "created_at"], name="audit_logs_organiz_3d53d3_idx")),
    ]
