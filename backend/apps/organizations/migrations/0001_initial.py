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
            name="Organization",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(db_index=True, max_length=280, unique=True)),
                ("organization_type", models.CharField(choices=[("university", "University"), ("company", "Company"), ("bootcamp", "Bootcamp"), ("ngo", "NGO"), ("government", "Government Institution"), ("enterprise", "Enterprise Customer")], db_index=True, max_length=30)),
                ("status", models.CharField(choices=[("pending", "Pending Verification"), ("active", "Active"), ("suspended", "Suspended"), ("archived", "Archived")], db_index=True, default="pending", max_length=20)),
                ("website_url", models.URLField(blank=True, default="")),
                ("country_code", models.CharField(blank=True, db_index=True, default="", max_length=2)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_accounts_created", to=settings.AUTH_USER_MODEL)),
                ("verified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_accounts_verified", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "organization_accounts"},
        ),
        migrations.CreateModel(
            name="OrganizationMembership",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(choices=[("student", "Student"), ("instructor", "Instructor"), ("mentor", "Mentor"), ("recruiter", "Recruiter"), ("company_admin", "Company Admin"), ("university_admin", "University Admin"), ("content_moderator", "Content Moderator"), ("finance_admin", "Finance Admin"), ("platform_admin", "Platform Admin"), ("super_admin", "Super Admin")], db_index=True, max_length=30)),
                ("status", models.CharField(choices=[("active", "Active"), ("invited", "Invited"), ("suspended", "Suspended"), ("removed", "Removed")], db_index=True, default="active", max_length=20)),
                ("invited_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_memberships_invited", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="organizations.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="organization_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "organization_account_memberships", "unique_together": {("organization", "user", "role")}},
        ),
        migrations.CreateModel(
            name="OrganizationInvitation",
            fields=[
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("role", models.CharField(choices=[("student", "Student"), ("instructor", "Instructor"), ("mentor", "Mentor"), ("recruiter", "Recruiter"), ("company_admin", "Company Admin"), ("university_admin", "University Admin"), ("content_moderator", "Content Moderator"), ("finance_admin", "Finance Admin"), ("platform_admin", "Platform Admin"), ("super_admin", "Super Admin")], max_length=30)),
                ("token_hash", models.CharField(db_index=True, max_length=128, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("accepted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_invitations_accepted", to=settings.AUTH_USER_MODEL)),
                ("invited_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_invitations_sent", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="organizations.organization")),
            ],
            options={"db_table": "organization_account_invitations"},
        ),
        migrations.AddIndex(model_name="organization", index=models.Index(fields=["organization_type", "status"], name="organizatio_organiz_118010_idx")),
        migrations.AddIndex(model_name="organization", index=models.Index(fields=["country_code", "status"], name="organizatio_country_0b7cf0_idx")),
        migrations.AddIndex(model_name="organizationmembership", index=models.Index(fields=["organization", "role", "status"], name="organizatio_organiz_68067a_idx")),
        migrations.AddIndex(model_name="organizationmembership", index=models.Index(fields=["user", "status"], name="organizatio_user_id_dfbb75_idx")),
        migrations.AddIndex(model_name="organizationinvitation", index=models.Index(fields=["organization", "email"], name="organizatio_organiz_0cc3b2_idx")),
        migrations.AddIndex(model_name="organizationinvitation", index=models.Index(fields=["email", "expires_at"], name="organizatio_email_783529_idx")),
    ]
