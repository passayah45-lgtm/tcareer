import hashlib
import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from common.models import BaseModel


class PasswordResetToken(BaseModel):
    """
    Time-limited single-use token for password reset.

    We store a SHA-256 hash of the token, not the token itself.
    The plaintext token is sent in the email link and never stored.
    This prevents database breaches from exposing valid reset tokens.

    Token lifetime: 1 hour.
    Single use: used_at is set on consumption, subsequent uses are rejected.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    TOKEN_LIFETIME_HOURS = 1

    class Meta:
        db_table = "password_reset_tokens"

    def __str__(self):
        return f"Reset token for {self.user.email} (expires {self.expires_at})"

    @classmethod
    def create_for_user(cls, user) -> str:
        """
        Generate a new reset token for a user.
        Invalidates any existing unused tokens.
        Returns the plaintext token (to be sent in the email).
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
        """
        Validate a plaintext token.
        Returns the PasswordResetToken if valid, None otherwise.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            reset_token = cls.objects.select_related("user").get(token_hash=token_hash)
        except cls.DoesNotExist:
            return None

        if reset_token.used_at is not None:
            return None

        if reset_token.expires_at < timezone.now():
            return None

        return reset_token

    def consume(self) -> None:
        """Mark the token as used. After this it cannot be used again."""
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
