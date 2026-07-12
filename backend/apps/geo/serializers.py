# backend/apps/geo/serializers.py

from rest_framework import serializers
from .models import Market, Country, Currency, Language, CountrySettings, ExchangeRate


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            "code",
            "name",
            "symbol",
            "symbol_position",
            "decimal_places",
            "is_active",
        ]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "code",
            "name_en",
            "name_local",
            "direction",
            "is_ui_language",
            "is_content_language",
        ]


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = [
            "id",
            "name",
            "code",
            "description",
            "is_active",
            "is_launch_market",
            "default_currency",
            "default_language",
        ]


class CountrySerializer(serializers.ModelSerializer):
    market = MarketSerializer(read_only=True)
    default_language = LanguageSerializer(read_only=True)
    default_currency = CurrencySerializer(read_only=True)

    class Meta:
        model = Country
        fields = [
            "code",
            "code3",
            "name_en",
            "name_local",
            "region",
            "subregion",
            "market",
            "default_language",
            "default_currency",
            "default_timezone",
            "phone_prefix",
            "is_active",
            "is_launch_market",
        ]


class CountrySettingsSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = CountrySettings
        fields = [
            "id",
            "country",
            "date_format",
            "time_format",
            "number_format",
            "vat_rate",
            "tax_label",
            "tax_included_in_price",
            "payment_providers",
            "default_payment_provider",
            "payment_currencies",
            "email_provider",
            "sms_provider",
            "requires_gdpr",
            "requires_age_verification",
            "minimum_age",
            "supported_languages",
            "default_content_language",
        ]


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = [
            "id",
            "from_currency",
            "to_currency",
            "rate",
            "source",
            "fetched_at",
        ]


class CountryListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for dropdowns and selects.
    Used in user profile forms and job posting forms.
    """
    class Meta:
        model = Country
        fields = [
            "code",
            "name_en",
            "name_local",
            "phone_prefix",
            "default_timezone",
        ]