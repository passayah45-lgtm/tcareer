import logging
from django.conf import settings
from django.utils import timezone
from common.audit import AuditService

logger = logging.getLogger(__name__)


def get_stripe():
    """Lazy import Stripe to avoid import errors when key is not configured."""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


class PaymentService:

    PLAN_PRICE_ID = getattr(settings, "STRIPE_PRICE_ID", "")

    @staticmethod
    def create_checkout_session(user, success_url: str, cancel_url: str) -> str:
        """
        Create a Stripe Checkout session for the Pro subscription.
        Returns the Checkout session URL to redirect the user to.
        """
        stripe = get_stripe()

        # Retrieve or create a Stripe customer for this user
        customer_id = PaymentService._get_or_create_customer(user)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": PaymentService.PLAN_PRICE_ID,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user.id)},
            subscription_data={
                "metadata": {"user_id": str(user.id)},
            },
        )
        logger.info("Checkout session created for user %s", user.email)
        return session.url

    @staticmethod
    def _get_or_create_customer(user) -> str:
        """
        Look up an existing Stripe customer by email or create a new one.
        We search by email rather than storing the customer ID before payment
        to avoid orphaned customers when users abandon checkout.
        """
        stripe = get_stripe()
        from apps.payments.models import Subscription

        existing = Subscription.objects.filter(user=user).first()
        if existing and existing.stripe_customer_id:
            return existing.stripe_customer_id

        customers = stripe.Customer.list(email=user.email, limit=1)
        if customers.data:
            return customers.data[0].id

        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={"user_id": str(user.id)},
        )
        return customer.id

    @staticmethod
    def handle_checkout_complete(session: dict) -> None:
        """
        Called when Stripe fires checkout.session.completed event.
        Creates or updates the Subscription record for the user.
        """
        from apps.payments.models import Subscription, SubscriptionStatus
        from apps.users.models import User
        import datetime

        user_id = session.get("metadata", {}).get("user_id")
        if not user_id:
            logger.error("checkout.session.completed missing user_id in metadata")
            return

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error("User %s not found for checkout completion", user_id)
            return

        stripe = get_stripe()
        subscription = stripe.Subscription.retrieve(session["subscription"])
        period_end = datetime.datetime.fromtimestamp(
            subscription["current_period_end"], tz=timezone.utc
        )

        subscription_record, _ = Subscription.objects.update_or_create(
            stripe_subscription_id=subscription["id"],
            defaults={
                "user": user,
                "stripe_customer_id": session["customer"],
                "status": SubscriptionStatus.ACTIVE,
                "current_period_end": period_end,
            },
        )
        AuditService.record(
            actor=user,
            action="entitlement_subscription_purchased",
            target=subscription_record,
            metadata={"provider": "stripe", "stripe_subscription_id": subscription["id"]},
        )
        logger.info("Subscription activated for user %s", user.email)

    @staticmethod
    def handle_subscription_updated(subscription: dict) -> None:
        """
        Called when Stripe fires customer.subscription.updated event.
        Keeps our local subscription record in sync.
        """
        from apps.payments.models import Subscription, SubscriptionStatus
        import datetime

        try:
            sub = Subscription.objects.get(
                stripe_subscription_id=subscription["id"]
            )
        except Subscription.DoesNotExist:
            logger.warning(
                "Subscription %s not found locally for update", subscription["id"]
            )
            return

        period_end = datetime.datetime.fromtimestamp(
            subscription["current_period_end"], tz=timezone.utc
        )
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "cancelled": SubscriptionStatus.CANCELLED,
            "past_due": SubscriptionStatus.PAST_DUE,
            "unpaid": SubscriptionStatus.UNPAID,
            "trialing": SubscriptionStatus.TRIALING,
        }
        sub.status = status_map.get(subscription["status"], SubscriptionStatus.PAST_DUE)
        sub.current_period_end = period_end
        sub.save(update_fields=["status", "current_period_end", "updated_at"])
        AuditService.record(
            actor=sub.user,
            action="entitlement_subscription_updated",
            target=sub,
            metadata={"provider": "stripe", "stripe_subscription_id": subscription["id"]},
        )
        logger.info("Subscription updated: %s -> %s", subscription["id"], sub.status)

    @staticmethod
    def handle_subscription_deleted(subscription: dict) -> None:
        """
        Called when Stripe fires customer.subscription.deleted event.
        Marks the subscription as cancelled.
        """
        from apps.payments.models import Subscription, SubscriptionStatus

        try:
            sub = Subscription.objects.get(
                stripe_subscription_id=subscription["id"]
            )
            sub.status = SubscriptionStatus.CANCELLED
            sub.cancelled_at = timezone.now()
            sub.save(update_fields=["status", "cancelled_at", "updated_at"])
            AuditService.record(
                actor=sub.user,
                action="entitlement_subscription_cancelled",
                target=sub,
                metadata={"provider": "stripe", "stripe_subscription_id": subscription["id"]},
            )
            logger.info("Subscription cancelled: %s", subscription["id"])
        except Subscription.DoesNotExist:
            logger.warning(
                "Subscription %s not found for deletion", subscription["id"]
            )

    @staticmethod
    def create_billing_portal_session(user, return_url: str) -> str:
        """
        Create a Stripe billing portal session.
        Lets users manage their subscription, update payment methods, and cancel.
        """
        stripe = get_stripe()
        customer_id = PaymentService._get_or_create_customer(user)
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
