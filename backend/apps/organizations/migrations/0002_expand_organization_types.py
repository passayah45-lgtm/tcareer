from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="organization_type",
            field=models.CharField(
                choices=[
                    ("university", "University"),
                    ("company", "Company"),
                    ("bootcamp", "Bootcamp"),
                    ("ngo", "NGO"),
                    ("government", "Government Institution"),
                    ("enterprise", "Enterprise Customer"),
                    ("platform_partner", "Platform Partner"),
                    ("other", "Other"),
                ],
                db_index=True,
                max_length=30,
            ),
        ),
    ]
