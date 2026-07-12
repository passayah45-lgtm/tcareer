# backend/apps/geo/urls.py

from django.urls import path
from . import views

app_name = "geo"

urlpatterns = [
    # Bootstrap
    path("bootstrap/", views.locale_bootstrap, name="locale_bootstrap"),

    # Markets
    path("markets/", views.market_list, name="market_list"),
    path("markets/<str:code>/", views.market_detail, name="market_detail"),

    # Countries
    path("countries/", views.country_list, name="country_list"),
    path("countries/<str:code>/", views.country_detail, name="country_detail"),
    path("countries/<str:code>/settings/", views.country_settings, name="country_settings"),

    # Currencies
    path("currencies/", views.currency_list, name="currency_list"),
    path("currencies/<str:code>/", views.currency_detail, name="currency_detail"),

    # Languages
    path("languages/", views.language_list, name="language_list"),

    # Exchange rates
    path("rates/<str:from_code>/<str:to_code>/", views.exchange_rate, name="exchange_rate"),
    path("rates/update/", views.update_exchange_rate, name="update_exchange_rate"),
]