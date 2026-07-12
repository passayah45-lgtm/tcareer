import logging
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .services import PaymentService
from .models import Subscription
from common.webhooks import WebhookSecurityService

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    POST /api/v1/payments/checkout/

    Creates a Stripe Checkout session and returns the redirect URL.
    Frontend redirects the user to this URL to complete payment.

    Response: { "checkout_url": "https://checkout.stripe.com/..." }
    """
    frontend_url = settings.FRONTEND_URL
    success_url = f"{frontend_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{frontend_url}/payment/cancelled"

    try:
        checkout_url = PaymentService.create_checkout_session(
            user=request.user,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return Response({"checkout_url": checkout_url})
    except Exception as exc:
        logger.error("Checkout session creation failed: %s", exc)
        return Response(
            {"detail": "Could not create payment session. Please try again."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_billing_portal(request):
    """
    POST /api/v1/payments/billing-portal/

    Creates a Stripe billing portal session so the user can
    manage their subscription or update their payment method.
    """
    return_url = f"{settings.FRONTEND_URL}/dashboard"
    try:
        portal_url = PaymentService.create_billing_portal_session(
            user=request.user,
            return_url=return_url,
        )
        return Response({"portal_url": portal_url})
    except Exception as exc:
        logger.error("Billing portal creation failed: %s", exc)
        return Response(
            {"detail": "Could not open billing portal. Please try again."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """
    GET /api/v1/payments/subscription/

    Returns the authenticated user's current subscription status.
    """
    sub = Subscription.objects.filter(user=request.user).order_by("-created_at").first()
    if not sub:
        return Response({
            "has_subscription": False,
            "status": None,
            "plan": None,
            "current_period_end": None,
        })
    return Response({
        "has_subscription": True,
        "is_active": sub.is_active,
        "status": sub.status,
        "plan": sub.plan,
        "current_period_end": sub.current_period_end,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    POST /api/v1/payments/webhook/

    Receives and processes Stripe webhook events.
    Stripe signature is validated before any processing occurs.
    This endpoint must be excluded from CSRF protection.
    """
    import stripe

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        WebhookSecurityService.require_configured_secret("STRIPE_WEBHOOK_SECRET")
    except Exception:
        logger.error("Stripe webhook secret is not configured.")
        return Response(status=status.HTTP_403_FORBIDDEN)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.warning("Stripe webhook: invalid payload")
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook: invalid signature")
        return Response(status=status.HTTP_400_BAD_REQUEST)

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        PaymentService.handle_checkout_complete(data)

    elif event_type == "customer.subscription.updated":
        PaymentService.handle_subscription_updated(data)

    elif event_type == "customer.subscription.deleted":
        PaymentService.handle_subscription_deleted(data)

    else:
        logger.debug("Unhandled Stripe event: %s", event_type)

    return Response({"received": True})
