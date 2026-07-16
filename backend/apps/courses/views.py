import csv
import logging

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.exceptions import PermissionError
from common.pagination import StandardPagination
from common.permission_service import PermissionService
from common.permissions import IsInstructor
from common.webhooks import WebhookSecurityService

from .models import (
    Course,
    CourseProject,
    Enrollment,
    Lesson,
    LessonProgress,
    LessonVersion,
    ResourceLibraryItem,
    ReviewAssignment,
)
from .serializers import (
    AcademicReviewerProfileSerializer,
    CourseCreateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseProjectReviewDecisionSerializer,
    CourseProjectReviewSerializer,
    CourseProjectSerializer,
    CourseReviewSerializer,
    CourseUpdateSerializer,
    EnrollmentSerializer,
    InstructorAnalyticsSerializer,
    InstructorReviewResponseSerializer,
    LessonCreateSerializer,
    LessonProgressSerializer,
    LessonReviewActionSerializer,
    LessonSerializer,
    LessonStructuredReviewSerializer,
    LessonVersionCompareSerializer,
    LessonVersionCreateSerializer,
    LessonVersionSerializer,
    PublishBlockerSerializer,
    QualityDashboardSerializer,
    ResourceLibraryItemSerializer,
    ResourceReviewActionSerializer,
    ResourceScanActionSerializer,
    ResourceUploadRequestSerializer,
    ReviewActionSerializer,
    ReviewAssignmentCreateSerializer,
    ReviewAssignmentSerializer,
    ReviewReassignSerializer,
    StructuredLessonReviewActionSerializer,
    StructuredProjectReviewActionSerializer,
    SubmitCourseReviewSerializer,
    UpdateProgressSerializer,
    UploadUrlRequestSerializer,
)
from .services import (
    AcademicReviewAssignmentService,
    AcademicReviewService,
    CourseProjectService,
    CourseQualityService,
    CourseService,
    EnrollmentService,
    InstructorAnalyticsService,
    LessonService,
    LessonVersionService,
    MalwareScanService,
    ProgressService,
    ResourceLibraryService,
)

logger = logging.getLogger(__name__)


ACADEMIC_AUDIT_ACTIONS = [
    "academic_review_assigned",
    "academic_review_reassigned",
    "course_submitted_for_review",
    "course_review_status_changed",
    "lesson_review_status_changed",
    "structured_lesson_review_completed",
    "course_project_reviewed",
    "course_project_review_reopened",
    "academic_resource_upload_requested",
    "academic_resource_reviewed",
    "academic_resource_malware_scanned",
    "academic_resource_downloaded",
    "academic_resource_download_blocked",
    "academic_instructor_response",
    "course_publication_blocked",
    "academic_review_escalated",
    "academic_override_recorded",
    "quiz_question_approved",
    "quiz_question_structured_reviewed",
    "lesson_version_rollback",
]


