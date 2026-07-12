import logging

from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger("tcareer.security.throttle")


class LoggingScopedRateThrottle(SimpleRateThrottle):
    scope = "sensitive"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = f"user:{request.user.pk}"
        else:
            ident = f"ip:{self.get_ident(request)}"
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def throttle_failure(self):
        request = getattr(self, "request", None)
        view = getattr(self, "view", None)
        user = getattr(request, "user", None)
        logger.warning(
            "rate_limit_exceeded",
            extra={
                "scope": self.scope,
                "path": getattr(request, "path", ""),
                "method": getattr(request, "method", ""),
                "view": view.__class__.__name__ if view is not None else "",
                "user_id": str(getattr(user, "id", "")) if getattr(user, "is_authenticated", False) else "",
                "ip_address": self.get_ident(request) if request is not None else "",
            },
        )
        try:
            from common.audit import AuditService

            AuditService.record(
                actor=user if getattr(user, "is_authenticated", False) else None,
                action="rate_limit_exceeded",
                target_type="Throttle",
                target_id=self.scope,
                request=request,
                metadata={
                    "scope": self.scope,
                    "path": getattr(request, "path", ""),
                    "method": getattr(request, "method", ""),
                    "view": view.__class__.__name__ if view is not None else "",
                },
            )
        except Exception:
            logger.exception("rate_limit_audit_failed", extra={"scope": self.scope})
        return super().throttle_failure()


class AuthRateThrottle(LoggingScopedRateThrottle):
    scope = "auth"


class RefreshRateThrottle(LoggingScopedRateThrottle):
    scope = "refresh"


class NotificationPreferenceRateThrottle(LoggingScopedRateThrottle):
    scope = "notification_preferences"


class UnsubscribeRateThrottle(LoggingScopedRateThrottle):
    scope = "unsubscribe"


class CandidateUnlockRateThrottle(LoggingScopedRateThrottle):
    scope = "candidate_unlock"


class RecruiterSearchRateThrottle(LoggingScopedRateThrottle):
    scope = "recruiter_search"


class ApplicationSubmitRateThrottle(LoggingScopedRateThrottle):
    scope = "application_submit"


class ResumeDownloadRateThrottle(LoggingScopedRateThrottle):
    scope = "resume_download"


class InvitationAcceptRateThrottle(LoggingScopedRateThrottle):
    scope = "invitation_accept"


class AIRateThrottle(LoggingScopedRateThrottle):
    scope = "ai"
