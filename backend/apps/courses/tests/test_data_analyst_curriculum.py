from __future__ import annotations

import csv
import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assessments.models import CourseRating, QuestionReviewStatus, QuizAttempt, QuizQuestion
from apps.certificates.models import Certificate
from apps.courses.data_analyst_curriculum import CURRICULA
from apps.courses.models import Course, CourseStatus, Enrollment, Lesson
from apps.courses.production_catalog import COURSES_BY_SLUG
from apps.users.models import User
from apps.users.tests.factories import InstructorFactory, UserFactory


@pytest.fixture
def instructor(db):
    return InstructorFactory(email="curriculum.instructor@example.com")


def create_course_shells(instructor, slugs: list[str] | None = None):
    selected = slugs or list(CURRICULA.keys())
    for slug in selected:
        course_def = COURSES_BY_SLUG[slug]
        Course.objects.create(
            instructor=instructor,
            title=course_def.title,
            slug=slug,
            short_description=course_def.short_description,
            description=course_def.description,
            level=course_def.level,
            status=CourseStatus.DRAFT,
            price=course_def.price,
            requirements=list(course_def.requirements),
            what_you_learn=list(course_def.what_you_learn),
        )


def run_content_seed(instructor, *args, confirm=True):
    output = io.StringIO()
    command_args = [
        "--instructor-email",
        instructor.email,
        *args,
    ]
    if confirm and "--dry-run" not in args:
        command_args.append("--confirm-production")
    call_command("seed_data_analyst_course_content", *command_args, stdout=output)
    return output.getvalue()


@pytest.mark.django_db
def test_dry_run_writes_nothing(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    output = run_content_seed(
        instructor,
        "--course",
        "excel-for-data-analysis",
        "--dry-run",
    )

    assert "Dry run only" in output
    assert Lesson.objects.count() == 0
    assert QuizQuestion.objects.count() == 0


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_production_guard_blocks_without_confirmation(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    with pytest.raises(CommandError, match="confirm-production"):
        run_content_seed(
            instructor,
            "--course",
            "excel-for-data-analysis",
            confirm=False,
        )

    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_seed_creates_no_fake_users_or_activity(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])
    before_users = User.objects.count()

    run_content_seed(instructor, "--course", "excel-for-data-analysis")

    assert User.objects.count() == before_users
    assert Enrollment.objects.count() == 0
    assert CourseRating.objects.count() == 0
    assert QuizAttempt.objects.count() == 0
    assert Certificate.objects.count() == 0


@pytest.mark.django_db
def test_idempotent_rerun_prevents_duplicate_lessons_and_assessments(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    run_content_seed(instructor, "--course", "excel-for-data-analysis")
    first_lessons = Lesson.objects.count()
    first_questions = QuizQuestion.objects.count()
    run_content_seed(instructor, "--course", "excel-for-data-analysis")

    assert Lesson.objects.count() == first_lessons
    assert QuizQuestion.objects.count() == first_questions


@pytest.mark.django_db
def test_correct_lesson_order_and_no_duplicate_titles(instructor):
    create_course_shells(instructor, ["sql-for-data-analysis"])

    run_content_seed(instructor, "--course", "sql-for-data-analysis")

    lessons = list(Lesson.objects.order_by("position"))
    assert [lesson.position for lesson in lessons] == sorted(lesson.position for lesson in lessons)
    assert len({lesson.title for lesson in lessons}) == len(lessons)
    assert lessons[0].title == "Relational concepts"


@pytest.mark.django_db
def test_existing_manual_lesson_preserved_without_update_existing(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])
    course = Course.objects.get(slug="excel-for-data-analysis")
    Lesson.objects.create(
        course=course,
        title="Excel foundations",
        content="Manual instructor content",
        position=999,
        is_published=True,
    )

    run_content_seed(instructor, "--course", "excel-for-data-analysis")

    lesson = Lesson.objects.get(title="Excel foundations")
    assert lesson.content == "Manual instructor content"
    assert lesson.position == 999
    assert lesson.is_published is True


@pytest.mark.django_db
def test_update_existing_rewrites_seeded_lesson_to_review_required_draft(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])
    course = Course.objects.get(slug="excel-for-data-analysis")
    Lesson.objects.create(
        course=course,
        title="Excel foundations",
        content="Old content",
        position=999,
        is_published=True,
    )

    run_content_seed(instructor, "--course", "excel-for-data-analysis", "--update-existing")

    lesson = Lesson.objects.get(title="Excel foundations")
    assert "## Excel-specific explanation" in lesson.content
    assert "workbook" in lesson.content.lower()
    assert lesson.position == 10
    assert lesson.is_published is False


@pytest.mark.django_db
def test_invalid_instructor_rejected(instructor):
    student = UserFactory(email="student@example.com")
    create_course_shells(instructor, ["excel-for-data-analysis"])

    with pytest.raises(CommandError, match="owner"):
        run_content_seed(student, "--course", "excel-for-data-analysis")


