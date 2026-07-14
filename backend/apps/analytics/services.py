import logging

logger = logging.getLogger(__name__)


SYSTEM_EVENT_NAMES = {
    "ai_knowledge_document_indexed",
    "ai_knowledge_document_index_failed",
    "ai_reindex_started",
    "ai_reindex_completed",
}


class AnalyticsService:
    @staticmethod
    def classify(name: str, metadata: dict | None = None) -> dict:
        metadata = metadata or {}
        if name in SYSTEM_EVENT_NAMES or metadata.get("is_system_event"):
            return {
                "category": metadata.get("category", "operations"),
                "source": metadata.get("source", "system"),
                "actor_type": metadata.get("actor_type", "system"),
                "is_system_event": True,
                "counts_toward_engagement": False,
            }
        return {
            "category": metadata.get("category", "engagement"),
            "source": metadata.get("source", "application"),
            "actor_type": metadata.get("actor_type", "user"),
            "is_system_event": False,
            "counts_toward_engagement": bool(metadata.get("counts_toward_engagement", True)),
        }

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
            classification = AnalyticsService.classify(name, metadata)
            return AnalyticsEvent.objects.create(
                name=name,
                user=user if getattr(user, "is_authenticated", False) else None,
                organization_id=getattr(organization, "id", None),
                target_type=target.__class__.__name__ if target is not None else "",
                target_id=str(getattr(target, "id", "")) if target is not None else "",
                category=classification["category"],
                source=classification["source"],
                actor_type=classification["actor_type"],
                is_system_event=classification["is_system_event"],
                counts_toward_engagement=classification["counts_toward_engagement"],
                metadata=metadata or {},
            )
        except Exception as exc:
            logger.warning("Analytics event dropped: %s", exc)
            return None

    @staticmethod
    def recruiting_event(
        name: str, *, user=None, organization=None, target=None, metadata: dict | None = None
    ):
        return AnalyticsService.track(
            name=name,
            user=user,
            organization=organization,
            target=target,
            metadata=metadata,
        )

    @staticmethod
    def job_created(*, user=None, organization=None, job=None):
        return AnalyticsService.recruiting_event(
            "job_created", user=user, organization=organization, target=job
        )

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
