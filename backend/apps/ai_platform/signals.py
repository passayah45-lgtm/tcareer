import logging

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.ai_platform.models import KnowledgeCollectionType, KnowledgeVisibility
from apps.ai_platform.services import KnowledgeIndexingService

logger = logging.getLogger("tcareer.ai")


def _auto_index_enabled():
    return bool(getattr(settings, "AI_KNOWLEDGE_AUTO_INDEX", True))


def _index_safely(instance):
    if not _auto_index_enabled():
        return
    try:
        KnowledgeIndexingService.index_source(source=instance)
    except Exception as exc:
        logger.warning("ai_knowledge_auto_index_failed", extra={"model": instance.__class__.__name__, "id": str(getattr(instance, "id", "")), "error": str(exc)})


@receiver(post_save, sender="courses.Course")
@receiver(post_save, sender="courses.Lesson")
@receiver(post_save, sender="jobs.JobListing")
@receiver(post_save, sender="careers.CareerResume")
@receiver(post_save, sender="careers.Portfolio")
@receiver(post_save, sender="careers.PortfolioSkill")
@receiver(post_save, sender="careers.PortfolioProject")
@receiver(post_save, sender="tracks.CareerTrack")
def auto_index_supported_source(sender, instance, **kwargs):
    _index_safely(instance)


@receiver(post_delete, sender="courses.Course")
@receiver(post_delete, sender="courses.Lesson")
@receiver(post_delete, sender="jobs.JobListing")
@receiver(post_delete, sender="careers.CareerResume")
@receiver(post_delete, sender="careers.Portfolio")
@receiver(post_delete, sender="tracks.CareerTrack")
def mark_deleted_source_stale(sender, instance, **kwargs):
    source_map = {
        "Course": "course",
        "Lesson": "lesson",
        "JobListing": "job",
        "CareerResume": "resume",
        "Portfolio": "portfolio",
        "CareerTrack": "career_track",
    }
    source_type = source_map.get(instance.__class__.__name__)
    if source_type:
        KnowledgeIndexingService.mark_stale(source_type=source_type, source_id=instance.id, reason="source_deleted")


@receiver(post_delete, sender="careers.PortfolioSkill")
@receiver(post_delete, sender="careers.PortfolioProject")
def mark_portfolio_child_deleted_stale(sender, instance, **kwargs):
    KnowledgeIndexingService.mark_stale(source_type="portfolio", source_id=instance.portfolio_id, reason="portfolio_child_deleted")


@receiver(post_save, sender="assessments.QuizQuestion")
def auto_index_quiz_question(sender, instance, **kwargs):
    if not _auto_index_enabled():
        return
    try:
        course = instance.course
        text = "\n".join(filter(None, [instance.question_text, instance.explanation, " ".join(instance.options or [])]))
        KnowledgeIndexingService.index_document(
            collection_type=KnowledgeCollectionType.QUIZZES,
            source_type="quiz_question",
            source_id=instance.id,
            title=f"Quiz question for {course.title}",
            text=text,
            organization=getattr(course, "organization", None),
            owner=getattr(course, "instructor", None),
            visibility=KnowledgeVisibility.PUBLIC if getattr(course, "is_published", False) else KnowledgeVisibility.PRIVATE,
            source_updated_at=getattr(instance, "updated_at", None),
            metadata={"course_id": str(course.id)},
        )
    except Exception as exc:
        logger.warning("ai_knowledge_quiz_index_failed", extra={"id": str(getattr(instance, "id", "")), "error": str(exc)})


@receiver(post_save, sender="certificates.Certificate")
def auto_index_certificate(sender, instance, **kwargs):
    if not _auto_index_enabled():
        return
    try:
        KnowledgeIndexingService.index_document(
            collection_type=KnowledgeCollectionType.CERTIFICATES,
            source_type="certificate",
            source_id=instance.id,
            title=getattr(instance.course, "title", "") or "Certificate",
            text="\n".join(filter(None, [getattr(instance.course, "title", ""), getattr(instance.user, "full_name", ""), getattr(instance, "cert_number", "")])),
            owner=getattr(instance, "user", None),
            visibility=KnowledgeVisibility.PUBLIC,
            source_updated_at=getattr(instance, "updated_at", None),
            metadata={"certificate_number": getattr(instance, "cert_number", ""), "verify_url": getattr(instance, "verify_url", "")},
        )
    except Exception as exc:
        logger.warning("ai_knowledge_certificate_index_failed", extra={"id": str(getattr(instance, "id", "")), "error": str(exc)})
