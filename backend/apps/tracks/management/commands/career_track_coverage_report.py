from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.courses.models import CourseStatus
from apps.tracks.models import CareerTrack, TrackCourse


class Command(BaseCommand):
    help = "Report career track course coverage and publication status."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
        parser.add_argument("--track", help="Limit report to one track slug.")
        parser.add_argument(
            "--fail-on-empty",
            action="store_true",
            help="Exit with an error if any selected track has no attached courses.",
        )

    def handle(self, *args, **options):
        tracks = CareerTrack.objects.filter(is_active=True).order_by("position", "title")
        if options["track"]:
            tracks = tracks.filter(slug=options["track"])
            if not tracks.exists():
                raise CommandError(f"Career track not found: {options['track']}")

        report = [self._track_report(track) for track in tracks]
        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2))
        else:
            self._print_report(report)

        if options["fail_on_empty"]:
            empty = [item["track"] for item in report if item["attached_course_count"] == 0]
            if empty:
                raise CommandError(f"Empty career tracks: {', '.join(empty)}")

    def _track_report(self, track: CareerTrack) -> dict:
        attachments = (
            TrackCourse.objects.filter(track=track)
            .select_related("course", "course__instructor")
            .order_by("position", "course__title")
        )
        duplicate_positions = []
        seen_positions = set()
        missing_required_fields = []
        missing_instructor = []
        for attachment in attachments:
            if attachment.position in seen_positions:
                duplicate_positions.append(attachment.position)
            seen_positions.add(attachment.position)
            course = attachment.course
            missing = [
                field
                for field in ("title", "slug", "short_description", "description")
                if not getattr(course, field)
            ]
            if missing:
                missing_required_fields.append({"course": course.slug, "fields": missing})
            if not course.instructor_id:
                missing_instructor.append(course.slug)

        return {
            "track": track.slug,
            "title": track.title,
            "attached_course_count": attachments.count(),
            "published_course_count": attachments.filter(
                course__status=CourseStatus.PUBLISHED, course__deleted_at__isnull=True
            ).count(),
            "draft_course_count": attachments.filter(course__status=CourseStatus.DRAFT).count(),
            "missing_required_fields": missing_required_fields,
            "missing_instructor": missing_instructor,
            "duplicate_attachment_positions": duplicate_positions,
            "is_empty": not attachments.exists(),
        }

    def _print_report(self, report: list[dict]) -> None:
        self.stdout.write("Career track coverage report")
        for item in report:
            self.stdout.write(
                f"- {item['track']} ({item['title']}): "
                f"{item['attached_course_count']} attached, "
                f"{item['published_course_count']} published, "
                f"{item['draft_course_count']} draft"
            )
            if item["missing_required_fields"]:
                self.stdout.write(f"  missing fields: {item['missing_required_fields']}")
            if item["missing_instructor"]:
                self.stdout.write(f"  missing instructor: {item['missing_instructor']}")
            if item["duplicate_attachment_positions"]:
                self.stdout.write(
                    f"  duplicate positions: {item['duplicate_attachment_positions']}"
                )
