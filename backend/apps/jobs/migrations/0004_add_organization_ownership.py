import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0003_add_global_job_fields"),
        ("organizations", "0003_recruiter_entitlements_candidate_unlocks"),
    ]

    operations = [
        migrations.AddField(
            model_name="joblisting",
            name="organization",
            field=models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="job_listings", to="organizations.organization"),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["organization", "is_active"], name="job_listing_organiz_585f46_idx"),
        ),
    ]
