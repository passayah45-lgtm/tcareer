import pytest

from apps.courses.models import (
    AcademicOverrideReason,
    ContentReviewStatus,
    MalwareScanStatus,
    ResourceLibraryItem,
    ResourceVisibility,
    ReviewerRole,
    ReviewPriority,
    ReviewTargetType,
)
from apps.courses.services import (
    AcademicOverrideService,
    AcademicReviewAssignmentService,
    AcademicReviewService,
    CourseService,
    MalwareScanService,
    ResourceLibraryService,
)
from apps.courses.tests.factories import CourseFactory, LessonFactory
from apps.users.tests.factories import AdminFactory, InstructorFactory, UserFactory
from common.exceptions import ConflictError, PermissionError, ServiceError


@pytest.mark.django_db
def test_reviewer_assignment_blocks_instructor_self_assignment():
    course = CourseFactory()
    lead = UserFactory()
    AcademicReviewAssignmentService.ensure_reviewer_profile(
        lead,
        role=ReviewerRole.LEAD_REVIEWER,
    )

    with pytest.raises(PermissionError):
        AcademicReviewAssignmentService.assign(
            assigner=lead,
            reviewer=course.instructor,
            target_type=ReviewTargetType.COURSE,
            target_id=course.id,
            priority=ReviewPriority.HIGH,
        )


@pytest.mark.django_db
def test_assigned_reviewer_can_approve_course_but_instructor_cannot_self_approve():
    course = CourseFactory()
    reviewer = UserFactory()
    lead = UserFactory()
    AcademicReviewAssignmentService.ensure_reviewer_profile(
        lead,
        role=ReviewerRole.LEAD_REVIEWER,
    )
    AcademicReviewAssignmentService.ensure_reviewer_profile(
        reviewer,
        role=ReviewerRole.COURSE_REVIEWER,
    )
    AcademicReviewAssignmentService.assign(
        assigner=lead,
        reviewer=reviewer,
        target_type=ReviewTargetType.COURSE,
        target_id=course.id,
    )

    with pytest.raises(PermissionError):
        AcademicReviewService.review_course(
            course,
            course.instructor,
            status=ContentReviewStatus.APPROVED,
        )

    review = AcademicReviewService.review_course(
        course,
        reviewer,
        status=ContentReviewStatus.APPROVED,
        comments="Ready",
    )
    assert review.status == ContentReviewStatus.APPROVED


@pytest.mark.django_db
def test_resource_upload_rejects_executable_extension():
    with pytest.raises(ServiceError):
        ResourceLibraryService.validate_resource_metadata(
            file_name="malware.exe",
            content_type="application/octet-stream",
            file_size=100,
        )


@pytest.mark.django_db
def test_private_resource_download_requires_owner_or_reviewer():
    owner = InstructorFactory()
    stranger = UserFactory()
    resource = ResourceLibraryItem.objects.create(
        owner=owner,
        title="Private workbook",
        resource_type="excel",
        file_url="https://cdn.example.test/private.xlsx",
        visibility=ResourceVisibility.PRIVATE,
        review_status=ContentReviewStatus.APPROVED,
    )

    with pytest.raises(PermissionError):
        ResourceLibraryService.download(resource, stranger)

    url = ResourceLibraryService.download(resource, owner)
    resource.refresh_from_db()
    assert url.endswith("private.xlsx")
    assert resource.download_count == 1


@pytest.mark.django_db
def test_publish_blockers_include_unapproved_resources():
    course = CourseFactory()
    LessonFactory(
        course=course,
        is_published=True,
        review_status=ContentReviewStatus.PUBLISHED,
        published_version=1,
        content="Approved content",
    )
    ResourceLibraryItem.objects.create(
        owner=course.instructor,
        course=course,
        title="Needs review",
        resource_type="pdf",
        file_url="https://cdn.example.test/resource.pdf",
        visibility=ResourceVisibility.COURSE,
        review_status=ContentReviewStatus.NEEDS_REVIEW,
    )

    codes = {item["code"] for item in CourseService.publish_blockers(course)}
    assert "resource_review_unresolved" in codes


@pytest.mark.django_db
def test_assignment_respects_subject_scope_and_workload_limit():
    course = CourseFactory()
    lead = UserFactory()
    reviewer = UserFactory()
    AcademicReviewAssignmentService.ensure_reviewer_profile(
        lead,
        role=ReviewerRole.LEAD_REVIEWER,
    )
    profile = AcademicReviewAssignmentService.ensure_reviewer_profile(
        reviewer,
        role=ReviewerRole.SUBJECT_REVIEWER,
        subject_tags=["excel"],
    )
    profile.max_active_assignments = 1
    profile.save(update_fields=["max_active_assignments"])

    with pytest.raises(PermissionError):
        AcademicReviewAssignmentService.assign(
            assigner=lead,
            reviewer=reviewer,
            target_type=ReviewTargetType.COURSE,
            target_id=course.id,
            subject="python",
        )

    AcademicReviewAssignmentService.assign(
        assigner=lead,
        reviewer=reviewer,
        target_type=ReviewTargetType.COURSE,
        target_id=course.id,
        subject="excel",
    )

    lesson = LessonFactory(course=course)
    with pytest.raises(ConflictError):
        AcademicReviewAssignmentService.assign(
            assigner=lead,
            reviewer=reviewer,
            target_type=ReviewTargetType.LESSON,
            target_id=lesson.id,
            subject="excel",
        )


