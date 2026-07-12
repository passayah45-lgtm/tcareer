import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_expand_organization_types"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationRecruiterEntitlement",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("max_recruiter_seats", models.PositiveIntegerField(default=0)),
                ("can_post_jobs", models.BooleanField(default=False)),
                ("can_search_candidates", models.BooleanField(default=False)),
                ("can_view_candidate_profiles", models.BooleanField(default=False)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("organization", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="recruiter_entitlement", to="organizations.organization")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="recruiter_entitlements_updated", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "organization_recruiter_entitlements"},
        ),
        migrations.CreateModel(
            name="CandidateProfileUnlock",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidate_profile_unlocks", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidate_profile_unlocks", to="organizations.organization")),
                ("unlocked_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="candidate_profiles_unlocked", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "candidate_profile_unlocks",
                "unique_together": {("organization", "candidate")},
            },
        ),
        migrations.AddIndex(
            model_name="candidateprofileunlock",
            index=models.Index(fields=["organization", "candidate"], name="candidate_p_organiz_6acffe_idx"),
        ),
    ]
