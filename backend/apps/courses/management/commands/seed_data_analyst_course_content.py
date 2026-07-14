from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.assessments.models import CourseRating, QuizQuestion
from apps.audit.models import AuditLog
from apps.certificates.models import Certificate
from apps.courses.data_analyst_curriculum import (
    CURRICULA,
    SOURCE,
    build_lesson_body,
)
from apps.courses.models import Course, CourseStatus, Enrollment, Lesson, LessonType


class Command(BaseCommand):
    help = "Seed review-required Data Analyst course lesson and assessment content."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--confirm-production", action="store_true")
        parser.add_argument("--course", help="Seed one Data Analyst course slug.")
        parser.add_argument("--all-courses", action="store_true")
        parser.add_argument("--instructor-email", required=True)
        parser.add_argument("--update-existing", action="store_true")
        parser.add_argument(
            "--fields",
            default="",
            help="Comma-separated update fields: lesson_content,objectives,exercises,assessments.",
        )
        parser.add_argument(
            "--publish-ready",
            action="store_true",
            help="Mark content as review-ready in metadata/audit only. Does not publish.",
        )

    def handle(self, *args, **options):
        self._validate_options(options)
        instructor = self._get_instructor(options["instructor_email"])
        slugs = self._selected_course_slugs(options)
        plan = self._build_plan(slugs, instructor, options)
        self._print_plan(plan, options)

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run only. No database changes were made."))
            return

        with transaction.atomic():
            result = self._apply_plan(plan, options)

        self.stdout.write(
            self.style.SUCCESS(
                "Data Analyst curriculum seed complete: "
                f"{result['lessons_created']} lessons created, "
                f"{result['lessons_updated']} lessons updated, "
                f"{result['assessments_created']} assessment questions created, "
                f"{result['assessments_updated']} assessment questions updated."
            )
        )

    def _validate_options(self, options: dict[str, Any]) -> None:
        if options["course"] and options["all_courses"]:
            raise CommandError("Use either --course or --all-courses, not both.")
        if not options["course"] and not options["all_courses"]:
            raise CommandError("Choose --course <slug> or --all-courses.")
        if not settings.DEBUG and not options["dry_run"] and not options["confirm_production"]:
            raise CommandError("Refusing production write without --confirm-production.")
        allowed_fields = {"lesson_content", "objectives", "exercises", "assessments"}
        requested = self._requested_fields(options)
        unknown = requested - allowed_fields
        if unknown:
            raise CommandError("Unsupported --fields value(s): " + ", ".join(sorted(unknown)))
        if options["update_existing"] and options["all_courses"] and requested:
            raise CommandError("Field-level --update-existing is only supported with --course.")

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
            raise CommandError("Course content owner must be instructor/admin/staff.")
        return user

    def _selected_course_slugs(self, options: dict[str, Any]) -> list[str]:
        if options["all_courses"]:
            return list(CURRICULA.keys())
        slug = options["course"]
        if slug not in CURRICULA:
            supported = ", ".join(CURRICULA)
            raise CommandError(f"Unsupported course '{slug}'. Supported courses: {supported}")
        return [slug]

    def _build_plan(self, slugs: list[str], instructor, options: dict[str, Any]):
        plan = []
        requested_fields = self._requested_fields(options)
        for slug in slugs:
            curriculum = CURRICULA[slug]
            try:
                course = Course.objects.get(slug=slug, deleted_at=None)
            except Course.DoesNotExist as exc:
                raise CommandError(f"Course shell not found: {slug}") from exc
            if course.instructor_id != instructor.id and not instructor.is_staff:
                raise CommandError(f"Instructor {instructor.email} does not own course {slug}.")
            lessons = []
            position = 0
            for module in curriculum.modules:
                for lesson_def in module.lessons:
                    position += 10
                    existing = Lesson.objects.filter(
                        course=course,
                        title=lesson_def.title,
                        deleted_at=None,
                    ).first()
                    action = "create" if existing is None else "keep"
                    if (
                        existing
                        and options["update_existing"]
                        and self._should_update_lesson(requested_fields)
                    ):
                        action = "update"
                    lessons.append(
                        {
                            "module": module,
                            "definition": lesson_def,
                            "position": position,
                            "existing": existing,
                            "action": action,
                        }
                    )
            assessments = []
            for index, question in enumerate(curriculum.assessments, start=1):
                existing = QuizQuestion.objects.filter(
                    course=course,
                    question_text=question.question_text,
                ).first()
                if (
                    existing is None
                    and options["update_existing"]
                    and self._should_update_assessments(requested_fields)
                ):
                    existing = QuizQuestion.objects.filter(
                        course=course,
                        position=index * 10,
                    ).first()
                action = "create" if existing is None else "keep"
                if (
                    existing
                    and options["update_existing"]
                    and self._should_update_assessments(requested_fields)
                ):
                    action = "update"
                assessments.append(
                    {
                        "definition": question,
                        "position": index * 10,
                        "existing": existing,
                        "action": action,
                    }
                )
            plan.append(
                {
                    "course": course,
                    "curriculum": curriculum,
                    "lessons": lessons,
                    "assessments": assessments,
                }
            )
        return plan

    def _print_plan(self, plan, options: dict[str, Any]) -> None:
        mode = "DRY RUN" if options["dry_run"] else "WRITE"
        self.stdout.write(f"Data Analyst curriculum plan ({mode})")
        self.stdout.write("Lessons remain draft. Courses are not published.")
        if options.get("fields"):
            self.stdout.write(f"Requested update fields: {options['fields']}")
        for item in plan:
            self.stdout.write(f"\nCourse: {item['course'].slug} ({item['course'].title})")
            self.stdout.write(
                f"  modules={len(item['curriculum'].modules)} "
                f"lessons={len(item['lessons'])} assessments={len(item['assessments'])}"
            )
            for lesson in item["lessons"]:
                self.stdout.write(
                    f"  - {lesson['position']:03d} {lesson['definition'].title} "
                    f"[{lesson['action']}]"
                )
            for assessment in item["assessments"]:
                self.stdout.write(
                    f"  - Q{assessment['position']:03d} "
                    f"{assessment['definition'].lesson_mapping or 'course'} "
                    f"[{assessment['action']}]"
                )

    def _apply_plan(self, plan, options: dict[str, Any]) -> dict[str, int]:
        before = self._safety_counts()
        result = {
            "lessons_created": 0,
            "lessons_updated": 0,
            "assessments_created": 0,
            "assessments_updated": 0,
        }
        for item in plan:
            course = item["course"]
            curriculum = item["curriculum"]
            self._apply_course_metadata(course, curriculum, options)
            for lesson_item in item["lessons"]:
                module = lesson_item["module"]
                lesson_def = lesson_item["definition"]
                body = build_lesson_body(course.title, module.title, lesson_def)
                lesson = lesson_item["existing"]
                if lesson is None:
                    lesson = Lesson.objects.create(
                        course=course,
                        title=lesson_def.title,
                        lesson_type=LessonType.TEXT,
                        content=body,
                        position=lesson_item["position"],
                        is_published=False,
                        is_free_preview=False,
                    )
                    result["lessons_created"] += 1
                    self._audit("lesson_seeded", "Lesson", lesson.id, course, lesson_def)
                elif lesson_item["action"] == "update":
                    old_position = lesson.position
                    lesson.lesson_type = LessonType.TEXT
                    lesson.content = body
                    lesson.position = lesson_item["position"]
                    lesson.is_published = False
                    lesson.save()
                    result["lessons_updated"] += 1
                    action = (
                        "ordering_changed"
                        if old_position != lesson_item["position"]
                        else "lesson_updated"
                    )
                    self._audit(action, "Lesson", lesson.id, course, lesson_def)

            for assessment_item in item["assessments"]:
                question_def = assessment_item["definition"]
                question = assessment_item["existing"]
                if question is None:
                    question = QuizQuestion.objects.create(
                        course=course,
                        question_text=question_def.question_text,
                        options=list(question_def.options),
                        correct_index=question_def.correct_index,
                        explanation=question_def.explanation,
                        position=assessment_item["position"],
                        question_type=question_def.question_type,
                        lesson_mapping=question_def.lesson_mapping,
                        difficulty=question_def.difficulty,
                        review_status=question_def.review_status,
                        is_certificate_eligible=False,
                    )
                    result["assessments_created"] += 1
                    self._audit(
                        "assessment_seeded", "QuizQuestion", question.id, course, question_def
                    )
                elif assessment_item["action"] == "update":
                    question.question_text = question_def.question_text
                    question.options = list(question_def.options)
                    question.correct_index = question_def.correct_index
                    question.explanation = question_def.explanation
                    question.position = assessment_item["position"]
                    question.question_type = question_def.question_type
                    question.lesson_mapping = question_def.lesson_mapping
                    question.difficulty = question_def.difficulty
                    question.review_status = question_def.review_status
                    question.reviewed_by = None
                    question.reviewed_at = None
                    question.review_notes = ""
                    question.is_certificate_eligible = False
                    question.save()
                    result["assessments_updated"] += 1
                    self._audit(
                        "assessment_updated", "QuizQuestion", question.id, course, question_def
                    )

            if options["publish_ready"]:
                self._audit(
                    "content_marked_review_ready",
                    "Course",
                    course.id,
                    course,
                    {"content_status": curriculum.content_status},
                )

        after = self._safety_counts()
        if before != after:
            raise CommandError("Safety violation: learner activity counts changed.")
        return result

    def _apply_course_metadata(self, course: Course, curriculum, options: dict[str, Any]) -> None:
        requested = self._requested_fields(options)
        if requested and "objectives" not in requested:
            return
        if not options["update_existing"] and (course.requirements or course.what_you_learn):
            return
        course.requirements = list(curriculum.prerequisites)
        course.what_you_learn = list(curriculum.objectives)
        tags = set(course.tags or [])
        tags.add("data-analyst-curriculum")
        tags.add("content-status:review-required")
        course.tags = sorted(tags)
        course.status = CourseStatus.DRAFT
        course.save(
            update_fields=["requirements", "what_you_learn", "tags", "status", "updated_at"]
        )

    def _requested_fields(self, options: dict[str, Any]) -> set[str]:
        raw = options.get("fields") or ""
        return {field.strip() for field in raw.split(",") if field.strip()}

    def _should_update_lesson(self, requested_fields: set[str]) -> bool:
        return not requested_fields or bool({"lesson_content", "exercises"} & requested_fields)

    def _should_update_assessments(self, requested_fields: set[str]) -> bool:
        return not requested_fields or "assessments" in requested_fields

    def _safety_counts(self) -> tuple[int, int, int, int]:
        return (
            get_user_model().objects.count(),
            Enrollment.objects.count(),
            CourseRating.objects.count(),
            Certificate.objects.count(),
        )

    def _audit(self, action: str, target_type: str, target_id, course, payload) -> None:
        metadata = {
            "source": SOURCE,
            "course_id": str(course.id),
            "course_slug": course.slug,
        }
        if hasattr(payload, "__dataclass_fields__"):
            metadata["definition"] = asdict(payload)
        elif isinstance(payload, dict):
            metadata.update(payload)
        AuditLog.objects.create(
            actor=None,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=metadata,
        )
