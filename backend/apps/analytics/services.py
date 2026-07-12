import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    @staticmethod
    def track(
        *,
        name: str,
        user=None,
        organization=None,
        target=None,
        metadata: dict | None = None,
    ):
        from apps.analytics.models import AnalyticsEvent

        try:
            return AnalyticsEvent.objects.create(
                name=name,
                user=user if getattr(user, "is_authenticated", False) else None,
                organization_id=getattr(organization, "id", None),
                target_type=target.__class__.__name__ if target is not None else "",
                target_id=str(getattr(target, "id", "")) if target is not None else "",
                metadata=metadata or {},
            )
        except Exception as exc:
            logger.warning("Analytics event dropped: %s", exc)
            return None

    @staticmethod
    def recruiting_event(name: str, *, user=None, organization=None, target=None, metadata: dict | None = None):
        return AnalyticsService.track(
            name=name,
            user=user,
            organization=organization,
            target=target,
            metadata=metadata,
        )

    @staticmethod
    def job_created(*, user=None, organization=None, job=None):
        return AnalyticsService.recruiting_event("job_created", user=user, organization=organization, target=job)

    @staticmethod
    def application_created(*, user=None, organization=None, application=None, metadata=None):
        return AnalyticsService.recruiting_event(
            "application_created",
            user=user,
            organization=organization,
            target=application,
            metadata=metadata,
        )

    @staticmethod
    def application_stage_changed(*, user=None, organization=None, application=None, metadata=None):
        return AnalyticsService.recruiting_event(
            "application_stage_changed",
            user=user,
            organization=organization,
            target=application,
            metadata=metadata,
        )

    @staticmethod
    def candidate_saved(*, user=None, organization=None, candidate=None, metadata=None):
        return AnalyticsService.recruiting_event(
            "candidate_saved",
            user=user,
            organization=organization,
            target=candidate,
            metadata=metadata,
        )

    @staticmethod
    def candidate_unlocked(*, user=None, organization=None, candidate=None, metadata=None):
        return AnalyticsService.recruiting_event(
            "candidate_unlocked",
            user=user,
            organization=organization,
            target=candidate,
            metadata=metadata,
        )

    @staticmethod
    def interview_scheduled(*, user=None, organization=None, interview=None, metadata=None):
        return AnalyticsService.recruiting_event(
            "interview_scheduled",
            user=user,
            organization=organization,
            target=interview,
            metadata=metadata,
        )

    @staticmethod
    def interview_completed(*, user=None, organization=None, interview=None, metadata=None):
        return AnalyticsService.recruiting_event(
            "interview_completed",
            user=user,
            organization=organization,
            target=interview,
            metadata=metadata,
        )

    @staticmethod
    def offer_event(name: str, *, user=None, organization=None, application=None, metadata=None):
        return AnalyticsService.recruiting_event(
            name,
            user=user,
            organization=organization,
            target=application,
            metadata=metadata,
        )