@pytest.mark.django_db
def test_transaction_rollback_when_course_missing(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    with pytest.raises(CommandError, match="Course shell not found"):
        run_content_seed(instructor, "--all-courses")

    assert Lesson.objects.count() == 0
    assert QuizQuestion.objects.count() == 0


@pytest.mark.django_db
def test_draft_lessons_hidden_publicly_and_published_lessons_exposed(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])
    course = Course.objects.get(slug="excel-for-data-analysis")
    run_content_seed(instructor, "--course", "excel-for-data-analysis")
    course.status = CourseStatus.PUBLISHED
    course.save(update_fields=["status", "updated_at"])
    client = APIClient()

    draft_response = client.get(reverse("courses:course-detail", kwargs={"slug": course.slug}))
    assert draft_response.status_code == 200
    assert draft_response.json()["data"]["lessons"] == []

    lesson = Lesson.objects.filter(course=course).order_by("position").first()
    lesson.is_published = True
    lesson.save(update_fields=["is_published", "updated_at"])

    published_response = client.get(reverse("courses:course-detail", kwargs={"slug": course.slug}))
    assert published_response.status_code == 200
    assert len(published_response.json()["data"]["lessons"]) == 1


@pytest.mark.django_db
def test_assessments_review_required_and_no_certificate_issued(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    run_content_seed(instructor, "--course", "excel-for-data-analysis", "--publish-ready")

    assert QuizQuestion.objects.count() == 23
    assert all(
        question.review_status == QuestionReviewStatus.REVIEW_REQUIRED
        and question.is_certificate_eligible is False
        for question in QuizQuestion.objects.all()
    )
    assert Certificate.objects.count() == 0


@pytest.mark.django_db
def test_excel_lessons_are_lesson_specific_and_have_required_sections(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    run_content_seed(instructor, "--course", "excel-for-data-analysis")

    lessons = list(Lesson.objects.order_by("position"))
    assert len(lessons) == 10
    required_sections = [
        "## Measurable objective",
        "## Excel-specific explanation",
        "## Worked example",
        "## Common mistakes",
        "## Guided practice",
        "## Independent practice",
        "## Expected output",
        "## Validation checklist",
        "## Version note",
    ]
    for lesson in lessons:
        for section in required_sections:
            assert section in lesson.content
        assert "generic analyst workflow" not in lesson.content.lower()
        assert "Content status: review_required" not in lesson.content


@pytest.mark.django_db
def test_excel_assessment_bank_covers_course_and_question_types(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    run_content_seed(instructor, "--course", "excel-for-data-analysis")

    questions = QuizQuestion.objects.order_by("position")
    assert questions.count() == 23
    assert questions.filter(question_type="applied_formula").count() >= 4
    assert questions.filter(question_type="data_cleaning_scenario").count() >= 3
    assert questions.filter(question_type="pivot_interpretation").count() >= 2
    assert questions.filter(question_type="chart_selection").count() >= 2
    covered = set(questions.values_list("lesson_mapping", flat=True))
    assert "Final dashboard project" in covered
    assert "Formulas and functions" in covered


@pytest.mark.django_db
def test_narrow_update_dry_run_writes_nothing_and_reports_fields(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])
    run_content_seed(instructor, "--course", "excel-for-data-analysis")
    before = list(Lesson.objects.values_list("id", "updated_at"))

    output = run_content_seed(
        instructor,
        "--course",
        "excel-for-data-analysis",
        "--update-existing",
        "--fields",
        "lesson_content,assessments",
        "--dry-run",
    )

    assert "Requested update fields: lesson_content,assessments" in output
    assert list(Lesson.objects.values_list("id", "updated_at")) == before


def test_excel_dataset_resource_is_reviewable():
    dataset_path = "apps/courses/resources/excel_retail_sales_sample.csv"
    with open(dataset_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 150
    assert set(rows[0]) == {
        "order_id",
        "order_date",
        "region",
        "city",
        "salesperson",
        "product",
        "category",
        "units",
        "unit_price",
        "discount",
        "revenue",
        "cost",
        "profit",
        "customer_segment",
    }
    assert any(row["discount"] == "" for row in rows)
    assert any(row["region"] != row["region"].strip() or row["region"].islower() for row in rows)
    assert len({row["order_id"] for row in rows}) < len(rows)


def test_excel_dataset_generator_is_deterministic(tmp_path):
    from apps.courses.management.commands.generate_excel_course_dataset import generate_rows

    assert generate_rows(rows=150, seed=42) == generate_rows(rows=150, seed=42)
    assert generate_rows(rows=150, seed=42) != generate_rows(rows=150, seed=43)


@pytest.mark.django_db
def test_readiness_report_detects_incomplete_and_ready_courses(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])
    output = io.StringIO()

    call_command(
        "course_content_readiness_report",
        "--course",
        "excel-for-data-analysis",
        "--json",
        stdout=output,
    )
    assert '"content_readiness": false' in output.getvalue()

    run_content_seed(instructor, "--course", "excel-for-data-analysis")
    ready_output = io.StringIO()
    call_command(
        "course_content_readiness_report",
        "--course",
        "excel-for-data-analysis",
        "--json",
        stdout=ready_output,
    )
    assert '"content_readiness": true' in ready_output.getvalue()


@pytest.mark.django_db
def test_readiness_report_fail_on_not_ready(instructor):
    create_course_shells(instructor, ["excel-for-data-analysis"])

    with pytest.raises(CommandError, match="not ready"):
        call_command(
            "course_content_readiness_report",
            "--course",
            "excel-for-data-analysis",
            "--fail-on-not-ready",
        )
