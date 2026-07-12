import logging
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from common.exceptions import ServiceError, ConflictError
from .models import User, UserRole, OAuthAccount

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
TOKEN_DENYLIST_PREFIX = "revoked_token:"
TOKEN_DENYLIST_TTL = 60 * 60 * 24 * 8  # 8 days, slightly longer than refresh token lifetime


class AuthService:
    """
    Handles all authentication business logic.
    Views call these methods. Services do not import from views.
    """

    @staticmethod
    def register(
        email: str,
        password: str,
        full_name: str,
        role: str = UserRole.STUDENT,
    ) -> User:
        """
        Create a new user account.
        Raises ConflictError if the email is already registered.
        """
        if User.objects.filter(email=email.lower().strip()).exists():
            raise ConflictError("An account with this email already exists.")

        user = User.objects.create_user(
            email=email.lower().strip(),
            password=password,
            full_name=full_name.strip(),
            role=role,
        )
        logger.info("New user registered: %s (role=%s)", user.email, user.role)
        return user

    @staticmethod
    def issue_tokens(user: User) -> dict[str, Any]:
        """
        Issue a JWT access/refresh token pair for the given user.
        The refresh token is rotated on each use (configured in settings).
        """
        refresh = RefreshToken.for_user(user)
        # Embed claims directly in the token so the frontend
        # does not need a separate /me call after login.
        refresh["email"] = user.email
        refresh["full_name"] = user.full_name
        refresh["role"] = user.role
        refresh["is_verified"] = user.is_verified

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def set_refresh_cookie(response, refresh_token: str) -> None:
        from django.conf import settings

        max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
        response.set_cookie(
            settings.AUTH_REFRESH_COOKIE_NAME,
            refresh_token,
            max_age=max_age,
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            domain=settings.AUTH_COOKIE_DOMAIN,
            path="/api/v1/auth/",
        )

    @staticmethod
    def clear_refresh_cookie(response) -> None:
        from django.conf import settings

        response.delete_cookie(
            settings.AUTH_REFRESH_COOKIE_NAME,
            domain=settings.AUTH_COOKIE_DOMAIN,
            path="/api/v1/auth/",
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

    @staticmethod
    def revoke_refresh_token(refresh_token_str: str) -> None:
        """
        Blacklist a refresh token on logout.
        We use DRF Simple JWT's built-in token blacklist app.
        Additionally store the JTI in Redis for fast lookup during the token lifetime.
        """
        try:
            token = RefreshToken(refresh_token_str)
            jti = token.get("jti", "")
            # Blacklist via the token_blacklist app (persisted in DB)
            token.blacklist()
            # Also set in Redis for fast path checks (avoids DB hit on every request)
            if jti:
                cache.set(
                    f"{TOKEN_DENYLIST_PREFIX}{jti}",
                    True,
                    timeout=TOKEN_DENYLIST_TTL,
                )
            logger.info("Refresh token revoked: jti=%s", jti)
        except TokenError as exc:
            logger.warning("Attempted to revoke invalid token: %s", exc)
            # Do not raise - a token that is already invalid is effectively revoked

    @staticmethod
    def authenticate_google(id_token: str) -> tuple[User, bool]:
        """
        Validate a Google ID token and return (user, created).
        Creates a new user account if the Google account has not been seen before.

        Flow:
        1. Frontend authenticates with Google and receives an ID token.
        2. Frontend sends the ID token to POST /api/v1/auth/google/.
        3. This method validates the token with Google's server.
        4. We look up or create the local user and OAuthAccount.
        5. We return tokens for the local user.

        We validate server-side against Google's tokeninfo endpoint rather than
        using a JWT library because it avoids managing Google's public key rotation.
        For production at scale, use the google-auth library with key caching.
        """
        response = requests.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"id_token": id_token},
            timeout=10,
        )

        if response.status_code != 200:
            raise ServiceError("Invalid Google token. Please sign in again.")

        payload = response.json()

        # Verify the token was issued for our application
        if payload.get("aud") != settings.GOOGLE_OAUTH_CLIENT_ID:
            raise ServiceError("This token was not issued for T-Career.")

        google_uid = payload.get("sub")
        email = payload.get("email", "").lower().strip()
        full_name = payload.get("name", "")
        avatar_url = payload.get("picture", "")

        if not email or not google_uid:
            raise ServiceError("Google account did not provide required information.")

        # Check if this Google account is already linked to a T-Career account
        try:
            oauth_account = OAuthAccount.objects.select_related("user").get(
                provider="google-oauth2",
                provider_uid=google_uid,
            )
            user = oauth_account.user
            created = False
        except OAuthAccount.DoesNotExist:
            # Check if a T-Career account exists with this email
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "avatar_url": avatar_url,
                    "is_verified": True,  # Google has verified the email
                    "role": UserRole.STUDENT,
                },
            )

            OAuthAccount.objects.create(
                user=user,
                provider="google-oauth2",
                provider_uid=google_uid,
                extra_data={"email": email, "name": full_name, "picture": avatar_url},
            )

            if created:
                logger.info("New user via Google OAuth: %s", email)
            else:
                logger.info("Existing user linked Google account: %s", email)

        if not user.is_active:
            raise ServiceError("This account has been deactivated. Please contact support.")

        return user, created

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> None:
        """Verify the current password then set the new one."""
        if not user.check_password(current_password):
            raise ServiceError("Current password is incorrect.")
        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info("Password changed for user: %s", user.email)
