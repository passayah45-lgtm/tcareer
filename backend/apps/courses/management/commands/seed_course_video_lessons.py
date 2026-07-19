from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.audit.models import AuditLog
from apps.courses.models import (
    ContentReviewStatus,
    Course,
    CourseStatus,
    Lesson,
    LessonType,
    TranscodingStatus,
    VideoLesson,
)
from apps.courses.production_catalog import COURSES_BY_SLUG

SOURCE = "course_video_lesson_seed"
DEFAULT_HLS_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
DEFAULT_THUMBNAIL_URL = "https://test-streams.mux.dev/x36xhzz/thumbs/00000001.jpg"


class Command(BaseCommand):
    help = "Seed one playable video lesson for production catalog courses."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print planned changes only.")
        parser.add_argument(
            "--confirm-production",
            action="store_true",
            help="Required for writes when DEBUG=False.",
        )
        parser.add_argument("--course", help="Seed one supported course slug.")
        parser.add_argument(
            "--all-courses",
            action="store_true",
            help="Seed all supported production catalog courses.",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update existing seeded video lesson metadata.",
        )
        parser.add_argument(
            "--hls-url",
            default=DEFAULT_HLS_URL,
            help="Playable HLS URL to use for seeded video lessons.",
        )
        parser.add_argument(
            "--thumbnail-url",
            default=DEFAULT_THUMBNAIL_URL,
            help="Thumbnail URL to use for seeded video lessons.",
        )

    def handle(self, *args, **options):
        self._validate_options(options)
        course_slugs = self._selected_course_slugs(options)
        courses = {
            course.slug: course
            for course in Course.objects.filter(
                slug__in=course_slugs,
                status=CourseStatus.PUBLISHED,
                deleted_at=None,
            )
        }
        missing = [slug for slug in course_slugs if slug not in courses]
        plan = self._build_plan(course_slugs, courses, options)
        self._print_plan(plan, missing, options)

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run only. No database changes were made."))
            return

        with transaction.atomic():
            result = self._apply_plan(plan, options)

        self.stdout.write(
            self.style.SUCCESS(
                "Course video lesson seed complete: "
                f"{result['lessons_created']} lessons created, "
                f"{result['lessons_updated']} lessons updated, "
                f"{result['videos_created']} video records created, "
                f"{result['videos_updated']} video records updated, "
                f"{len(missing)} courses skipped."
            )
        )

    def _validate_options(self, options):
        if bool(options["course"]) == bool(options["all_courses"]):
            raise CommandError("Choose exactly one of --course <slug> or --all-courses.")
        if options["course"] and options["course"] not in COURSES_BY_SLUG:
            supported = ", ".join(sorted(COURSES_BY_SLUG))
            raise CommandError(
                f"Unsupported course '{options['course']}'. Supported courses: {supported}"
            )
        if not settings.DEBUG and not options["dry_run"] and not options["confirm_production"]:
            raise CommandError(
                "Refusing to write in production without --confirm-production. "
                "Run --dry-run first, review output, then rerun with --confirm-production."
            )

    def _selected_course_slugs(self, options):
        if options["course"]:
            return [options["course"]]
        return sorted(COURSES_BY_SLUG)

    def _build_plan(self, course_slugs, courses, options):
        plan = []
        for slug in course_slugs:
            course = courses.get(slug)
            if course is None:
                continue
            title = f"{course.title}: Welcome video"
            lesson = Lesson.objects.filter(course=course, title=title, deleted_at=None).first()
            lesson_action = "create" if lesson is None else "keep"
            video_action = "create"
            if lesson is not None:
                video_exists = VideoLesson.objects.filter(lesson=lesson).exists()
                video_action = "keep" if video_exists else "create"
                if options["update_existing"]:
                    lesson_action = "update"
                    video_action = "update"
            plan.append(
                {
                    "course": course,
                    "title": title,
                    "lesson": lesson,
                    "lesson_action": lesson_action,
                    "video_action": video_action,
                }
            )
        return plan

    def _print_plan(self, plan, missing, options):
        mode = "DRY RUN" if options["dry_run"] else "WRITE"
        self.stdout.write(f"Course video lesson seed plan ({mode})")
        self.stdout.write(f"HLS URL: {options['hls_url']}")
        for item in plan:
            self.stdout.write(
                f"  - {item['course'].slug}: lesson={item['lesson_action']}, "
                f"video={item['video_action']}"
            )
        for slug in missing:
            self.stdout.write(self.style.WARNING(f"  - {slug}: skipped, published course not found"))

    def _apply_plan(self, plan, options):
        result = {
            "lessons_created": 0,
            "lessons_updated": 0,
            "videos_created": 0,
            "videos_updated": 0,
        }
        for item in plan:
            course = item["course"]
            lesson = item["lesson"]
            if lesson is None:
                lesson = Lesson.objects.create(
                    course=course,
                    title=item["title"],
                    lesson_type=LessonType.VIDEO,
                    content=(
                        "<p>This seeded video lesson is for validating the course player, "
                        "enrollment flow, progress tracking, and AI tutor entry points.</p>"
                    ),
                    position=1,
                    is_published=True,
                    is_free_preview=True,
                    review_status=ContentReviewStatus.PUBLISHED,
                    published_version=1,
                )
                result["lessons_created"] += 1
                self._audit("course_video_lesson_seeded", lesson)
            elif options["update_existing"]:
                lesson.lesson_type = LessonType.VIDEO
                lesson.content = (
                    "<p>This seeded video lesson is for validating the course player, "
                    "enrollment flow, progress tracking, and AI tutor entry points.</p>"
                )
                lesson.position = 1
                lesson.is_published = True
                lesson.is_free_preview = True
                lesson.review_status = ContentReviewStatus.PUBLISHED
                lesson.published_version = max(lesson.published_version, 1)
                lesson.save(
                    update_fields=[
                        "lesson_type",
                        "content",
                        "position",
                        "is_published",
                        "is_free_preview",
                        "review_status",
                        "published_version",
                        "updated_at",
                    ]
                )
                result["lessons_updated"] += 1
                self._audit("course_video_lesson_updated", lesson)

            video, created = VideoLesson.objects.get_or_create(lesson=lesson)
            if created or options["update_existing"]:
                video.hls_url = options["hls_url"]
                video.thumbnail_url = options["thumbnail_url"]
                video.duration_seconds = 42
                video.transcoding_status = TranscodingStatus.COMPLETE
                video.file_size_bytes = 0
                video.save(
                    update_fields=[
                        "hls_url",
                        "thumbnail_url",
                        "duration_seconds",
                        "transcoding_status",
                        "file_size_bytes",
                        "updated_at",
                    ]
                )
                result["videos_created" if created else "videos_updated"] += 1
                self._audit("course_video_asset_seeded", video)

            if not course.preview_video_url:
                course.preview_video_url = options["hls_url"]
                course.save(update_fields=["preview_video_url", "updated_at"])
        return result

    def _audit(self, action, target):
        AuditLog.objects.create(
            actor=None,
            action=action,
            target_type=target.__class__.__name__,
            target_id=str(target.id),
            metadata={"source": SOURCE},
        )