@pytest.mark.django_db
def test_mock_malware_scan_blocks_infected_resource_approval_and_download(settings):
    settings.ACADEMIC_MALWARE_SCANNER = "mock"
    course = CourseFactory()
    reviewer = UserFactory()
    AcademicReviewAssignmentService.ensure_reviewer_profile(
        reviewer,
        role=ReviewerRole.COURSE_REVIEWER,
    )
    resource = ResourceLibraryItem.objects.create(
        owner=course.instructor,
        course=course,
        title="Dataset",
        resource_type="excel",
        file_url="https://cdn.example.test/dataset.xlsx",
        file_name="dataset-eicar.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_size_bytes=100,
        visibility=ResourceVisibility.COURSE,
        review_status=ContentReviewStatus.NEEDS_REVIEW,
        malware_scan_status=MalwareScanStatus.PENDING,
        malware_scanner="mock",
        metadata={"malware_scan_required": True},
    )

    MalwareScanService.scan_resource(resource, actor=reviewer, provider="mock")
    resource.refresh_from_db()

    assert resource.malware_scan_status == MalwareScanStatus.INFECTED
    with pytest.raises(ServiceError):
        ResourceLibraryService.review(
            resource,
            reviewer,
            status=ContentReviewStatus.APPROVED,
        )
    with pytest.raises(PermissionError):
        ResourceLibraryService.download(resource, reviewer)


@pytest.mark.django_db
def test_clean_scan_allows_resource_approval_and_publish_gate_progress(settings):
    settings.ACADEMIC_MALWARE_SCANNER = "mock"
    course = CourseFactory()
    reviewer = UserFactory()
    AcademicReviewAssignmentService.ensure_reviewer_profile(
        reviewer,
        role=ReviewerRole.COURSE_REVIEWER,
    )
    resource = ResourceLibraryItem.objects.create(
        owner=course.instructor,
        course=course,
        title="Clean Dataset",
        resource_type="excel",
        file_url="https://cdn.example.test/dataset.xlsx",
        file_name="dataset.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_size_bytes=100,
        visibility=ResourceVisibility.COURSE,
        review_status=ContentReviewStatus.NEEDS_REVIEW,
        malware_scan_status=MalwareScanStatus.PENDING,
        malware_scanner="mock",
        metadata={"malware_scan_required": True},
    )

    MalwareScanService.scan_resource(resource, actor=reviewer, provider="mock")
    resource.refresh_from_db()
    assert resource.malware_scan_status == MalwareScanStatus.CLEAN

    ResourceLibraryService.review(resource, reviewer, status=ContentReviewStatus.APPROVED)
    resource.refresh_from_db()
    assert resource.review_status == ContentReviewStatus.APPROVED


@pytest.mark.django_db
def test_publish_blockers_include_approved_resource_with_pending_scan():
    course = CourseFactory()
    ResourceLibraryItem.objects.create(
        owner=course.instructor,
        course=course,
        title="Approved but unscanned",
        resource_type="excel",
        file_url="https://cdn.example.test/dataset.xlsx",
        visibility=ResourceVisibility.COURSE,
        review_status=ContentReviewStatus.APPROVED,
        malware_scan_status=MalwareScanStatus.PENDING,
    )

    codes = {item["code"] for item in CourseService.publish_blockers(course)}
    assert "resource_scan_not_clean" in codes


@pytest.mark.django_db
def test_academic_override_requires_admin_and_records_audit():
    course = CourseFactory()
    admin = AdminFactory()
    reviewer = UserFactory()

    with pytest.raises(PermissionError):
        AcademicOverrideService.record_override(
            actor=reviewer,
            target=course,
            reason_code=AcademicOverrideReason.STUCK_STATE,
            reason="Repair stuck state",
            previous_state={"status": "under_review"},
            new_state={"status": "needs_review"},
        )

    log = AcademicOverrideService.record_override(
        actor=admin,
        target=course,
        reason_code=AcademicOverrideReason.STUCK_STATE,
        reason="Repair verified stuck academic state",
        previous_state={"status": "under_review"},
        new_state={"status": "needs_review"},
    )

    assert log.reason_code == AcademicOverrideReason.STUCK_STATE
