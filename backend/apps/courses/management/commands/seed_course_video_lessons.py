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
COURSE_VIDEO_URLS = {
    "sql-for-data-analysis": "https://www.youtube-nocookie.com/embed/HXV3zeQKqGY",
    "python-fundamentals": "https://www.youtube-nocookie.com/embed/rfscVS0vtbw",
    "python-for-data-analysis": "https://www.youtube-nocookie.com/embed/vmEHCJofslg",
    "html-and-css-from-zero": "https://www.youtube-nocookie.com/embed/pQN-pnXPaVg",
    "javascript-essentials": "https://www.youtube-nocookie.com/embed/PkZNo7MFNFg",
    "git-and-github-for-developers": "https://www.youtube-nocookie.com/embed/RGOj5yH7evk",
    "react-from-zero-to-first-app": "https://www.youtube-nocookie.com/embed/bMknfKXIFA8",
    "nodejs-and-express-backend-development": "https://www.youtube-nocookie.com/embed/Oe421EPjeBE",
    "postgresql-for-developers": "https://www.youtube-nocookie.com/embed/qw--VYLpxG4",
    "typescript-for-javascript-developers": "https://www.youtube-nocookie.com/embed/30LWjhZzg50",
    "docker-and-containerization-from-scratch": "https://www.youtube-nocookie.com/embed/pg19Z8LL06w",
}


