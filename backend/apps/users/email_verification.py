import hashlib
import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from common.models import BaseModel


class EmailVerificationToken(BaseModel):
    """
    Time-limited single-use token for email verification.

    Same pattern as PasswordResetToken:
    - SHA-256 hash stored, plaintext sent in email
    - Expires after 24 hours
    - Single use enforced by used_at field
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    TOKEN_LIFETIME_HOURS = 24

    class Meta:
        db_table = "email_verification_tokens"

    def __str__(self):
        return f"Verification token for {self.user.email}"

    @classmethod
    def create_for_user(cls, user) -> str:
        """
        Generate a new verification token for a user.
        Invalidates any existing unused tokens.
        Returns the plaintext token to be sent in the email.
        """
        cls.objects.filter(user=user, used_at=None).delete()
        plaintext = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        cls.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=cls.TOKEN_LIFETIME_HOURS),
        )
        return plaintext

    @classmethod
    def validate(cls, token: str):
        """Validate a plaintext token. Returns the token object if valid."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            obj = cls.objects.select_related("user").get(token_hash=token_hash)
        except cls.DoesNotExist:
            return None
        if obj.used_at is not None:
            return None
        if obj.expires_at < timezone.now():
            return None
        return obj

    def consume(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
