from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Currency",
            fields=[
                ("code", models.CharField(max_length=3, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("symbol", models.CharField(max_length=10)),
                ("symbol_position", models.CharField(
                    choices=[("before", "Before"), ("after", "After")],
                    default="before",
                    max_length=6,
                )),
                ("decimal_places", models.SmallIntegerField(default=2)),
                ("is_active", models.BooleanField(default=True)),
                ("exchange_source", models.CharField(
                    choices=[
                        ("manual", "Manual"),
                        ("openexchangerates", "Open Exchange Rates"),
                        ("ecb", "European Central Bank"),
                    ],
                    default="manual",
                    max_length=50,
                )),
            ],
            options={"db_table": "geo_currencies", "ordering": ["code"], "verbose_name_plural": "currencies"},
        ),
        migrations.CreateModel(
            name="Language",
            fields=[
                ("code", models.CharField(max_length=10, primary_key=True, serialize=False)),
                ("name_en", models.CharField(max_length=100)),
                ("name_local", models.CharField(max_length=100)),
                ("direction", models.CharField(
                    choices=[("ltr", "Left to Right"), ("rtl", "Right to Left")],
                    default="ltr",
                    max_length=3,
                )),
                ("is_active", models.BooleanField(default=True)),
                ("is_ui_language", models.BooleanField(default=False)),
                ("is_content_language", models.BooleanField(default=False)),
            ],
            options={"db_table": "geo_languages", "ordering": ["name_en"]},
        ),
        migrations.CreateModel(
            name="Market",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("code", models.SlugField(max_length=50, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True, db_index=True)),
                ("is_launch_market", models.BooleanField(default=False)),
                ("default_currency", models.CharField(default="USD", max_length=3)),
                ("default_language", models.CharField(default="en", max_length=10)),
            ],
            options={"db_table": "geo_markets", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Country",
            fields=[
                ("code", models.CharField(max_length=2, primary_key=True, serialize=False)),
                ("code3", models.CharField(max_length=3, unique=True)),
                ("name_en", models.CharField(max_length=100)),
                ("name_local", models.CharField(blank=True, default="", max_length=100)),
                ("region", models.CharField(blank=True, default="", max_length=50)),
                ("subregion", models.CharField(blank=True, default="", max_length=50)),
                ("default_timezone", models.CharField(default="UTC", max_length=50)),
                ("phone_prefix", models.CharField(blank=True, default="", max_length=10)),
                ("is_active", models.BooleanField(default=True, db_index=True)),
                ("is_launch_market", models.BooleanField(default=False)),
                ("market", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="countries",
                    to="geo.market",
                )),
                ("default_language", models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="default_countries",
                    to="geo.language",
                )),
                ("default_currency", models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="default_countries",
                    to="geo.currency",
                )),
            ],
            options={"db_table": "geo_countries", "ordering": ["name_en"], "verbose_name_plural": "countries"},
        ),
        migrations.CreateModel(
            name="CountrySettings",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date_format", models.CharField(default="DD/MM/YYYY", max_length=20)),
                ("time_format", models.CharField(default="24h", max_length=10)),
                ("number_format", models.CharField(default="space_dot", max_length=20)),
                ("vat_rate", models.DecimalField(decimal_places=4, default=0.0, max_digits=5)),
                ("tax_label", models.CharField(default="VAT", max_length=20)),
                ("tax_included_in_price", models.BooleanField(default=False)),
                ("payment_providers", models.JSONField(default=list)),
                ("default_payment_provider", models.CharField(blank=True, default="", max_length=50)),
                ("payment_currencies", models.JSONField(default=list)),
                ("email_provider", models.CharField(default="ses", max_length=50)),
                ("sms_provider", models.CharField(blank=True, default="", max_length=50)),
                ("push_provider", models.CharField(default="fcm", max_length=50)),
                ("requires_gdpr", models.BooleanField(default=False)),
                ("requires_age_verification", models.BooleanField(default=False)),
                ("minimum_age", models.SmallIntegerField(default=13)),
                ("data_residency_required", models.BooleanField(default=False)),
                ("data_residency_region", models.CharField(blank=True, default="", max_length=50)),
                ("terms_url", models.URLField(blank=True, default="")),
                ("privacy_url", models.URLField(blank=True, default="")),
                ("supported_languages", models.JSONField(default=list)),
                ("default_content_language", models.CharField(default="fr", max_length=10)),
                ("country", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="settings",
                    to="geo.country",
                )),
            ],
            options={"db_table": "geo_country_settings", "verbose_name": "Country Settings", "verbose_name_plural": "Country Settings"},
        ),
        migrations.CreateModel(
            name="ExchangeRate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("rate", models.DecimalField(decimal_places=8, max_digits=20)),
                ("source", models.CharField(default="manual", max_length=50)),
                ("fetched_at", models.DateTimeField(auto_now=True)),
                ("from_currency", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="rates_from",
                    to="geo.currency",
                )),
                ("to_currency", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="rates_to",
                    to="geo.currency",
                )),
            ],
            options={"db_table": "geo_exchange_rates"},
        ),
        migrations.AddIndex(
            model_name="exchangerate",
            index=models.Index(fields=["from_currency", "to_currency"], name="geo_exchan_from_cu_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="exchangerate",
            unique_together={("from_currency", "to_currency")},
        ),
    ]