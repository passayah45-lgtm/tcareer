from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", views.TokenRefreshWithUserView.as_view(), name="token-refresh"),
    path("logout/", views.logout, name="logout"),
    path("google/", views.google_auth, name="google-auth"),
    path("me/", views.me, name="me"),
    path("me/update/", views.update_profile, name="update-profile"),
    path("privacy/", views.privacy_settings, name="privacy-settings"),
    path("change-password/", views.change_password, name="change-password"),
    path("forgot-password/", views.forgot_password, name="forgot-password"),
    path("reset-password/", views.reset_password, name="reset-password"),
    path("verify-email/", views.verify_email, name="verify-email"),
    path("resend-verification/", views.resend_verification, name="resend-verification"),
    path("profile/<slug:username>/", views.public_profile, name="public-profile"),
]
