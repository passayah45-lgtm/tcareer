from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.courses.models import (
    Course,
    CourseStatus,
    Enrollment,
    Lesson,
    LessonType,
    TranscodingStatus,
    VideoLesson,
)
from apps.courses.production_catalog import TRACK_ATTACHMENTS
from apps.tracks.models import CareerTrack, TrackCourse
from apps.users.models import User
from apps.users.tests.factories import InstructorFactory, UserFactory


@pytest.fixture
def data_analyst_track(db):
    return CareerTrack.objects.create(
        title="Data Analyst",
        slug="data-analyst",
        short_description="Data analyst path",
        description="Learn analytics.",
        category="data_ai",
        difficulty="beginner",
        position=1,
        is_active=True,
    )


@pytest.fixture
def full_stack_track(db):
    return CareerTrack.objects.create(
        title="Full Stack Developer",
        slug="full-stack-developer",
        short_description="Full stack developer path",
        description="Learn frontend, backend, and deployment.",
        category="tech",
        difficulty="beginner",
        position=2,
        is_active=True,
    )


def run_seed(instructor, *args, confirm=True):
    output = io.StringIO()
    command_args = [
        "--track",
        "data-analyst",
        "--instructor-email",
        instructor.email,
        *args,
    ]
    if confirm and "--dry-run" not in args:
        command_args.append("--confirm-production")
    call_command(
        "seed_production_course_catalog",
        *command_args,
        stdout=output,
    )
    return output.getvalue()


def run_track_seed(instructor, track_slug, *args, confirm=True):
    output = io.StringIO()
    command_args = [
        "--track",
        track_slug,
        "--instructor-email",
        instructor.email,
        *args,
    ]
    if confirm and "--dry-run" not in args:
        command_args.append("--confirm-production")
    call_command(
        "seed_production_course_catalog",
        *command_args,
        stdout=output,
    )
    return output.getvalue()


def run_course_seed(instructor, course_slug, *args, confirm=True):
    output = io.StringIO()
    command_args = [
        "--course",
        course_slug,
        "--instructor-email",
        instructor.email,
        *args,
    ]
    if confirm and "--dry-run" not in args:
        command_args.append("--confirm-production")
    call_command(
        "seed_production_course_catalog",
        *command_args,
        stdout=output,
    )
    return output.getvalue()


