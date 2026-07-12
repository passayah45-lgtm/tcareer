# backend/apps/geo/models.py

import uuid
from django.db import models
from common.models import BaseModel


class Market(BaseModel):
    """
    A Market represents a business region for T-Career.
    Markets group countries for pricing, content, and go-to-market strategy.
    Examples: West Africa, Europe, South Asia, North America.
    A country belongs to one primary market.
    """

    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    is_launch_market = models.BooleanField(default=False)
    default_currency = models.CharField(max_length=3, default="USD")
    default_language = models.CharField(max_length=10, default="en")

    class Meta:
        db_table = "geo_markets"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Currency(models.Model):
    """
    ISO 4217 currency definitions.
    Not using BaseModel here since currencies are reference data,
    not business objects requiring UUID or audit timestamps.
    """

    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    symbol_position = models.CharField(
        max_length=6,
        choices=[("before", "Before"), ("after", "After")],
        default="before",
    )
    decimal_places = models.SmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    exchange_source = models.CharField(
        max_length=50,
        choices=[
            ("manual", "Manual"),
            ("openexchangerates", "Open Exchange Rates"),
            ("ecb", "European Central Bank"),
        ],
        default="manual",
    )

    class Meta:
        db_table = "geo_currencies"
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self) -> str:
        return f"{self.code} ({self.symbol})"


class Language(models.Model):
    """
    BCP 47 language codes supported by T-Career.
    Tracks whether a language is available for UI, course content, or both.
    """

    code = models.CharField(max_length=10, primary_key=True)
    name_en = models.CharField(max_length=100)
    name_local = models.CharField(max_length=100)
    direction = models.CharField(
        max_length=3,
        choices=[("ltr", "Left to Right"), ("rtl", "Right to Left")],
        default="ltr",
    )
    is_active = models.BooleanField(default=True)
    is_ui_language = models.BooleanField(
        default=False,
        help_text="Available as a platform UI language.",
    )
    is_content_language = models.BooleanField(
        default=False,
        help_text="Available for course content translation.",
    )

    class Meta:
        db_table = "geo_languages"
        ordering = ["name_en"]

    def __str__(self) -> str:
        return f"{self.name_en} ({self.code})"


class Country(models.Model):
    """
    ISO 3166-1 country definitions with T-Career platform configuration.
    Countries belong to a Market and carry locale defaults.
    No BaseModel here: countries are reference data, not user-created objects.
    """

    code = models.CharField(max_length=2, primary_key=True)
    code3 = models.CharField(max_length=3, unique=True)
    name_en = models.CharField(max_length=100)
    name_local = models.CharField(max_length=100, blank=True, default="")
    region = models.CharField(max_length=50, blank=True, default="")
    subregion = models.CharField(max_length=50, blank=True, default="")
    market = models.ForeignKey(
        Market,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="countries",
    )
    default_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        related_name="default_countries",
    )
    default_currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        related_name="default_countries",
    )
    default_timezone = models.CharField(max_length=50, default="UTC")
    phone_prefix = models.CharField(max_length=10, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    is_launch_market = models.BooleanField(default=False)

    class Meta:
        db_table = "geo_countries"
        ordering = ["name_en"]
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return f"{self.name_en} ({self.code})"


class CountrySettings(BaseModel):
    """
    All country-specific platform configuration in one table.
    Nothing is hardcoded: tax, payments, providers, legal rules
    all live here. Adding a new country means inserting a row.
    """

    country = models.OneToOneField(
        Country,
        on_delete=models.CASCADE,
        related_name="settings",
    )

    # Date and number formatting
    date_format = models.CharField(max_length=20, default="DD/MM/YYYY")
    time_format = models.CharField(max_length=10, default="24h")
    number_format = models.CharField(
        max_length=10,
        default="space_comma",
        help_text="space_comma: 1 000,00 | comma_dot: 1,000.00",
    )

    # Tax configuration
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.0,
        help_text="e.g. 0.18 for 18 percent VAT",
    )
    tax_label = models.CharField(
        max_length=20,
        default="VAT",
        help_text="Label shown to user: VAT, GST, TVA, etc.",
    )
    tax_included_in_price = models.BooleanField(default=False)

    # Payment configuration
    payment_providers = models.JSONField(
        default=list,
        help_text='Ordered list of provider keys: ["orange_money", "stripe"]',
    )
    default_payment_provider = models.CharField(max_length=50, blank=True, default="")
    payment_currencies = models.JSONField(
        default=list,
        help_text='Currencies accepted for payment: ["GNF", "USD"]',
    )

    # Communication providers
    email_provider = models.CharField(
        max_length=50,
        default="ses",
        help_text="ses, sendgrid, mailgun",
    )
    sms_provider = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="twilio, orange_api, mtn_api",
    )
    push_provider = models.CharField(
        max_length=50,
        default="fcm",
        help_text="fcm, apns",
    )

    # Legal and compliance
    requires_gdpr = models.BooleanField(default=False)
    requires_age_verification = models.BooleanField(default=False)
    minimum_age = models.SmallIntegerField(default=13)
    data_residency_required = models.BooleanField(default=False)
    data_residency_region = models.CharField(max_length=50, blank=True, default="")
    terms_url = models.URLField(blank=True, default="")
    privacy_url = models.URLField(blank=True, default="")

    # Content
    supported_languages = models.JSONField(
        default=list,
        help_text='Languages available in this country: ["fr", "en"]',
    )
    default_content_language = models.CharField(max_length=10, default="fr")

    class Meta:
        db_table = "geo_country_settings"
        verbose_name = "Country Settings"
        verbose_name_plural = "Country Settings"

    def __str__(self) -> str:
        return f"Settings for {self.country.name_en}"

    def get_payment_providers(self) -> list:
        return self.payment_providers or []

    def get_primary_payment_provider(self) -> str:
        providers = self.get_payment_providers()
        return providers[0] if providers else ""

    def apply_tax(self, amount) -> object:
        from decimal import Decimal
        return amount * (1 + Decimal(str(self.vat_rate)))


class ExchangeRate(BaseModel):
    """
    Stores exchange rates between currency pairs.
    Updated by a Celery beat task from configured exchange_source.
    Last-write-wins: always use the most recently fetched rate.
    """

    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="rates_from",
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="rates_to",
    )
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    source = models.CharField(max_length=50, default="manual")
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "geo_exchange_rates"
        unique_together = [("from_currency", "to_currency")]
        indexes = [
            models.Index(fields=["from_currency", "to_currency"]),
        ]

    def __str__(self) -> str:
        return f"1 {self.from_currency_id} = {self.rate} {self.to_currency_id}"