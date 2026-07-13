from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.audit.models import AuditLog
from apps.courses.models import Course, CourseStatus, Enrollment
from apps.courses.production_catalog import COURSES_BY_SLUG, SOURCE, TRACK_ATTACHMENTS
from apps.tracks.models import CareerTrack, TrackCourse


class Command(BaseCommand):
    help = "Seed production-safe courses and attach them to career tracks."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print planned changes only.")
        parser.add_argument(
            "--confirm-production",
            action="store_true",
            help="Required for writes when DEBUG=False.",
        )
        parser.add_argument("--track", help="Seed one supported track slug.")
        parser.add_argument("--all-tracks", action="store_true", help="Seed all supported tracks.")
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update existing seeded course fields and attachment metadata.",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Create or update courses as published after validation.",
        )
        parser.add_argument(
            "--instructor-email",
            required=True,
            help="Existing active instructor/platform admin email used as course owner.",
        )

    def handle(self, *args, **options):
        self._validate_options(options)
        instructor = self._get_instructor(options["instructor_email"])
        track_slugs = self._selected_track_slugs(options)
        plan = self._build_plan(track_slugs, instructor, options)
        self._print_plan(plan, options)

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run only. No database changes were made."))
            return

        with transaction.atomic():
            result = self._apply_plan(plan, instructor, options)

        self.stdout.write(
            self.style.SUCCESS(
                "Production course catalog seed complete: "
                f"{result['courses_created']} courses created, "
                f"{result['courses_updated']} courses updated, "
                f"{result['attachments_created']} attachments created, "
                f"{result['attachments_updated']} attachments updated."
            )
        )

    def _validate_options(self, options: dict[str, Any]) -> None:
        if options["track"] and options["all_tracks"]:
            raise CommandError("Use either --track or --all-tracks, not both.")
        if not options["track"] and not options["all_tracks"]:
            raise CommandError("Choose --track <slug> or --all-tracks.")
        if not settings.DEBUG and not options["dry_run"] and not options["confirm_production"]:
            raise CommandError(
                "Refusing to write in production without --confirm-production. "
                "Run --dry-run first, review output, then rerun with --confirm-production."
            )

    def _get_instructor(self, email: str):
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise CommandError(f"Instructor not found: {email}") from exc
        if not user.is_active:
            raise CommandError(f"Instructor is inactive: {email}")
        allowed_roles = {"instructor", "platform_admin", "super_admin", "admin"}
        if user.role not in allowed_roles and not user.is_staff:
            raise CommandError(
                "Course owner must be an instructor, platform admin, super admin, admin, "
                "or staff user."
            )
        return user

    def _selected_track_slugs(self, options: dict[str, Any]) -> list[str]:
        if options["all_tracks"]:
            return sorted(TRACK_ATTACHMENTS)
        slug = options["track"]
        if slug not in TRACK_ATTACHMENTS:
            supported = ", ".join(sorted(TRACK_ATTACHMENTS))
            raise CommandError(f"Unsupported track '{slug}'. Supported tracks: {supported}")
        return [slug]

    def _build_plan(self, track_slugs: list[str], instructor, options: dict[str, Any]):
        plan = {"tracks": [], "courses": {}, "attachments": []}
        for track_slug in track_slugs:
            try:
                track = CareerTrack.objects.get(slug=track_slug)
            except CareerTrack.DoesNotExist as exc:
                raise CommandError(f"Career track not found: {track_slug}") from exc
            plan["tracks"].append(track)

            for attachment in TRACK_ATTACHMENTS[track_slug]:
                course_def = COURSES_BY_SLUG[attachment.course_slug]
                existing_course = Course.objects.filter(slug=course_def.slug).first()
                desired_status = (
                    CourseStatus.PUBLISHED if options["publish"] else CourseStatus.DRAFT
                )
                course_action = "create" if existing_course is None else "keep"
                if existing_course and options["update_existing"]:
                    course_action = "update"
                plan["courses"][course_def.slug] = {
                    "definition": course_def,
                    "existing": existing_course,
                    "action": course_action,
                    "desired_status": desired_status,
                }

                existing_attachment = None
                if existing_course:
                    existing_attachment = TrackCourse.objects.filter(
                        track=track, course=existing_course
                    ).first()
                attachment_action = "create" if existing_attachment is None else "keep"
                if existing_attachment and options["update_existing"]:
                    changed = (
                        existing_attachment.position != attachment.position
                        or existing_attachment.stage != attachment.stage
                        or existing_attachment.is_required != attachment.is_required
                        or existing_attachment.notes != attachment.notes
                    )
                    attachment_action = "update" if changed else "keep"
                plan["attachments"].append(
                    {
                        "track": track,
                        "definition": attachment,
                        "existing": existing_attachment,
                        "action": attachment_action,
                    }
                )
        self._validate_course_definitions(plan["courses"].values(), instructor)
        return plan

    def _validate_course_definitions(self, course_plans, instructor) -> None:
        errors = {}
        for item in course_plans:
            course_def = item["definition"]
            course = item["existing"] or Course(slug=course_def.slug, instructor=instructor)
            self._assign_course_fields(course, course_def, instructor, item["desired_status"])
            try:
                course.full_clean()
            except ValidationError as exc:
                errors[course_def.slug] = exc.message_dict
        if errors:
            raise CommandError(f"Invalid course data: {errors}")

    def _print_plan(self, plan, options: dict[str, Any]) -> None:
        mode = "DRY RUN" if options["dry_run"] else "WRITE"
        self.stdout.write(f"Production course catalog plan ({mode})")
        self.stdout.write(f"Publish mode: {'published' if options['publish'] else 'draft'}")
        for track in plan["tracks"]:
            self.stdout.write(f"\nTrack: {track.slug} ({track.title})")
            for attachment in plan["attachments"]:
                if attachment["track"].id != track.id:
                    continue
                course_def = COURSES_BY_SLUG[attachment["definition"].course_slug]
                course_action = plan["courses"][course_def.slug]["action"]
                self.stdout.write(
                    f"  - {attachment['definition'].position:03d} {course_def.title} "
                    f"[course={course_action}, attachment={attachment['action']}]"
                )

    def _apply_plan(self, plan, instructor, options: dict[str, Any]) -> dict[str, int]:
        result = {
            "courses_created": 0,
            "courses_updated": 0,
            "attachments_created": 0,
            "attachments_updated": 0,
        }
        course_objects: dict[str, Course] = {}
        for slug, item in plan["courses"].items():
            course_def = item["definition"]
            course = item["existing"]
            if course is None:
                course = Course(slug=slug, instructor=instructor)
                self._assign_course_fields(course, course_def, instructor, item["desired_status"])
                course.save()
                result["courses_created"] += 1
                self._audit("course_seeded", "Course", course.id, course_def=course_def)
                if course.status == CourseStatus.PUBLISHED:
                    self._audit("course_published", "Course", course.id, course_def=course_def)
            elif options["update_existing"]:
                old_status = course.status
                self._assign_course_fields(course, course_def, instructor, item["desired_status"])
                course.save()
                result["courses_updated"] += 1
                self._audit("course_updated", "Course", course.id, course_def=course_def)
                if old_status != CourseStatus.PUBLISHED and course.status == CourseStatus.PUBLISHED:
                    self._audit("course_published", "Course", course.id, course_def=course_def)
            course_objects[slug] = course

        for item in plan["attachments"]:
            attachment_def = item["definition"]
            course = course_objects[attachment_def.course_slug]
            existing = TrackCourse.objects.filter(track=item["track"], course=course).first()
            defaults = {
                "position": attachment_def.position,
                "stage": attachment_def.stage,
                "is_required": attachment_def.is_required,
                "notes": attachment_def.notes,
            }
            if existing is None:
                track_course = TrackCourse.objects.create(
                    track=item["track"], course=course, **defaults
                )
                result["attachments_created"] += 1
                self._audit(
                    "course_attached_to_track",
                    "TrackCourse",
                    track_course.id,
                    track=item["track"],
                    course=course,
                    attachment=attachment_def,
                )
            elif options["update_existing"]:
                old_position = existing.position
                for field, value in defaults.items():
                    setattr(existing, field, value)
                existing.save()
                result["attachments_updated"] += 1
                action = (
                    "attachment_order_changed"
                    if old_position != attachment_def.position
                    else "course_track_attachment_updated"
                )
                self._audit(
                    action,
                    "TrackCourse",
                    existing.id,
                    track=item["track"],
                    course=course,
                    attachment=attachment_def,
                    old_position=old_position,
                )

        if Enrollment.objects.filter(course__slug__in=course_objects).exists():
            raise CommandError("Safety violation: seed command must not create enrollments.")
        return result

    def _assign_course_fields(self, course, course_def, instructor, status: str) -> None:
        course.instructor = instructor
        course.title = course_def.title
        course.short_description = course_def.short_description
        course.description = course_def.description
        course.level = course_def.level
        course.status = status
        course.price = course_def.price
        course.language = course_def.language
        course.tags = list(course_def.tags)
        course.requirements = list(course_def.requirements)
        course.what_you_learn = list(course_def.what_you_learn)

    def _audit(self, action: str, target_type: str, target_id, **metadata) -> None:
        serializable = {}
        for key, value in metadata.items():
            if hasattr(value, "id"):
                serializable[key] = {
                    "id": str(value.id),
                    "title": getattr(value, "title", str(value)),
                }
            elif hasattr(value, "__dataclass_fields__"):
                serializable[key] = asdict(value)
            else:
                serializable[key] = value
        serializable["source"] = SOURCE
        AuditLog.objects.create(
            actor=None,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=serializable,
        )