@pytest.mark.django_db
def test_dry_run_makes_no_changes(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    output = run_seed(instructor, "--dry-run")

    assert "Dry run only" in output
    assert Course.objects.count() == 0
    assert TrackCourse.objects.count() == 0
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_single_course_dry_run_plans_only_excel(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    output = run_course_seed(instructor, "excel-for-data-analysis", "--dry-run")

    assert "Excel for Data Analysis" in output
    assert "SQL for Data Analysis" not in output
    assert Course.objects.count() == 0
    assert TrackCourse.objects.count() == 0


@pytest.mark.django_db
def test_single_course_seed_creates_only_excel_and_one_attachment(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    run_course_seed(instructor, "excel-for-data-analysis")

    assert list(Course.objects.values_list("slug", flat=True)) == ["excel-for-data-analysis"]
    assert TrackCourse.objects.count() == 1
    track_course = TrackCourse.objects.select_related("course", "track").get()
    assert track_course.track.slug == "data-analyst"
    assert track_course.course.slug == "excel-for-data-analysis"
    assert track_course.position == 10
    assert track_course.course.status == CourseStatus.DRAFT


@pytest.mark.django_db
def test_full_stack_seed_creates_priced_track_courses(full_stack_track):
    instructor = InstructorFactory(email="instructor@example.com")
    client = APIClient()

    run_track_seed(instructor, "full-stack-developer", "--publish")

    attachments = TrackCourse.objects.filter(track=full_stack_track).select_related("course")
    assert attachments.count() == len(TRACK_ATTACHMENTS["full-stack-developer"])
    assert attachments.filter(is_required=True).count() == 7
    assert str(Course.objects.get(slug="javascript-essentials").price) == "19.99"
    assert str(Course.objects.get(slug="html-and-css-from-zero").price) == "0.00"

    response = client.get(
        reverse("tracks:track-detail", kwargs={"slug": "full-stack-developer"})
    )
    assert response.status_code == 200
    courses = [
        course
        for stage in response.json()["data"]["courses_by_stage"]
        for course in stage["courses"]
    ]
    assert courses[0]["course_slug"] == "html-and-css-from-zero"
    assert any(course["course_price"] == "29.99" for course in courses)


@pytest.mark.django_db
def test_video_lesson_seed_dry_run_makes_no_changes(full_stack_track):
    instructor = InstructorFactory(email="instructor@example.com")
    run_track_seed(instructor, "full-stack-developer", "--publish")
    output = io.StringIO()

    call_command(
        "seed_course_video_lessons",
        "--course",
        "javascript-essentials",
        "--dry-run",
        stdout=output,
    )

    assert "Dry run only" in output.getvalue()
    assert Lesson.objects.count() == 0
    assert VideoLesson.objects.count() == 0


@pytest.mark.django_db
def test_video_lesson_seed_creates_playable_lessons_for_catalog_courses(full_stack_track):
    instructor = InstructorFactory(email="instructor@example.com")
    run_track_seed(instructor, "full-stack-developer", "--publish")
    output = io.StringIO()

    call_command(
        "seed_course_video_lessons",
        "--course",
        "javascript-essentials",
        "--confirm-production",
        stdout=output,
    )

    lesson = Lesson.objects.select_related("course").get(
        course__slug="javascript-essentials"
    )
    assert lesson.lesson_type == LessonType.VIDEO
    assert lesson.is_published is True
    assert lesson.is_free_preview is True
    assert lesson.video.transcoding_status == TranscodingStatus.COMPLETE
    assert lesson.video.hls_url.endswith(".m3u8")
    assert Course.objects.get(slug="javascript-essentials").preview_video_url.endswith(".m3u8")

    call_command(
        "seed_course_video_lessons",
        "--course",
        "javascript-essentials",
        "--confirm-production",
        stdout=io.StringIO(),
    )
    assert Lesson.objects.count() == 1
    assert VideoLesson.objects.count() == 1


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_production_guard_blocks_writes_without_confirmation(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    with pytest.raises(CommandError, match="--confirm-production"):
        run_seed(instructor, confirm=False)

    assert Course.objects.count() == 0


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_production_dry_run_allowed_without_confirmation(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    output = run_seed(instructor, "--dry-run")

    assert "Dry run only" in output
    assert Course.objects.count() == 0


@pytest.mark.django_db
def test_idempotent_rerun_creates_no_duplicate_courses_or_attachments(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    run_seed(instructor, "--publish")
    first_course_count = Course.objects.count()
    first_attachment_count = TrackCourse.objects.count()
    run_seed(instructor, "--publish")

    assert Course.objects.count() == first_course_count
    assert TrackCourse.objects.count() == first_attachment_count
    assert first_course_count == len(TRACK_ATTACHMENTS["data-analyst"])


@pytest.mark.django_db
def test_seed_creates_no_users_enrollments_or_fake_activity(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    run_seed(instructor, "--publish")

    assert User.objects.count() == 1
    assert Enrollment.objects.count() == 0


@pytest.mark.django_db
def test_instructor_validation_rejects_student(data_analyst_track):
    student = UserFactory(email="student@example.com")

    with pytest.raises(CommandError, match="Course owner must be"):
        run_seed(student)

    assert Course.objects.count() == 0


@pytest.mark.django_db
def test_default_seed_creates_draft_courses(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    run_seed(instructor)

    assert Course.objects.count() == len(TRACK_ATTACHMENTS["data-analyst"])
    assert Course.objects.filter(status=CourseStatus.DRAFT).count() == Course.objects.count()


@pytest.mark.django_db
def test_publish_seed_creates_published_courses_and_audit_logs(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    run_seed(instructor, "--publish")

    assert Course.objects.filter(status=CourseStatus.PUBLISHED).count() == Course.objects.count()
    assert AuditLog.objects.filter(action="course_seeded").count() == Course.objects.count()
    assert AuditLog.objects.filter(action="course_published").count() == Course.objects.count()
    assert (
        AuditLog.objects.filter(action="course_attached_to_track").count()
        == TrackCourse.objects.count()
    )


@pytest.mark.django_db
def test_public_track_hides_draft_courses_and_returns_published_courses(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")
    client = APIClient()

    run_seed(instructor)
    draft_response = client.get(reverse("tracks:track-detail", kwargs={"slug": "data-analyst"}))
    assert draft_response.status_code == 200
    assert draft_response.json()["data"]["total_courses"] == 0
    assert draft_response.json()["data"]["courses_by_stage"] == []

    run_seed(instructor, "--publish", "--update-existing")
    published_response = client.get(reverse("tracks:track-detail", kwargs={"slug": "data-analyst"}))
    assert published_response.status_code == 200
    assert published_response.json()["data"]["total_courses"] == len(
        TRACK_ATTACHMENTS["data-analyst"]
    )
    stages = published_response.json()["data"]["courses_by_stage"]
    returned_titles = [course["course_title"] for stage in stages for course in stage["courses"]]
    assert returned_titles[0] == "Excel for Data Analysis"
    assert "Interview Preparation for Data Analysts" in returned_titles


@pytest.mark.django_db
def test_course_ordering(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    run_seed(instructor, "--publish")

    positions = list(
        TrackCourse.objects.filter(track=data_analyst_track)
        .order_by("position")
        .values_list("position", flat=True)
    )
    assert positions == sorted(positions)
    assert positions[0] == 10


@pytest.mark.django_db
def test_manual_course_fields_preserved_without_update_existing(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")

    run_seed(instructor)
    course = Course.objects.get(slug="excel-for-data-analysis")
    course.title = "Manually Edited Excel Course"
    course.save(update_fields=["title", "updated_at"])

    run_seed(instructor, "--publish")

    course.refresh_from_db()
    assert course.title == "Manually Edited Excel Course"
    assert course.status == CourseStatus.DRAFT


@pytest.mark.django_db
def test_coverage_report_json_and_fail_on_empty(data_analyst_track):
    instructor = InstructorFactory(email="instructor@example.com")
    empty_track = CareerTrack.objects.create(
        title="Backend Developer",
        slug="backend-developer",
        short_description="Backend path",
        description="Learn backend.",
        category="tech",
        difficulty="beginner",
        position=2,
        is_active=True,
    )
    run_seed(instructor, "--publish")
    output = io.StringIO()

    call_command("career_track_coverage_report", "--track", "data-analyst", "--json", stdout=output)
    assert '"track": "data-analyst"' in output.getvalue()
    assert '"published_course_count": 12' in output.getvalue()

    with pytest.raises(CommandError, match=empty_track.slug):
        call_command("career_track_coverage_report", "--fail-on-empty")
