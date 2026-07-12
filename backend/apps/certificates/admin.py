from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["cert_number", "user", "course", "is_revoked", "issued_at"]
    list_filter = ["is_revoked"]
    search_fields = ["cert_number", "user__email", "course__title"]
    readonly_fields = ["id", "cert_number", "issued_at", "pdf_url"]
