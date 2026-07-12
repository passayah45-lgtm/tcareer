from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.list_notifications, name="list"),
    path("preferences/", views.notification_preferences, name="preferences"),
    path("delivery-history/", views.delivery_history, name="delivery-history"),
    path("email/provider-webhook/", views.email_provider_webhook, name="email-provider-webhook"),
    path("unsubscribe/", views.unsubscribe, name="unsubscribe"),
    path("resubscribe/", views.resubscribe, name="resubscribe"),
    path("unsubscribe/<str:token>/", views.unsubscribe_token, name="unsubscribe-token"),
    path("read-all/", views.mark_all_read, name="read-all"),
    path("<uuid:notification_id>/read/", views.mark_read, name="read"),
]
