import hmac

from django.conf import settings
from rest_framework.exceptions import PermissionDenied


class WebhookSecurityService:
    @staticmethod
    def require_configured_secret(setting_name: str) -> str:
        secret = getattr(settings, setting_name, "")
        if not secret:
            if getattr(settings, "DEBUG", False):
                return ""
            raise PermissionDenied("Webhook secret is not configured.")
        return secret

    @staticmethod
    def verify_static_secret(request, *, setting_name: str, header_name: str = "X-Webhook-Secret") -> None:
        secret = WebhookSecurityService.require_configured_secret(setting_name)
        if not secret and getattr(settings, "DEBUG", False):
            return
        incoming = request.headers.get(header_name, "")
        if not hmac.compare_digest(incoming, secret):
            raise PermissionDenied("Invalid webhook secret.")
