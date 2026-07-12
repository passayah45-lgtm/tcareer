from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Portfolio",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("headline", models.CharField(blank=True, default="", max_length=200)),
                ("bio", models.TextField(blank=True, default="")),
                ("location", models.CharField(blank=True, default="", max_length=100)),
                ("desired_role", models.CharField(blank=True, db_index=True, default="", help_text="Target job title for matching. e.g. 'Backend Developer'", max_length=200)),
                ("experience_level", models.CharField(choices=[("student", "Student"), ("entry", "Entry Level (0-2 years)"), ("mid", "Mid Level (2-5 years)"), ("senior", "Senior (5+ years)"), ("lead", "Lead / Manager")], db_index=True, default="student", max_length=20)),
                ("linkedin_url", models.URLField(blank=True, default="", max_length=500)),
                ("github_url", models.URLField(blank=True, default="", max_length=500)),
                ("website_url", models.URLField(blank=True, default="", max_length=500)),
                ("visibility", models.CharField(choices=[("public", "Public"), ("unlisted", "Unlisted"), ("private", "Private")], db_index=True, default="public", max_length=10)),
                ("profile_views", models.PositiveIntegerField(default=0)),
                ("user", models.OneToOneField(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="portfolio", to="users.user")),
            ],
            options={"db_table": "portfolios"},
        ),
        migrations.CreateModel(
            name="PortfolioProject",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("tech_stack", models.JSONField(default=list)),
                ("project_url", models.URLField(blank=True, default="", max_length=500)),
                ("github_url", models.URLField(blank=True, default="", max_length=500)),
                ("demo_video_url", models.URLField(blank=True, default="", max_length=500)),
                ("thumbnail_url", models.URLField(blank=True, default="", max_length=500)),
                ("gallery_urls", models.JSONField(default=list)),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("position", models.PositiveIntegerField(default=0)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("portfolio", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="careers.portfolio")),
            ],
            options={"db_table": "portfolio_projects", "ordering": ["-is_featured", "position"]},
        ),
        migrations.CreateModel(
            name="PortfolioSkill",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("category", models.CharField(blank=True, default="", max_length=50)),
                ("source", models.CharField(choices=[("manual", "Added manually"), ("track", "Imported from career track"), ("course", "Imported from completed course")], default="manual", max_length=10)),
                ("source_id", models.UUIDField(blank=True, null=True)),
                ("position", models.PositiveIntegerField(default=0)),
                ("portfolio", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="skills", to="careers.portfolio")),
            ],
            options={"db_table": "portfolio_skills", "ordering": ["position", "name"]},
        ),
        migrations.CreateModel(
            name="Resume",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(blank=True, default="", max_length=200)),
                ("summary", models.TextField(blank=True, default="")),
                ("target_role", models.CharField(blank=True, db_index=True, default="", max_length=200)),
                ("education", models.JSONField(default=list)),
                ("experience", models.JSONField(default=list)),
                ("pdf_url", models.URLField(blank=True, default="", max_length=500)),
                ("last_generated_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.OneToOneField(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="resume", to="users.user")),
            ],
            options={"db_table": "resumes"},
        ),
        migrations.AddIndex(
            model_name="portfolio",
            index=models.Index(fields=["user"], name="portfolios_user_idx"),
        ),
        migrations.AddIndex(
            model_name="portfolio",
            index=models.Index(fields=["visibility", "experience_level"], name="portfolios_visibility_exp_idx"),
        ),
        migrations.AddIndex(
            model_name="portfolio",
            index=models.Index(fields=["desired_role"], name="portfolios_desired_role_idx"),
        ),
        migrations.AddIndex(
            model_name="portfolioskill",
            index=models.Index(fields=["portfolio"], name="portfolio_skills_portfolio_idx"),
        ),
        migrations.AddIndex(
            model_name="portfolioskill",
            index=models.Index(fields=["name"], name="portfolio_skills_name_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="portfolioskill",
            unique_together={("portfolio", "name")},
        ),
        migrations.AddIndex(
            model_name="portfolioproject",
            index=models.Index(fields=["portfolio"], name="portfolio_projects_portfolio_idx"),
        ),
        migrations.AddIndex(
            model_name="portfolioproject",
            index=models.Index(fields=["portfolio", "is_featured"], name="portfolio_projects_featured_idx"),
        ),
        migrations.AddIndex(
            model_name="resume",
            index=models.Index(fields=["user"], name="resumes_user_idx"),
        ),
        migrations.AddIndex(
            model_name="resume",
            index=models.Index(fields=["target_role"], name="resumes_target_role_idx"),
        ),
    ]
