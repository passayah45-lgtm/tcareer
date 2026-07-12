import logging
import secrets

from django.conf import settings
from django.middleware.csrf import constant_time_compare
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.exceptions import AuthenticationFailed

from common.audit import AuditService
from common.privacy import PrivacyService
from common.throttles import AuthRateThrottle, RefreshRateThrottle

from .models import User, UserRole
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    GoogleAuthSerializer,
    ChangePasswordSerializer,
    UpdateProfileSerializer,
    CustomTokenObtainPairSerializer,
)
from .services import AuthService

logger = logging.getLogger(__name__)


def _set_auth_cookies(response, refresh_token):
    AuthService.set_refresh_cookie(response, refresh_token)
    response.set_cookie(
        settings.AUTH_CSRF_COOKIE_NAME,
        secrets.token_urlsafe(32),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=False,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path="/api/v1/auth/",
    )


def _clear_auth_cookies(response):
    AuthService.clear_refresh_cookie(response)
    response.delete_cookie(
        settings.AUTH_CSRF_COOKIE_NAME,
        domain=settings.AUTH_COOKIE_DOMAIN,
        path="/api/v1/auth/",
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def _require_cookie_csrf(request):
    if settings.AUTH_REFRESH_COOKIE_NAME not in request.COOKIES:
        return
    cookie_token = request.COOKIES.get(settings.AUTH_CSRF_COOKIE_NAME, "")
    header_token = request.headers.get("X-CSRFToken", "")
    if not cookie_token or not header_token or not constant_time_compare(cookie_token, header_token):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("CSRF token missing or invalid.")


def _without_refresh_payload(data):
    data = dict(data)
    data.pop("refresh", None)
    return data


def _audit_admin_login(request, response):
    if response.status_code >= 400:
        return
    user_payload = response.data.get("user") if isinstance(response.data, dict) else None
    email = user_payload.get("email") if isinstance(user_payload, dict) else ""
    if not email:
        return
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return
    admin_roles = {
        UserRole.ADMIN,
        UserRole.PLATFORM_ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.FINANCE_ADMIN,
        UserRole.CONTENT_MODERATOR,
    }
    if user.is_staff or user.is_superuser or user.role in admin_roles:
        AuditService.record(
            actor=user,
            action="admin_login",
            target=user,
            request=request,
            metadata={"role": user.role},
        )


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/

    Accepts email and password. Returns access token, refresh token, and user data.
    The refresh token should be stored in an httpOnly cookie by the frontend.
    Rate limited to 10 requests per minute per IP.
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        summary="Login with email and password",
        responses={
            200: OpenApiResponse(description="Login successful"),
            400: OpenApiResponse(description="Invalid credentials"),
            429: OpenApiResponse(description="Too many login attempts"),
        },
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except (AuthenticationFailed, InvalidToken, TokenError) as exc:
            logger.warning(
                "auth_login_failed",
                extra={"email": request.data.get("email", ""), "ip": request.META.get("REMOTE_ADDR", ""), "error": exc.__class__.__name__},
            )
            AuditService.record(
                actor=None,
                action="failed_login",
                target_type="User",
                target_id=request.data.get("email", ""),
                request=request,
                metadata={"error": exc.__class__.__name__},
            )
            raise
        _audit_admin_login(request, response)
        refresh = response.data.get("refresh")
        if refresh:
            _set_auth_cookies(response, refresh)
            response.data = _without_refresh_payload(response.data)
        return response


class TokenRefreshWithUserView(TokenRefreshView):
    """
    POST /api/v1/auth/token/refresh/

    Accepts a refresh token. Returns a new access token.
    The old refresh token is blacklisted (rotation is enabled).
    """

    throttle_classes = [RefreshRateThrottle]

    @extend_schema(summary="Refresh access token")
    def post(self, request, *args, **kwargs):
        _require_cookie_csrf(request)
        if "refresh" not in request.data and settings.AUTH_REFRESH_COOKIE_NAME in request.COOKIES:
            request.data["refresh"] = request.COOKIES[settings.AUTH_REFRESH_COOKIE_NAME]
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh")
        if refresh:
            _set_auth_cookies(response, refresh)
            response.data = _without_refresh_payload(response.data)
        return response


@extend_schema(
    summary="Register a new account",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description="Account created"),
        400: OpenApiResponse(description="Validation error"),
        409: OpenApiResponse(description="Email already registered"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register(request):
    """
    POST /api/v1/auth/register/

    Creates a new user account and returns tokens immediately.
    The user is logged in right after registration - no separate login step needed.
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()
    tokens = AuthService.issue_tokens(user)

    # Auto-generate username for public profile URL
    try:
        if not user.username:
            user.username = user.generate_username()
            user.save(update_fields=["username"])
    except Exception:
        pass

    # Send verification email
    try:
        from apps.users.email_verification import EmailVerificationToken
        from tasks.email import send_verification_email
        verification_token = EmailVerificationToken.create_for_user(user)
        send_verification_email.delay(str(user.id), verification_token)
    except Exception:
        pass  # Do not block registration if email fails

    # Send welcome notification
    try:
        from apps.notifications.models import NotificationService
        NotificationService.welcome(user)
    except Exception:
        pass

    response = Response(
        {
            "user": UserSerializer(user).data,
            "access": tokens["access"],
        },
        status=status.HTTP_201_CREATED,
    )
    _set_auth_cookies(response, tokens["refresh"])
    return response


@extend_schema(
    summary="Logout - revoke refresh token",
    responses={
        204: OpenApiResponse(description="Logged out"),
        400: OpenApiResponse(description="Missing refresh token"),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/v1/auth/logout/

    Blacklists the refresh token, preventing it from being used to obtain
    new access tokens. The access token will expire on its own (15 minutes).

    Expects: { "refresh": "<refresh_token>" }
    """
    _require_cookie_csrf(request)
    refresh_token = request.data.get("refresh") or request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if not refresh_token:
        return Response(
            {"detail": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    AuthService.revoke_refresh_token(refresh_token)
    response = Response(status=status.HTTP_204_NO_CONTENT)
    _clear_auth_cookies(response)
    return response


@extend_schema(
    summary="Authenticate with Google",
    request=GoogleAuthSerializer,
    responses={
        200: OpenApiResponse(description="Authenticated"),
        400: OpenApiResponse(description="Invalid Google token"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def google_auth(request):
    """
    POST /api/v1/auth/google/

    Validates a Google ID token obtained by the frontend via Google Sign-In.
    Creates a new account if the user has not signed in before.

    Expects: { "id_token": "<google_id_token>" }
    """
    serializer = GoogleAuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user, created = AuthService.authenticate_google(serializer.validated_data["id_token"])
    tokens = AuthService.issue_tokens(user)

    response = Response(
        {
            "user": UserSerializer(user).data,
            "access": tokens["access"],
            "created": created,
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )
    _set_auth_cookies(response, tokens["refresh"])
    return response


@extend_schema(summary="Get current user profile")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /api/v1/auth/me/

    Returns the authenticated user's profile data.
    """
    return Response(UserSerializer(request.user).data)


@extend_schema(
    summary="Update profile",
    request=UpdateProfileSerializer,
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    PATCH /api/v1/auth/me/

    Updates full_name and avatar_url. Partial update only.
    """
    serializer = UpdateProfileSerializer(
        request.user,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(request.user).data)


@extend_schema(
    summary="Change password",
    request=ChangePasswordSerializer,
    responses={
        204: OpenApiResponse(description="Password changed"),
        400: OpenApiResponse(description="Validation error or wrong current password"),
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    POST /api/v1/auth/change-password/

    Requires the current password for verification before setting a new one.
    """
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    AuthService.change_password(
        user=request.user,
        current_password=serializer.validated_data["current_password"],
        new_password=serializer.validated_data["new_password"],
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Password Reset ────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def forgot_password(request):
    """
    POST /api/v1/auth/forgot-password/

    Accepts an email address and sends a reset link if the account exists.
    Always returns 200 to prevent email enumeration attacks.

    Request: { "email": "user@example.com" }
    """
    email = request.data.get("email", "").lower().strip()
    if email:
        from apps.users.models import User
        from apps.users.password_reset import PasswordResetToken
        try:
            user = User.objects.get(email=email, is_active=True)
            token = PasswordResetToken.create_for_user(user)
            from tasks.email import send_password_reset_email
            send_password_reset_email.delay(str(user.id), token)
        except User.DoesNotExist:
            pass  # Return 200 regardless to prevent email enumeration
    return Response(
        {"detail": "If an account exists with this email, a reset link has been sent."}
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    """
    POST /api/v1/auth/reset-password/

    Validates the token and sets the new password.

    Request: { "token": "...", "password": "NewPass123!", "password_confirm": "NewPass123!" }
    """
    from apps.users.password_reset import PasswordResetToken
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError

    token_str = request.data.get("token", "")
    password = request.data.get("password", "")
    password_confirm = request.data.get("password_confirm", "")

    if not token_str:
        return Response({"detail": "Token is required."}, status=400)

    if password != password_confirm:
        return Response({"detail": "Passwords do not match."}, status=400)

    try:
        validate_password(password)
    except DjangoValidationError as exc:
        return Response({"detail": list(exc.messages)}, status=400)

    reset_token = PasswordResetToken.validate(token_str)
    if not reset_token:
        return Response(
            {"detail": "This reset link is invalid or has expired."},
            status=400,
        )

    user = reset_token.user
    user.set_password(password)
    user.save(update_fields=["password"])
    reset_token.consume()

    return Response({"detail": "Password reset successfully. You can now sign in."})


# ── Public Profile ────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def public_profile(request, username):
    """
    GET /api/v1/auth/profile/{username}/

    Public profile page. No authentication required.
    Returns the student's public information, certificates, and track progress.
    """
    from apps.users.models import User
    from apps.certificates.models import Certificate
    from apps.tracks.models import UserTrackEnrollment
    from apps.courses.models import Enrollment, EnrollmentStatus

    try:
        user = User.objects.get(username=username, is_active=True, is_public_profile=True)
    except User.DoesNotExist:
        return Response({"detail": "Profile not found."}, status=404)

    certificates = Certificate.objects.filter(
        user=user, is_revoked=False
    ).select_related("course").order_by("-issued_at")

    track_enrollments = UserTrackEnrollment.objects.filter(
        user=user
    ).select_related("track").order_by("-last_activity_at")

    completed_courses = Enrollment.objects.filter(
        user=user, status=EnrollmentStatus.COMPLETED
    ).select_related("course").order_by("-created_at")

    return Response({
        "full_name": user.full_name,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "profile_headline": user.profile_headline,
        "profile_bio": user.profile_bio,
        "profile_location": user.profile_location,
        "linkedin_url": user.linkedin_url,
        "github_url": user.github_url,
        "role": user.role,
        "member_since": user.created_at.strftime("%B %Y"),
        "certificates": [
            {
                "cert_number": c.cert_number,
                "course_title": c.course.title,
                "issued_at": c.issued_at,
                "verify_url": c.verify_url,
                "pdf_url": c.pdf_url,
            }
            for c in certificates
        ],
        "tracks": [
            {
                "track_title": e.track.title,
                "track_slug": e.track.slug,
                "track_color": e.track.color,
                "progress_percentage": e.progress_percentage,
                "current_stage_display": e.get_current_stage_display(),
                "is_completed": e.is_completed,
            }
            for e in track_enrollments
        ],
        "completed_courses": [
            {
                "title": e.course.title,
                "slug": e.course.slug,
                "level": e.course.level,
            }
            for e in completed_courses[:10]
        ],
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    PATCH /api/v1/auth/me/update/

    Update the authenticated user's profile fields.
    """
    from apps.users.models import User

    allowed_fields = [
        "full_name", "profile_headline", "profile_bio",
        "profile_location", "linkedin_url", "github_url", "is_public_profile",
    ]

    user = request.user
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    if "is_public_profile" in request.data:
        privacy = PrivacyService.get_settings(user)
        privacy.public_profile = bool(request.data["is_public_profile"])
        privacy.save(update_fields=["public_profile", "updated_at"])

    # Auto-generate username if not set
    if not user.username:
        user.username = user.generate_username()

    user.save(update_fields=allowed_fields + ["username", "updated_at"])

    return Response({
        "detail": "Profile updated.",
        "username": user.username,
        "profile_url": f"/u/{user.username}",
    })


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def privacy_settings(request):
    privacy = PrivacyService.get_settings(request.user)
    fields = [
        "public_profile",
        "recruiter_resume_visibility",
        "recruiter_portfolio_visibility",
        "open_to_work",
        "allow_recruiter_contact",
        "allow_analytics",
        "allow_ai_analysis",
    ]
    if request.method == "PATCH":
        before = {field: getattr(privacy, field) for field in fields}
        for field in fields:
            if field in request.data:
                setattr(privacy, field, bool(request.data[field]))
        privacy.save()
        after = {field: getattr(privacy, field) for field in fields}
        changed = {field: {"from": before[field], "to": after[field]} for field in fields if before[field] != after[field]}
        if changed:
            AuditService.record(
                actor=request.user,
                action="privacy_settings_changed",
                target=privacy,
                request=request,
                metadata={"changed": changed},
            )
    return Response({field: getattr(privacy, field) for field in fields})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    """
    POST /api/v1/auth/verify-email/

    Validates the email verification token and marks the user as verified.
    Request: { "token": "..." }
    """
    from apps.users.email_verification import EmailVerificationToken

    token_str = request.data.get("token", "")
    if not token_str:
        return Response({"detail": "Token is required."}, status=400)

    verification = EmailVerificationToken.validate(token_str)
    if not verification:
        return Response(
            {"detail": "This verification link is invalid or has expired."},
            status=400,
        )

    user = verification.user
    user.is_email_verified = True
    user.is_verified = True
    user.save(update_fields=["is_email_verified", "is_verified"])
    verification.consume()

    return Response({"detail": "Email verified successfully. You now have full access."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resend_verification(request):
    """
    POST /api/v1/auth/resend-verification/

    Sends a new verification email to the authenticated user.
    """
    from apps.users.email_verification import EmailVerificationToken
    from tasks.email import send_verification_email

    if request.user.is_email_verified:
        return Response({"detail": "Your email is already verified."}, status=400)

    token = EmailVerificationToken.create_for_user(request.user)
    send_verification_email.delay(str(request.user.id), token)

    return Response({"detail": "Verification email sent. Check your inbox."})