@api_view(["GET"])
@permission_classes([AllowAny])
def course_list(request):
    filters = {
        "level": request.query_params.get("level"),
        "search": request.query_params.get("search"),
        "is_free": request.query_params.get("is_free") == "true",
    }
    queryset = CourseService.get_published_courses(filters)
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = CourseListSerializer(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, status="published", deleted_at=None)
    serializer = CourseDetailSerializer(course, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def course_create(request):
    serializer = CourseCreateSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    course = serializer.save()
    return Response(
        CourseDetailSerializer(course, context={"request": request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsInstructor])
def course_update(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    serializer = CourseUpdateSerializer(course, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    course = serializer.save()
    return Response(CourseDetailSerializer(course, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def course_publish(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    course = CourseService.publish_course(course, request.user)
    return Response(CourseDetailSerializer(course, context={"request": request}).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsInstructor])
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    CourseService.soft_delete_course(course, request.user)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInstructor])
def instructor_courses(request):
    courses = CourseService.get_instructor_courses(request.user)
    paginator = StandardPagination()
    page = paginator.paginate_queryset(courses, request)
    serializer = CourseListSerializer(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def author_analytics(request):
    data = InstructorAnalyticsService.summary(request.user)
    return Response(InstructorAnalyticsSerializer(data).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def content_quality_dashboard(request):
    data = CourseQualityService.dashboard(request.user)
    return Response(QualityDashboardSerializer(data).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reviewer_dashboard(request):
    if not PermissionService.is_academic_reviewer(request.user):
        raise PermissionError("You are not an academic reviewer.")
    return Response(
        {
            "metrics": AcademicReviewAssignmentService.metrics(request.user),
            "profile": AcademicReviewerProfileSerializer(
                getattr(request.user, "academic_reviewer_profile", None)
            ).data
            if hasattr(request.user, "academic_reviewer_profile")
            else None,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def academic_audit(request):
    if not PermissionService.is_academic_admin(request.user):
        raise PermissionError("You cannot view academic audit logs.")
    from apps.audit.models import AuditLog

    qs = AuditLog.objects.select_related("actor").filter(action__in=ACADEMIC_AUDIT_ACTIONS)
    if request.query_params.get("action"):
        qs = qs.filter(action=request.query_params["action"])
    if request.query_params.get("actor"):
        qs = qs.filter(actor_id=request.query_params["actor"])
    if request.query_params.get("target_type"):
        qs = qs.filter(target_type=request.query_params["target_type"])
    if request.query_params.get("status"):
        qs = qs.filter(metadata__status=request.query_params["status"])
    qs = qs.order_by("-timestamp")

    if request.query_params.get("format") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="academic-audit.csv"'
        writer = csv.writer(response)
        writer.writerow(["timestamp", "actor", "action", "target_type", "target_id", "metadata"])
        for row in qs[:1000]:
            writer.writerow(
                [
                    row.timestamp.isoformat(),
                    getattr(row.actor, "email", ""),
                    row.action,
                    row.target_type,
                    row.target_id,
                    row.metadata,
                ]
            )
        return response

    paginator = StandardPagination()
    page = paginator.paginate_queryset(qs, request)
    data = [
        {
            "id": str(row.id),
            "timestamp": row.timestamp,
            "actor_email": getattr(row.actor, "email", ""),
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "metadata": row.metadata,
        }
        for row in page
    ]
    return paginator.get_paginated_response(data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def reviewer_queue(request):
    if request.method == "GET":
        if not PermissionService.is_academic_reviewer(request.user):
            raise PermissionError("You are not an academic reviewer.")
        assignments = AcademicReviewAssignmentService.queue_for(request.user, request.query_params)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(assignments, request)
        serializer = ReviewAssignmentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = ReviewAssignmentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reviewer = get_object_or_404(
        get_user_model(),
        id=serializer.validated_data["reviewer_id"],
        is_active=True,
    )
    assignment = AcademicReviewAssignmentService.assign(
        assigner=request.user,
        reviewer=reviewer,
        target_type=serializer.validated_data["target_type"],
        target_id=serializer.validated_data["target_id"],
        due_date=serializer.validated_data.get("due_date"),
        priority=serializer.validated_data.get("priority"),
        subject=serializer.validated_data.get("subject", ""),
    )
    return Response(ReviewAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reviewer_assignment_reassign(request, assignment_id):
    assignment = get_object_or_404(
        ReviewAssignment.objects.select_related("course"), id=assignment_id
    )
    serializer = ReviewReassignSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reviewer = get_object_or_404(
        get_user_model(),
        id=serializer.validated_data["reviewer_id"],
        is_active=True,
    )
    assignment = AcademicReviewAssignmentService.reassign(
        assignment,
        assigner=request.user,
        reviewer=reviewer,
        reason=serializer.validated_data.get("reason", ""),
    )
    return Response(ReviewAssignmentSerializer(assignment).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reviewer_assignment_response(request, assignment_id):
    assignment = get_object_or_404(
        ReviewAssignment.objects.select_related("course", "assigned_reviewer"), id=assignment_id
    )
    serializer = InstructorReviewResponseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    assignment = AcademicReviewService.instructor_response(
        assignment,
        request.user,
        response=serializer.validated_data["response"],
        addressed=serializer.validated_data.get("addressed", False),
    )
    return Response(ReviewAssignmentSerializer(assignment).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_quality(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    return Response(CourseQualityService.readiness(course))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_publish_blockers(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    if not PermissionService.can_publish_course(
        request.user, course
    ) and not PermissionService.is_academic_reviewer(request.user):
        raise PermissionError("You cannot view publication blockers for this course.")
    blockers = CourseService.publish_blockers(course)
    return Response(
        PublishBlockerSerializer({"blockers": blockers, "publish_ready": not blockers}).data
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_reviews(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    if not PermissionService.can_publish_course(
        request.user, course
    ) and not PermissionService.is_platform_admin(request.user):
        raise PermissionError("You cannot view reviews for this course.")
    reviews = course.academic_reviews.select_related("reviewer", "submitted_by").order_by(
        "-created_at"
    )
    return Response(CourseReviewSerializer(reviews, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_course_review(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    serializer = SubmitCourseReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    review = AcademicReviewService.submit_course(
        course,
        request.user,
        comments=serializer.validated_data.get("comments", ""),
    )
    return Response(CourseReviewSerializer(review).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_course(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    serializer = ReviewActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    review = AcademicReviewService.review_course(
        course,
        request.user,
        status=serializer.validated_data["status"],
        comments=serializer.validated_data.get("comments", ""),
        required_fixes=serializer.validated_data.get("required_fixes", []),
    )
    return Response(CourseReviewSerializer(review).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def course_project(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    if request.method == "GET":
        project = CourseProject.objects.filter(course=course).select_related("reviewed_by").first()
        if not project:
            return Response({"detail": "Project not configured."}, status=status.HTTP_404_NOT_FOUND)
        if not PermissionService.can_publish_course(
            request.user, course
        ) and not PermissionService.is_platform_admin(request.user):
            raise PermissionError("You cannot view this course project.")
        return Response(CourseProjectSerializer(project).data)

    serializer = CourseProjectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    project = CourseProjectService.upsert(course, request.user, serializer.validated_data)
    return Response(CourseProjectSerializer(project).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_course_project(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    project = get_object_or_404(CourseProject, course=course)
    serializer = CourseProjectReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    project = CourseProjectService.review(
        project,
        request.user,
        status=serializer.validated_data["status"],
        notes=serializer.validated_data.get("notes", ""),
    )
    return Response(CourseProjectSerializer(project).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def structured_course_project_review(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    project = get_object_or_404(CourseProject, course=course)
    serializer = StructuredProjectReviewActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    decision = CourseProjectService.structured_review(
        project,
        request.user,
        decision=serializer.validated_data["decision"],
        review_sections=serializer.validated_data.get("review_sections", {}),
        required_changes=serializer.validated_data.get("required_changes", []),
        notes=serializer.validated_data.get("notes", ""),
    )
    return Response(
        CourseProjectReviewDecisionSerializer(decision).data, status=status.HTTP_201_CREATED
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def resource_library(request):
    if request.method == "GET":
        resources = ResourceLibraryService.list_for_user(request.user).order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(resources, request)
        serializer = ResourceLibraryItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = ResourceLibraryItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    resource = ResourceLibraryService.create(request.user, serializer.validated_data)
    return Response(ResourceLibraryItemSerializer(resource).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resource_upload_url(request):
    serializer = ResourceUploadRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = None
    if serializer.validated_data.get("course_id"):
        course = get_object_or_404(
            Course, id=serializer.validated_data["course_id"], deleted_at=None
        )
    result = ResourceLibraryService.request_upload(
        request.user,
        course=course,
        file_name=serializer.validated_data["file_name"],
        content_type=serializer.validated_data["content_type"],
        file_size=serializer.validated_data["file_size"],
        checksum=serializer.validated_data.get("checksum", ""),
        visibility=serializer.validated_data.get("visibility", "private"),
    )
    return Response(
        {
            "resource": ResourceLibraryItemSerializer(result["resource"]).data,
            "upload": result["upload"],
            "malware_scan_required": result["malware_scan_required"],
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resource_review(request, resource_id):
    resource = get_object_or_404(
        ResourceLibraryItem.objects.select_related("course", "owner"), id=resource_id
    )
    serializer = ResourceReviewActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    resource = ResourceLibraryService.review(
        resource,
        request.user,
        status=serializer.validated_data["status"],
        notes=serializer.validated_data.get("notes", ""),
    )
    return Response(ResourceLibraryItemSerializer(resource).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resource_scan(request, resource_id):
    resource = get_object_or_404(
        ResourceLibraryItem.objects.select_related("course", "owner"), id=resource_id
    )
    if not PermissionService.is_academic_reviewer(request.user):
        raise PermissionError("You cannot scan this resource.")
    serializer = ResourceScanActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    resource = MalwareScanService.scan_resource(
        resource,
        actor=request.user,
        provider=serializer.validated_data.get("provider"),
        sample_text=serializer.validated_data.get("sample_text", ""),
    )
    return Response(ResourceLibraryItemSerializer(resource).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resource_download(request, resource_id):
    resource = get_object_or_404(
        ResourceLibraryItem.objects.select_related("course", "owner"), id=resource_id
    )
    url = ResourceLibraryService.download(resource, request.user)
    return Response({"download_url": url})


@api_view(["GET"])
@permission_classes([AllowAny])
def lesson_list(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    lessons = course.lessons.filter(deleted_at=None)
    can_manage_course = request.user.is_authenticated and PermissionService.can_publish_course(
        request.user, course
    )
    if not can_manage_course:
        lessons = lessons.filter(is_published=True)
    serializer = LessonSerializer(lessons, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def lesson_detail(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course, deleted_at=None)
    if not PermissionService.can_access_lesson(request.user, lesson):
        raise PermissionError("Enroll in this course to access this lesson.")
    serializer = LessonSerializer(lesson, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_create(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    serializer = LessonCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    lesson = serializer.save(course=course)
    return Response(
        LessonSerializer(lesson, context={"request": request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_update(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course, deleted_at=None)
    serializer = LessonCreateSerializer(lesson, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    lesson = serializer.save()
    return Response(LessonSerializer(lesson, context={"request": request}).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def lesson_versions(request, course_id, lesson_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"), id=lesson_id, course=course, deleted_at=None
    )
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")

    if request.method == "GET":
        versions = lesson.versions.select_related("editor").order_by("-version_number")
        return Response(LessonVersionSerializer(versions, many=True).data)

    serializer = LessonVersionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    version = LessonVersionService.capture(
        lesson,
        request.user,
        summary=serializer.validated_data.get("summary_of_changes", ""),
    )
    return Response(LessonVersionSerializer(version).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def lesson_version_rollback(request, course_id, lesson_id, version_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"), id=lesson_id, course=course, deleted_at=None
    )
    version = get_object_or_404(LessonVersion, id=version_id, lesson=lesson)
    lesson = LessonVersionService.rollback(lesson, version, request.user)
    return Response(LessonSerializer(lesson, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def lesson_version_compare(request, course_id, lesson_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"), id=lesson_id, course=course, deleted_at=None
    )
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    serializer = LessonVersionCompareSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    left = get_object_or_404(
        LessonVersion, id=serializer.validated_data["left_version_id"], lesson=lesson
    )
    right = get_object_or_404(
        LessonVersion, id=serializer.validated_data["right_version_id"], lesson=lesson
    )
    return Response(LessonVersionService.compare(lesson, left, right))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def lesson_review(request, course_id, lesson_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"), id=lesson_id, course=course, deleted_at=None
    )
    serializer = LessonReviewActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    lesson = AcademicReviewService.review_lesson(
        lesson,
        request.user,
        status=serializer.validated_data["status"],
        comments=serializer.validated_data.get("comments", ""),
    )
    return Response(LessonSerializer(lesson, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def structured_lesson_review(request, course_id, lesson_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, deleted_at=None
    )
    lesson = get_object_or_404(
        Lesson.objects.select_related("course"), id=lesson_id, course=course, deleted_at=None
    )
    serializer = StructuredLessonReviewActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    review = AcademicReviewService.structured_lesson_review(
        lesson,
        request.user,
        decision=serializer.validated_data["decision"],
        section_comments=serializer.validated_data.get("section_comments", {}),
        required_changes=serializer.validated_data.get("required_changes", []),
    )
    return Response(LessonStructuredReviewSerializer(review).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_upload_url(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    serializer = UploadUrlRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = LessonService.get_upload_url(
        lesson=lesson,
        file_name=serializer.validated_data["file_name"],
        content_type=serializer.validated_data.get("content_type", "video/mp4"),
    )
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_confirm_upload(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    s3_key = request.data.get("s3_key", "")
    file_size_bytes = request.data.get("file_size_bytes", 0)
    if not s3_key:
        return Response({"detail": "s3_key is required."}, status=status.HTTP_400_BAD_REQUEST)
    video_lesson = LessonService.confirm_upload(lesson, s3_key, file_size_bytes)
    return Response(
        {
            "id": str(video_lesson.id),
            "transcoding_status": video_lesson.transcoding_status,
            "message": "Transcoding job started. The video will be ready in a few minutes.",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    enrollment = EnrollmentService.enroll(request.user, course)
    return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_enrollments(request):
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .select_related("course", "course__instructor")
        .order_by("-created_at")
    )
    paginator = StandardPagination()
    page = paginator.paginate_queryset(enrollments, request)
    serializer = EnrollmentSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_progress(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    enrollment = EnrollmentService.get_enrollment(request.user, course)
    serializer = UpdateProgressSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    progress = ProgressService.update_progress(
        enrollment=enrollment,
        lesson=lesson,
        watch_percentage=serializer.validated_data["watch_percentage"],
        last_position_seconds=serializer.validated_data.get("last_position_seconds", 0),
    )
    return Response(LessonProgressSerializer(progress).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_text_lesson(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    enrollment = EnrollmentService.get_enrollment(request.user, course)
    progress = ProgressService.mark_text_lesson_complete(enrollment, lesson)
    return Response(LessonProgressSerializer(progress).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_progress(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    enrollment = EnrollmentService.get_enrollment(request.user, course)
    summary = ProgressService.get_course_progress(enrollment)
    lesson_progress = LessonProgress.objects.filter(enrollment=enrollment).select_related("lesson")
    summary["lessons"] = LessonProgressSerializer(lesson_progress, many=True).data
    return Response(summary)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_reorder(request, course_id):
    from .serializers import LessonReorderSerializer
    from .services import LessonReorderService

    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError("You do not own this course.")
    serializer = LessonReorderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    lessons = LessonReorderService.reorder(
        course=course,
        reorder_data=serializer.validated_data["lessons"],
        instructor=request.user,
    )
    return Response(LessonSerializer(lessons, many=True, context={"request": request}).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_inline_update(request, lesson_id):
    from .serializers import LessonInlineUpdateSerializer
    from .services import LessonInlineUpdateService

    lesson = get_object_or_404(
        Lesson.objects.select_related("course", "course__instructor"),
        id=lesson_id,
        deleted_at=None,
    )
    if not PermissionService.can_publish_course(request.user, lesson.course):
        raise PermissionError("You do not own this lesson.")
    serializer = LessonInlineUpdateSerializer(lesson, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    lesson = LessonInlineUpdateService.update(
        lesson=lesson,
        data=serializer.validated_data,
        instructor=request.user,
    )
    return Response(LessonSerializer(lesson, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def mediaconvert_webhook_v2(request):
    from django.conf import settings

    from apps.courses.models import TranscodingStatus, VideoLesson

    try:
        WebhookSecurityService.verify_static_secret(
            request,
            setting_name="MEDIACONVERT_WEBHOOK_SECRET",
        )
    except Exception:
        logger.warning(
            "MediaConvert webhook: invalid secret from %s", request.META.get("REMOTE_ADDR")
        )
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    event_type = request.data.get("detail-type", "")
    if event_type != "MediaConvert Job State Change":
        return Response(status=status.HTTP_200_OK)

    detail = request.data.get("detail", {})
    job_status = detail.get("status", "")
    job_id = detail.get("jobId", "")
    user_metadata = detail.get("userMetadata", {})

    logger.info("MediaConvert webhook: job %s status=%s", job_id, job_status)

    if job_status == "COMPLETE":
        output_groups = detail.get("outputGroupDetails", [])
        hls_url = ""
        thumbnail_url = ""

        for group in output_groups:
            for output_detail in group.get("outputDetails", []):
                output_uri = output_detail.get("outputFilePaths", [""])[0]
                if output_uri.endswith("master.m3u8"):
                    bucket = settings.AWS_S3_BUCKET_NAME
                    if getattr(settings, "AWS_S3_CUSTOM_DOMAIN", ""):
                        hls_url = output_uri.replace(
                            f"s3://{bucket}/", f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/"
                        )
                    else:
                        hls_url = output_uri.replace(
                            "s3://", f"https://s3.{settings.AWS_REGION}.amazonaws.com/"
                        )
                if output_uri.endswith(".jpg"):
                    hls_url_temp = output_uri.replace("s3://", "https://s3.amazonaws.com/")
                    thumbnail_url = hls_url_temp

        try:
            video_lesson = VideoLesson.objects.get(mediaconvert_job_id=job_id)
            if video_lesson.transcoding_status == TranscodingStatus.COMPLETE:
                return Response(status=status.HTTP_200_OK)
            video_lesson.transcoding_status = TranscodingStatus.COMPLETE
            video_lesson.hls_url = hls_url
            if thumbnail_url:
                video_lesson.thumbnail_url = thumbnail_url
            video_lesson.save(
                update_fields=["transcoding_status", "hls_url", "thumbnail_url", "updated_at"]
            )
            logger.info("VideoLesson %s marked complete. HLS: %s", video_lesson.id, hls_url)
        except VideoLesson.DoesNotExist:
            logger.warning("No VideoLesson for job %s metadata=%s", job_id, user_metadata)
        except Exception as exc:
            logger.error("Webhook COMPLETE error for job %s: %s", job_id, exc)

    elif job_status == "ERROR":
        error_code = detail.get("errorCode", "")
        error_message = detail.get("errorMessage", "")
        logger.error("MediaConvert job %s FAILED: %s - %s", job_id, error_code, error_message)
        try:
            video_lesson = VideoLesson.objects.get(mediaconvert_job_id=job_id)
            video_lesson.transcoding_status = TranscodingStatus.FAILED
            video_lesson.save(update_fields=["transcoding_status", "updated_at"])
        except VideoLesson.DoesNotExist:
            pass

    return Response(status=status.HTTP_200_OK)
