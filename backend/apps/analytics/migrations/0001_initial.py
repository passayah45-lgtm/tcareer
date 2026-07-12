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
            name="AnalyticsEvent",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(db_index=True, max_length=100)),
                ("organization_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("target_type", models.CharField(blank=True, db_index=True, default="", max_length=100)),
                ("target_id", models.CharField(blank=True, db_index=True, default="", max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="analytics_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "analytics_events"},
        ),
        migrations.AddIndex(model_name="analyticsevent", index=models.Index(fields=["name", "occurred_at"], name="analytics_e_name_928f4a_idx")),
        migrations.AddIndex(model_name="analyticsevent", index=models.Index(fields=["user", "occurred_at"], name="analytics_e_user_id_661693_idx")),
        migrations.AddIndex(model_name="analyticsevent", index=models.Index(fields=["organization_id", "occurred_at"], name="analytics_e_organiz_f8d02d_idx")),
        migrations.AddIndex(model_name="analyticsevent", index=models.Index(fields=["target_type", "target_id"], name="analytics_e_target__40fcc2_idx")),
    ]
