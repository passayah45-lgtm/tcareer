import pytest

from apps.analytics.services import AnalyticsService


@pytest.mark.django_db
def test_knowledge_indexing_event_is_system_event():
    event = AnalyticsService.track(
        name="ai_knowledge_document_indexed",
        metadata={"source_type": "lesson", "collection_type": "lessons"},
    )

    assert event.category == "operations"
    assert event.source == "system"
    assert event.actor_type == "system"
    assert event.is_system_event is True
    assert event.counts_toward_engagement is False


@pytest.mark.django_db
def test_learning_event_counts_toward_engagement_by_default():
    event = AnalyticsService.track(name="lesson_completed")

    assert event.category == "engagement"
    assert event.source == "application"
    assert event.actor_type == "user"
    assert event.is_system_event is False
    assert event.counts_toward_engagement is True
