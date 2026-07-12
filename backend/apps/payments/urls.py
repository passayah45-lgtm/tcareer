from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("checkout/", views.create_checkout_session, name="checkout"),
    path("billing-portal/", views.create_billing_portal, name="billing-portal"),
    path("subscription/", views.subscription_status, name="subscription-status"),
    path("webhook/", views.stripe_webhook, name="stripe-webhook"),
]
