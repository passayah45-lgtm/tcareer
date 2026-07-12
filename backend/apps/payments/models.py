"""
Payment models for T-Career Stripe integration.

One subscription plan at MVP: $19/month, unlimited course access.
The Subscription model mirrors the Stripe subscription object.
We store enough data locally to check subscription status without
hitting the Stripe API on every request.

stripe_customer_id: stored so we can look up the customer in Stripe
    for refunds, plan changes, and billing portal access.

stripe_subscription_id: stored so we can cancel or modify the
    subscription via the Stripe API when needed.

current_period_end: stored so we can show the student when their
    access expires after cancellation. Also used to gate course
    access during the grace period after cancellation.
"""

from django.conf import settings
from django.db import models
from common.models import BaseModel


class SubscriptionPlan(models.TextChoices):
    PRO = "pro", "Pro"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CANCELLED = "cancelled", "Cancelled"
    PAST_DUE = "past_due", "Past Due"
    UNPAID = "unpaid", "Unpaid"
    TRIALING = "trialing", "Trialing"


class Subscription(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        db_index=True,
    )
    stripe_customer_id = models.CharField(max_length=100, db_index=True)
    stripe_subscription_id = models.CharField(max_length=100, unique=True, db_index=True)
    plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.PRO,
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
        db_index=True,
    )
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscriptions"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["stripe_subscription_id"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.status})"

    @property
    def is_active(self):
        from django.utils import timezone
        return (
            self.status == SubscriptionStatus.ACTIVE
            and self.current_period_end > timezone.now()
        )
