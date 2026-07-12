from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Market, Country, Currency, Language, CountrySettings, ExchangeRate
from .serializers import (
    MarketSerializer,
    CountrySerializer,
    CountryListSerializer,
    CurrencySerializer,
    LanguageSerializer,
    CountrySettingsSerializer,
    ExchangeRateSerializer,
)


# Markets 

@api_view(["GET"])
@permission_classes([AllowAny])
def market_list(request):
    """List all active markets."""
    markets = Market.objects.filter(is_active=True).order_by("name")
    serializer = MarketSerializer(markets, many=True)
    return Response({"success": True, "data": serializer.data})


@api_view(["GET"])
@permission_classes([AllowAny])
def market_detail(request, code):
    """Get a single market by code."""
    market = get_object_or_404(Market, code=code, is_active=True)
    serializer = MarketSerializer(market)
    return Response({"success": True, "data": serializer.data})


# Countries 

@api_view(["GET"])
@permission_classes([AllowAny])
def country_list(request):
    """
    List all active countries.
    Accepts ?market=west-africa to filter by market.
    Accepts ?lightweight=true for dropdown use.
    """
    queryset = Country.objects.filter(is_active=True).select_related(
        "market", "default_language", "default_currency"
    )

    market_code = request.query_params.get("market")
    if market_code:
        queryset = queryset.filter(market__code=market_code)

    lightweight = request.query_params.get("lightweight") == "true"

    if lightweight:
        serializer = CountryListSerializer(queryset, many=True)
    else:
        serializer = CountrySerializer(queryset, many=True)

    return Response({"success": True, "data": serializer.data})


@api_view(["GET"])
@permission_classes([AllowAny])
def country_detail(request, code):
    """Get a single country by ISO 3166-1 alpha-2 code."""
    country = get_object_or_404(
        Country.objects.select_related("market", "default_language", "default_currency"),
        code=code.upper(),
        is_active=True,
    )
    serializer = CountrySerializer(country)
    return Response({"success": True, "data": serializer.data})


@api_view(["GET"])
@permission_classes([AllowAny])
def country_settings(request, code):
    """Get platform configuration for a specific country."""
    country = get_object_or_404(Country, code=code.upper(), is_active=True)
    settings = get_object_or_404(CountrySettings, country=country)
    serializer = CountrySettingsSerializer(settings)
    return Response({"success": True, "data": serializer.data})


#  Currencies 

@api_view(["GET"])
@permission_classes([AllowAny])
def currency_list(request):
    """List all active currencies."""
    currencies = Currency.objects.filter(is_active=True).order_by("code")
    serializer = CurrencySerializer(currencies, many=True)
    return Response({"success": True, "data": serializer.data})


@api_view(["GET"])
@permission_classes([AllowAny])
def currency_detail(request, code):
    """Get a single currency by ISO 4217 code."""
    currency = get_object_or_404(Currency, code=code.upper(), is_active=True)
    serializer = CurrencySerializer(currency)
    return Response({"success": True, "data": serializer.data})


#  Languages 

@api_view(["GET"])
@permission_classes([AllowAny])
def language_list(request):
    """
    List all active languages.
    Accepts ?ui=true to return only UI languages.
    Accepts ?content=true to return only content languages.
    """
    queryset = Language.objects.filter(is_active=True)

    if request.query_params.get("ui") == "true":
        queryset = queryset.filter(is_ui_language=True)

    if request.query_params.get("content") == "true":
        queryset = queryset.filter(is_content_language=True)

    serializer = LanguageSerializer(queryset, many=True)
    return Response({"success": True, "data": serializer.data})


#  Exchange Rates 

@api_view(["GET"])
@permission_classes([AllowAny])
def exchange_rate(request, from_code, to_code):
    """Get the exchange rate between two currencies."""
    rate = get_object_or_404(
        ExchangeRate,
        from_currency=from_code.upper(),
        to_currency=to_code.upper(),
    )
    serializer = ExchangeRateSerializer(rate)
    return Response({"success": True, "data": serializer.data})


# Platform locale bootstrap 

@api_view(["GET"])
@permission_classes([AllowAny])
def locale_bootstrap(request):
    """
    Single endpoint the frontend calls on startup.
    Returns all countries, currencies, and languages needed
    to populate dropdowns and detect user locale.
    """
    countries = Country.objects.filter(is_active=True).select_related(
        "market", "default_language", "default_currency"
    )
    currencies = Currency.objects.filter(is_active=True)
    languages = Language.objects.filter(is_active=True)
    markets = Market.objects.filter(is_active=True)

    return Response({
        "success": True,
        "data": {
            "countries": CountryListSerializer(countries, many=True).data,
            "currencies": CurrencySerializer(currencies, many=True).data,
            "languages": LanguageSerializer(languages, many=True).data,
            "markets": MarketSerializer(markets, many=True).data,
        }
    })


# Admin only 

@api_view(["POST"])
@permission_classes([IsAdminUser])
def update_exchange_rate(request):
    """
    Manually update an exchange rate.
    Admin only. Automated updates come from Celery beat task.
    """
    from_code = request.data.get("from_currency", "").upper()
    to_code = request.data.get("to_currency", "").upper()
    rate_value = request.data.get("rate")

    if not from_code or not to_code or rate_value is None:
        return Response(
            {"success": False, "error": "from_currency, to_currency, and rate are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from_currency = get_object_or_404(Currency, code=from_code)
    to_currency = get_object_or_404(Currency, code=to_code)

    rate, created = ExchangeRate.objects.update_or_create(
        from_currency=from_currency,
        to_currency=to_currency,
        defaults={"rate": rate_value, "source": "manual"},
    )

    serializer = ExchangeRateSerializer(rate)
    return Response({
        "success": True,
        "data": serializer.data,
        "created": created,
    })