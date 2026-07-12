from django.urls import path
from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.my_certificates, name="my-certificates"),
    path("verify/<str:cert_number>/", views.verify_certificate, name="verify"),
]
