from django.core.management.base import BaseCommand

from apps.ai_platform.models import KnowledgeDocument
from apps.ai_platform.services import KnowledgeIndexingService


class Command(BaseCommand):
    help = "Reindex AI knowledge documents from supported source models."

    def add_arguments(self, parser):
        parser.add_argument("--collection", default="", help="Knowledge collection type to reindex.")
        parser.add_argument("--source-type", default="", help="Source type: course, lesson, job, resume, portfolio, track, skill, stale, failed.")
        parser.add_argument("--organization-id", default="", help="Restrict organization-scoped sources.")
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        source_type = options["source_type"]
        organization_id = options["organization_id"]
        limit = options["limit"]
        dry_run = options["dry_run"]
        indexed = 0
        candidates = []

        if source_type in {"stale", "failed"}:
            documents = KnowledgeDocument.objects.filter(index_status="stale" if source_type == "stale" else "failed")
            if options["collection"]:
                documents = documents.filter(collection__collection_type=options["collection"])
            if organization_id:
                documents = documents.filter(organization_id=organization_id)
            candidates = list(documents.order_by("updated_at")[:limit])
            if dry_run:
                self.stdout.write(f"Would retry {len(candidates)} {source_type} document(s).")
                return
            for document in candidates:
                payload = {
                    "collection_type": document.collection.collection_type,
                    "source_type": document.source_type,
                    "source_id": document.source_id,
                    "title": document.title,
                    "text": document.text,
                    "visibility": document.visibility,
                    "metadata": document.metadata,
                }
                KnowledgeIndexingService.reindex_from_payload(payload=payload, organization=document.organization)
                indexed += 1
            self.stdout.write(self.style.SUCCESS(f"Retried {indexed} {source_type} knowledge document(s)."))
            return

        if source_type in {"", "course"}:
            from apps.courses.models import Course

            qs = Course.objects.all().order_by("updated_at")
            candidates.extend(list(qs[:limit]))
        if source_type in {"", "lesson"}:
            from apps.courses.models import Lesson

            qs = Lesson.objects.select_related("course").order_by("updated_at")
            candidates.extend(list(qs[:limit]))
        if source_type in {"", "job"}:
            from apps.jobs.models import JobListing

            qs = JobListing.objects.select_related("organization").order_by("updated_at")
            if organization_id:
                qs = qs.filter(organization_id=organization_id)
            candidates.extend(list(qs[:limit]))
        if source_type in {"", "resume"}:
            from apps.careers.models import CareerResume

            candidates.extend(list(CareerResume.objects.select_related("user").order_by("updated_at")[:limit]))
        if source_type in {"", "portfolio"}:
            from apps.careers.models import Portfolio

            candidates.extend(list(Portfolio.objects.select_related("user").prefetch_related("skills", "projects").order_by("updated_at")[:limit]))
        if source_type in {"", "track", "career_track"}:
            from apps.tracks.models import CareerTrack

            candidates.extend(list(CareerTrack.objects.prefetch_related("track_courses__course").order_by("updated_at")[:limit]))
        if source_type == "skill":
            from apps.careers.models import PortfolioSkill

            candidates.extend(list(PortfolioSkill.objects.select_related("portfolio", "portfolio__user").order_by("updated_at")[:limit]))

        candidates = candidates[:limit]
        if dry_run:
            self.stdout.write(f"Would reindex {len(candidates)} source object(s).")
            return
        for source in candidates:
            KnowledgeIndexingService.index_source(source=source)
            indexed += 1
        self.stdout.write(self.style.SUCCESS(f"Reindexed {indexed} source object(s)."))
