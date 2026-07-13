from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.assessments.models import QuizQuestion
from apps.courses.data_analyst_curriculum import CURRICULA
from apps.courses.models import Course, CourseStatus, Lesson
from apps.tracks.models import TrackCourse


class Command(BaseCommand):
    help = "Report review readiness for course curriculum content."

    def add_arguments(self, parser):
        parser.add_argument("--course", help="Limit to one course slug.")
        parser.add_argument("--track", choices=["data-analyst"], help="Report a supported track.")
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--fail-on-not-ready", action="store_true")

    def handle(self, *args, **options):
        slugs = self._selected_slugs(options)
        report = [self._course_report(slug) for slug in slugs]
        payload = {
            "courses": report,
            "track_readiness": all(item["content_readiness"] for item in report),
        }
        if options["json"]:
            self.stdout.write(json.dumps(payload, indent=2))
        else:
            self._print_report(payload)
        if options["fail_on_not_ready"] and not payload["track_readiness"]:
            not_ready = [item["course"] for item in report if not item["content_readiness"]]
            raise CommandError(f"Courses not ready for manual review: {', '.join(not_ready)}")

    def _selected_slugs(self, options: dict) -> list[str]:
        if options["course"] and options["track"]:
            raise CommandError("Use either --course or --track, not both.")
        if options["course"]:
            if options["course"] not in CURRICULA:
                raise CommandError(f"Unsupported course: {options['course']}")
            return [options["course"]]
        if options["track"] == "data-analyst":
            slugs = list(
                TrackCourse.objects.filter(track__slug="data-analyst")
                .order_by("position")
                .values_list("course__slug", flat=True)
            )
            return [slug for slug in slugs if slug in CURRICULA] or list(CURRICULA.keys())
        return list(CURRICULA.keys())

    def _course_report(self, slug: str) -> dict:
        curriculum = CURRICULA[slug]
        course = (
            Course.objects.filter(slug=slug, deleted_at=None)
            .select_related("instructor")
            .first()
        )
        if course is None:
            return {
                "course": slug,
                "exists": False,
                "module_count": len(curriculum.modules),
                "lesson_count": 0,
                "assessment_count": 0,
                "content_readiness": False,
                "missing_instructor": True,
                "missing_prerequisites": list(curriculum.prerequisites),
                "missing_objectives": list(curriculum.objectives),
                "empty_lesson_count": 0,
                "missing_assessment": True,
                "course_publish_status": "missing",
            }
        lessons = Lesson.objects.filter(course=course, deleted_at=None)
        expected_titles = [
            lesson.title
            for module in curriculum.modules
            for lesson in module.lessons
        ]
        empty_lessons = lessons.filter(content__exact="").count()
        missing_titles = [
            title for title in expected_titles if not lessons.filter(title=title).exists()
        ]
        assessment_count = QuizQuestion.objects.filter(course=course).count()
        missing_objectives = not bool(course.what_you_learn)
        missing_prerequisites = not bool(course.requirements)
        ready = (
            course.instructor_id is not None
            and not missing_objectives
            and not missing_prerequisites
            and not missing_titles
            and empty_lessons == 0
            and assessment_count > 0
            and course.status == CourseStatus.DRAFT
        )
        return {
            "course": slug,
            "exists": True,
            "module_count": len(curriculum.modules),
            "lesson_count": lessons.count(),
            "expected_lesson_count": len(expected_titles),
            "lesson_status": {
                "draft": lessons.filter(is_published=False).count(),
                "published": lessons.filter(is_published=True).count(),
            },
            "assessment_count": assessment_count,
            "empty_lesson_count": empty_lessons,
            "missing_lessons": missing_titles,
            "missing_objectives": missing_objectives,
            "missing_prerequisites": missing_prerequisites,
            "missing_instructor": course.instructor_id is None,
            "missing_assessment": assessment_count == 0,
            "course_publish_status": course.status,
            "content_readiness": ready,
        }

    def _print_report(self, payload: dict) -> None:
        self.stdout.write("Course content readiness report")
        for item in payload["courses"]:
            self.stdout.write(
                f"- {item['course']}: modules={item['module_count']} "
                f"lessons={item['lesson_count']} assessments={item['assessment_count']} "
                f"ready={item['content_readiness']}"
            )
            if item.get("missing_lessons"):
                self.stdout.write(f"  missing lessons: {item['missing_lessons']}")
        self.stdout.write(f"Track readiness: {payload['track_readiness']}")
