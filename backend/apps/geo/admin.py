
from django.contrib import admin
from .models import Market, Country, Currency, Language, CountrySettings, ExchangeRate


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "default_currency", "default_language", "is_active", "is_launch_market"]
    search_fields = ["name", "code"]
    list_filter = ["is_active", "is_launch_market"]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["code", "name_en", "market", "default_currency", "default_language", "is_active"]
    search_fields = ["code", "name_en"]
    list_filter = ["is_active", "is_launch_market", "market"]


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "symbol", "decimal_places", "is_active"]
    search_fields = ["code", "name"]


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["code", "name_en", "name_local", "direction", "is_ui_language", "is_content_language"]
    search_fields = ["code", "name_en"]


@admin.register(CountrySettings)
class CountrySettingsAdmin(admin.ModelAdmin):
    list_display = ["country", "vat_rate", "tax_label", "default_payment_provider", "email_provider"]
    search_fields = ["country__name_en", "country__code"]


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ["from_currency", "to_currency", "rate", "source", "fetched_at"]
    list_filter = ["source"]