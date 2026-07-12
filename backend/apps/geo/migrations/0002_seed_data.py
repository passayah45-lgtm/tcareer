# backend/apps/geo/migrations/0002_seed_data.py

from django.db import migrations


def seed_languages(apps, schema_editor):
    Language = apps.get_model("geo", "Language")
    languages = [
        {"code": "en",    "name_en": "English",    "name_local": "English",    "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "fr",    "name_en": "French",     "name_local": "Français",   "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "ar",    "name_en": "Arabic",     "name_local": "العربية",    "direction": "rtl", "is_ui_language": True,  "is_content_language": True},
        {"code": "zh-CN", "name_en": "Chinese",    "name_local": "中文",        "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "hi",    "name_en": "Hindi",      "name_local": "हिंदी",       "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "es",    "name_en": "Spanish",    "name_local": "Español",    "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "pt-BR", "name_en": "Portuguese", "name_local": "Português",  "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "sw",    "name_en": "Swahili",    "name_local": "Kiswahili",  "direction": "ltr", "is_ui_language": False, "is_content_language": True},
        {"code": "ha",    "name_en": "Hausa",      "name_local": "Hausa",      "direction": "ltr", "is_ui_language": False, "is_content_language": True},
        {"code": "yo",    "name_en": "Yoruba",     "name_local": "Yorùbá",     "direction": "ltr", "is_ui_language": False, "is_content_language": True},
        {"code": "ig",    "name_en": "Igbo",       "name_local": "Igbo",       "direction": "ltr", "is_ui_language": False, "is_content_language": True},
        {"code": "am",    "name_en": "Amharic",    "name_local": "አማርኛ",       "direction": "ltr", "is_ui_language": False, "is_content_language": True},
        {"code": "de",    "name_en": "German",     "name_local": "Deutsch",    "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "ja",    "name_en": "Japanese",   "name_local": "日本語",      "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
        {"code": "ko",    "name_en": "Korean",     "name_local": "한국어",      "direction": "ltr", "is_ui_language": True,  "is_content_language": True},
    ]
    for lang in languages:
        Language.objects.get_or_create(code=lang["code"], defaults=lang)


def seed_currencies(apps, schema_editor):
    Currency = apps.get_model("geo", "Currency")
    currencies = [
        {"code": "GNF", "name": "Guinean Franc",       "symbol": "GNF",  "symbol_position": "before", "decimal_places": 0, "exchange_source": "manual"},
        {"code": "USD", "name": "US Dollar",            "symbol": "$",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "EUR", "name": "Euro",                 "symbol": "€",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "GBP", "name": "British Pound",        "symbol": "£",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "XOF", "name": "CFA Franc BCEAO",      "symbol": "CFA", "symbol_position": "after",  "decimal_places": 0, "exchange_source": "manual"},
        {"code": "XAF", "name": "CFA Franc BEAC",       "symbol": "CFA", "symbol_position": "after",  "decimal_places": 0, "exchange_source": "manual"},
        {"code": "NGN", "name": "Nigerian Naira",        "symbol": "₦",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "GHS", "name": "Ghanaian Cedi",         "symbol": "₵",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "KES", "name": "Kenyan Shilling",       "symbol": "KSh", "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "ZAR", "name": "South African Rand",   "symbol": "R",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "MAD", "name": "Moroccan Dirham",      "symbol": "MAD", "symbol_position": "after",  "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "EGP", "name": "Egyptian Pound",       "symbol": "E£",  "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "INR", "name": "Indian Rupee",         "symbol": "₹",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "CNY", "name": "Chinese Yuan",         "symbol": "¥",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "BRL", "name": "Brazilian Real",       "symbol": "R$",  "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "CAD", "name": "Canadian Dollar",      "symbol": "CA$", "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "AUD", "name": "Australian Dollar",    "symbol": "A$",  "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "AED", "name": "UAE Dirham",           "symbol": "AED", "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "SAR", "name": "Saudi Riyal",          "symbol": "SAR", "symbol_position": "before", "decimal_places": 2, "exchange_source": "openexchangerates"},
        {"code": "SLL", "name": "Sierra Leonean Leone", "symbol": "Le",  "symbol_position": "before", "decimal_places": 2, "exchange_source": "manual"},
        {"code": "GMD", "name": "Gambian Dalasi",       "symbol": "D",   "symbol_position": "before", "decimal_places": 2, "exchange_source": "manual"},
        {"code": "SEN", "name": "Senegalese Franc",     "symbol": "CFA", "symbol_position": "after",  "decimal_places": 0, "exchange_source": "manual"},
    ]
    for c in currencies:
        Currency.objects.get_or_create(code=c["code"], defaults=c)


def seed_markets(apps, schema_editor):
    Market = apps.get_model("geo", "Market")
    markets = [
        {"name": "Guinea",         "code": "guinea",        "description": "T-Career launch market.",                                         "is_active": True,  "is_launch_market": True,  "default_currency": "GNF", "default_language": "fr"},
        {"name": "West Africa",    "code": "west-africa",   "description": "Francophone and Anglophone West African countries.",               "is_active": True,  "is_launch_market": False, "default_currency": "XOF", "default_language": "fr"},
        {"name": "East Africa",    "code": "east-africa",   "description": "Kenya, Tanzania, Uganda, Ethiopia.",                              "is_active": False, "is_launch_market": False, "default_currency": "KES", "default_language": "en"},
        {"name": "North Africa",   "code": "north-africa",  "description": "Morocco, Egypt, Tunisia, Algeria.",                               "is_active": False, "is_launch_market": False, "default_currency": "MAD", "default_language": "ar"},
        {"name": "Europe",         "code": "europe",        "description": "European Union and United Kingdom.",                              "is_active": False, "is_launch_market": False, "default_currency": "EUR", "default_language": "en"},
        {"name": "North America",  "code": "north-america", "description": "United States and Canada.",                                       "is_active": False, "is_launch_market": False, "default_currency": "USD", "default_language": "en"},
        {"name": "South Asia",     "code": "south-asia",    "description": "India, Pakistan, Bangladesh, Sri Lanka.",                         "is_active": False, "is_launch_market": False, "default_currency": "INR", "default_language": "hi"},
        {"name": "Southeast Asia", "code": "southeast-asia","description": "Indonesia, Vietnam, Philippines, Thailand, Malaysia.",            "is_active": False, "is_launch_market": False, "default_currency": "USD", "default_language": "en"},
        {"name": "Middle East",    "code": "middle-east",   "description": "Gulf countries and Levant region.",                               "is_active": False, "is_launch_market": False, "default_currency": "AED", "default_language": "ar"},
        {"name": "Latin America",  "code": "latin-america", "description": "Brazil, Mexico, Colombia, Argentina and surrounding countries.",  "is_active": False, "is_launch_market": False, "default_currency": "BRL", "default_language": "pt-BR"},
    ]
    for m in markets:
        Market.objects.get_or_create(code=m["code"], defaults=m)


def seed_countries(apps, schema_editor):
    Country = apps.get_model("geo", "Country")
    Market = apps.get_model("geo", "Market")
    Language = apps.get_model("geo", "Language")
    Currency = apps.get_model("geo", "Currency")

    # Shorthand references for common objects
    gn_market  = Market.objects.get(code="guinea")
    wa_market  = Market.objects.get(code="west-africa")
    fr_lang    = Language.objects.get(code="fr")
    en_lang    = Language.objects.get(code="en")
    gnf        = Currency.objects.get(code="GNF")
    xof        = Currency.objects.get(code="XOF")
    usd        = Currency.objects.get(code="USD")

    countries = [
        {"code": "GN", "code3": "GIN", "name_en": "Guinea",         "name_local": "Guinée",          "region": "Africa",   "subregion": "Western Africa",  "market": gn_market,                             "default_language": fr_lang,                        "default_currency": gnf,                              "default_timezone": "Africa/Conakry",   "phone_prefix": "+224", "is_active": True,  "is_launch_market": True},
        {"code": "SN", "code3": "SEN", "name_en": "Senegal",         "name_local": "Sénégal",         "region": "Africa",   "subregion": "Western Africa",  "market": wa_market,                             "default_language": fr_lang,                        "default_currency": xof,                              "default_timezone": "Africa/Dakar",     "phone_prefix": "+221", "is_active": True,  "is_launch_market": False},
        {"code": "CI", "code3": "CIV", "name_en": "Ivory Coast",     "name_local": "Côte d'Ivoire",   "region": "Africa",   "subregion": "Western Africa",  "market": wa_market,                             "default_language": fr_lang,                        "default_currency": xof,                              "default_timezone": "Africa/Abidjan",   "phone_prefix": "+225", "is_active": True,  "is_launch_market": False},
        {"code": "ML", "code3": "MLI", "name_en": "Mali",            "name_local": "Mali",            "region": "Africa",   "subregion": "Western Africa",  "market": wa_market,                             "default_language": fr_lang,                        "default_currency": xof,                              "default_timezone": "Africa/Bamako",    "phone_prefix": "+223", "is_active": True,  "is_launch_market": False},
        {"code": "BF", "code3": "BFA", "name_en": "Burkina Faso",    "name_local": "Burkina Faso",    "region": "Africa",   "subregion": "Western Africa",  "market": wa_market,                             "default_language": fr_lang,                        "default_currency": xof,                              "default_timezone": "Africa/Ouagadougou","phone_prefix": "+226", "is_active": True,  "is_launch_market": False},
        {"code": "GH", "code3": "GHA", "name_en": "Ghana",           "name_local": "Ghana",           "region": "Africa",   "subregion": "Western Africa",  "market": wa_market,                             "default_language": en_lang,                        "default_currency": Currency.objects.get(code="GHS"), "default_timezone": "Africa/Accra",     "phone_prefix": "+233", "is_active": True,  "is_launch_market": False},
        {"code": "NG", "code3": "NGA", "name_en": "Nigeria",         "name_local": "Nigeria",         "region": "Africa",   "subregion": "Western Africa",  "market": wa_market,                             "default_language": en_lang,                        "default_currency": Currency.objects.get(code="NGN"), "default_timezone": "Africa/Lagos",     "phone_prefix": "+234", "is_active": True,  "is_launch_market": False},
        {"code": "US", "code3": "USA", "name_en": "United States",   "name_local": "United States",   "region": "Americas", "subregion": "Northern America", "market": Market.objects.get(code="north-america"), "default_language": en_lang,                        "default_currency": usd,                              "default_timezone": "America/New_York", "phone_prefix": "+1",   "is_active": True,  "is_launch_market": False},
        {"code": "FR", "code3": "FRA", "name_en": "France",          "name_local": "France",          "region": "Europe",   "subregion": "Western Europe",   "market": Market.objects.get(code="europe"),       "default_language": fr_lang,                        "default_currency": Currency.objects.get(code="EUR"), "default_timezone": "Europe/Paris",     "phone_prefix": "+33",  "is_active": True,  "is_launch_market": False},
        {"code": "GB", "code3": "GBR", "name_en": "United Kingdom",  "name_local": "United Kingdom",  "region": "Europe",   "subregion": "Northern Europe",  "market": Market.objects.get(code="europe"),       "default_language": en_lang,                        "default_currency": Currency.objects.get(code="GBP"), "default_timezone": "Europe/London",    "phone_prefix": "+44",  "is_active": True,  "is_launch_market": False},
        {"code": "IN", "code3": "IND", "name_en": "India",           "name_local": "भारत",            "region": "Asia",     "subregion": "Southern Asia",    "market": Market.objects.get(code="south-asia"),    "default_language": Language.objects.get(code="hi"), "default_currency": Currency.objects.get(code="INR"), "default_timezone": "Asia/Kolkata",     "phone_prefix": "+91",  "is_active": True,  "is_launch_market": False},
    ]

    for c in countries:
        Country.objects.get_or_create(code=c["code"], defaults=c)


def seed_guinea_settings(apps, schema_editor):
    CountrySettings = apps.get_model("geo", "CountrySettings")
    Country = apps.get_model("geo", "Country")

    guinea = Country.objects.get(code="GN")

    CountrySettings.objects.get_or_create(
        country=guinea,
        defaults={
            "date_format": "DD/MM/YYYY",
            "time_format": "24h",
            "number_format": "space_dot",
            "vat_rate": "0.1800",
            "tax_label": "TVA",
            "tax_included_in_price": False,
            "payment_providers": ["orange_money", "mtn_money"],
            "default_payment_provider": "orange_money",
            "payment_currencies": ["GNF", "USD"],
            "email_provider": "ses",
            "sms_provider": "orange_api",
            "push_provider": "fcm",
            "requires_gdpr": False,
            "requires_age_verification": False,
            "minimum_age": 13,
            "data_residency_required": False,
            "data_residency_region": "",
            "supported_languages": ["fr", "en"],
            "default_content_language": "fr",
        }
    )


def seed_exchange_rates(apps, schema_editor):
    ExchangeRate = apps.get_model("geo", "ExchangeRate")
    Currency = apps.get_model("geo", "Currency")

    rates = [
        ("GNF", "USD", "0.00011765"),
        ("USD", "GNF", "8500.00000000"),
        ("GNF", "EUR", "0.00010870"),
        ("EUR", "GNF", "9200.00000000"),
        ("GNF", "XOF", "0.09600000"),
        ("XOF", "GNF", "10.41666667"),
        ("USD", "EUR", "0.92000000"),
        ("EUR", "USD", "1.08695652"),
        ("USD", "GBP", "0.79000000"),
        ("GBP", "USD", "1.26582278"),
        ("USD", "NGN", "1580.00000000"),
        ("USD", "GHS", "15.50000000"),
        ("USD", "KES", "129.00000000"),
        ("USD", "INR", "83.50000000"),
        ("USD", "CNY", "7.24000000"),
        ("USD", "BRL", "4.97000000"),
        ("USD", "MAD", "10.05000000"),
        ("USD", "EGP", "48.50000000"),
        ("USD", "AED", "3.67000000"),
        ("USD", "SAR", "3.75000000"),
    ]

    for from_code, to_code, rate in rates:
        try:
            from_currency = Currency.objects.get(code=from_code)
            to_currency = Currency.objects.get(code=to_code)
            ExchangeRate.objects.get_or_create(
                from_currency=from_currency,
                to_currency=to_currency,
                defaults={"rate": rate, "source": "manual"},
            )
        except Currency.DoesNotExist:
            pass


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    initial = False
    dependencies = [
        ("geo", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_languages, reverse_seed),
        migrations.RunPython(seed_currencies, reverse_seed),
        migrations.RunPython(seed_markets, reverse_seed),
        migrations.RunPython(seed_countries, reverse_seed),
        migrations.RunPython(seed_guinea_settings, reverse_seed),
        migrations.RunPython(seed_exchange_rates, reverse_seed),
    ]