class Command(BaseCommand):
    help = "Seed playable preview lessons for production catalog courses."

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

    def _print_plan(self, plan, missing, options):
        mode = "DRY RUN" if options["dry_run"] else "WRITE"
        self.stdout.write(f"Course video lesson seed plan ({mode})")
        self.stdout.write("Video source: course-specific public embed when available, fallback HLS otherwise")
        for item in plan:
            self.stdout.write(
                f"  - {item['course'].slug}: lesson={item['lesson_action']}, "
                f"video={item['video_action']}, text={item['text_action']}, quiz={item['quiz_action']}"
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
            video_lesson = item["lesson"]
            if video_lesson is None:
                video_lesson = Lesson.objects.create(
                    course=course,
                    title=item["title"],
                    lesson_type=LessonType.VIDEO,
                    content=self._intro_content(course),
                    position=1,
                    is_published=True,
                    is_free_preview=True,
                    review_status=ContentReviewStatus.PUBLISHED,
                    published_version=1,
                )
                result["lessons_created"] += 1
                self._audit("course_video_lesson_seeded", video_lesson)
            elif options["update_existing"]:
                video_lesson.lesson_type = LessonType.VIDEO
                video_lesson.content = self._intro_content(course)
                video_lesson.position = 1
                video_lesson.is_published = True
                video_lesson.is_free_preview = True
                video_lesson.review_status = ContentReviewStatus.PUBLISHED
                video_lesson.published_version = max(video_lesson.published_version, 1)
                video_lesson.save(
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
                self._audit("course_video_lesson_updated", video_lesson)

            video, created = VideoLesson.objects.get_or_create(lesson=video_lesson)
            if created or options["update_existing"]:
                video.hls_url = COURSE_VIDEO_URLS.get(course.slug, options["hls_url"])
                video.thumbnail_url = options["thumbnail_url"]
                video.duration_seconds = 1800
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

            for lesson_type, title, content, position in (
                (
                    LessonType.TEXT,
                    f"{course.title}: Key ideas",
                    self._text_content(course),
                    2,
                ),
                (
                    LessonType.QUIZ,
                    f"{course.title}: Practice check",
                    self._quiz_content(course),
                    3,
                ),
            ):
                lesson = item[f"{lesson_type}_lesson"]
                if lesson is None:
                    lesson = Lesson.objects.create(
                        course=course,
                        title=title,
                        lesson_type=lesson_type,
                        content=content,
                        position=position,
                        is_published=True,
                        is_free_preview=False,
                        review_status=ContentReviewStatus.PUBLISHED,
                        published_version=1,
                    )
                    result["lessons_created"] += 1
                    self._audit(f"course_{lesson_type}_lesson_seeded", lesson)
                elif options["update_existing"]:
                    lesson.lesson_type = lesson_type
                    lesson.content = content
                    lesson.position = position
                    lesson.is_published = True
                    lesson.review_status = ContentReviewStatus.PUBLISHED
                    lesson.published_version = max(lesson.published_version, 1)
                    lesson.save(
                        update_fields=[
                            "lesson_type",
                            "content",
                            "position",
                            "is_published",
                            "review_status",
                            "published_version",
                            "updated_at",
                        ]
                    )
                    result["lessons_updated"] += 1
                    self._audit(f"course_{lesson_type}_lesson_updated", lesson)

            if not course.preview_video_url:
                course.preview_video_url = COURSE_VIDEO_URLS.get(course.slug, options["hls_url"])
                course.save(update_fields=["preview_video_url", "updated_at"])
        return result

    def _build_plan(self, course_slugs, courses, options):
        plan = []
        for slug in course_slugs:
            course = courses.get(slug)
            if course is None:
                continue
            title = f"{course.title}: Welcome video"
            text_title = f"{course.title}: Key ideas"
            quiz_title = f"{course.title}: Practice check"
            lesson = Lesson.objects.filter(course=course, title=title, deleted_at=None).first()
            text_lesson = Lesson.objects.filter(course=course, title=text_title, deleted_at=None).first()
            quiz_lesson = Lesson.objects.filter(course=course, title=quiz_title, deleted_at=None).first()
            lesson_action = "create" if lesson is None else "keep"
            text_action = "create" if text_lesson is None else "keep"
            quiz_action = "create" if quiz_lesson is None else "keep"
            video_action = "create"
            if lesson is not None:
                video_exists = VideoLesson.objects.filter(lesson=lesson).exists()
                video_action = "keep" if video_exists else "create"
                if options["update_existing"]:
                    lesson_action = "update"
                    text_action = "update"
                    quiz_action = "update"
                    video_action = "update"
            plan.append(
                {
                    "course": course,
                    "title": title,
                    "lesson": lesson,
                    "text_lesson": text_lesson,
                    "quiz_lesson": quiz_lesson,
                    "lesson_action": lesson_action,
                    "text_action": text_action,
                    "quiz_action": quiz_action,
                    "video_action": video_action,
                }
            )
        return plan

    def _intro_content(self, course):
        return (
            f"<p>This preview introduces <strong>{course.title}</strong> and shows how the "
            "topic connects to practical career skills on T-Career.</p>"
            "<p>The seeded video is a public learning resource for platform testing. "
            "Instructors should replace it with approved course-owned media before final publication.</p>"
        )

    def _text_content(self, course):
        outcomes = "".join(f"<li>{item}</li>" for item in course.what_you_learn[:4])
        requirements = "".join(f"<li>{item}</li>" for item in course.requirements[:3])
        return (
            f"<h2>{course.title}: Key ideas</h2>"
            f"<p>{course.description}</p>"
            "<h3>Learning outcomes</h3>"
            f"<ul>{outcomes}</ul>"
            "<h3>Before you continue</h3>"
            f"<ul>{requirements or '<li>Review the course overview and complete the video preview.</li>'}</ul>"
        )

    def _quiz_content(self, course):
        skill = course.tags[0] if course.tags else course.title
        return (
            f"<h2>{course.title}: Practice check</h2>"
            "<ol>"
            f"<li>What is one practical problem this course helps you solve with {skill}?</li>"
            "<li>Which requirement or prerequisite do you need to strengthen before continuing?</li>"
            "<li>Write one project idea you could add to your T-Career portfolio after this course.</li>"
            "</ol>"
            "<p>This preview quiz is stored as lesson content until the full assessment bank is approved.</p>"
        )

    def _audit(self, action, target):
        AuditLog.objects.create(
            actor=None,
            action=action,
            target_type=target.__class__.__name__,
            target_id=str(target.id),
            metadata={"source": SOURCE},
        )
