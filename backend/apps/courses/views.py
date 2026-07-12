import logging
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from common.exceptions import PermissionError
from common.pagination import StandardPagination
from common.permissions import IsInstructor
from common.permission_service import PermissionService
from common.webhooks import WebhookSecurityService
from .models import Course, Lesson, Enrollment, LessonProgress
from .serializers import (
    CourseListSerializer, CourseDetailSerializer,
    CourseCreateSerializer, CourseUpdateSerializer,
    LessonSerializer, LessonCreateSerializer,
    EnrollmentSerializer, LessonProgressSerializer,
    UpdateProgressSerializer, UploadUrlRequestSerializer,
)
from .services import CourseService, LessonService, EnrollmentService, ProgressService

logger = logging.getLogger(__name__)


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
@permission_classes([AllowAny])
def lesson_list(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    lessons = course.lessons.filter(deleted_at=None)
    can_manage_course = (
        request.user.is_authenticated
        and PermissionService.can_publish_course(request.user, course)
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
    return Response({
        "id": str(video_lesson.id),
        "transcoding_status": video_lesson.transcoding_status,
        "message": "Transcoding job started. The video will be ready in a few minutes.",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    enrollment = EnrollmentService.enroll(request.user, course)
    return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_enrollments(request):
    enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related("course", "course__instructor").order_by("-created_at")
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
    lesson_progress = LessonProgress.objects.filter(
        enrollment=enrollment
    ).select_related("lesson")
    summary["lessons"] = LessonProgressSerializer(lesson_progress, many=True).data
    return Response(summary)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_reorder(request, course_id):
    from .serializers import LessonReorderSerializer
    from .services import LessonReorderService
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    if not PermissionService.can_publish_course(request.user, course):
        raise PermissionError('You do not own this course.')
    serializer = LessonReorderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    lessons = LessonReorderService.reorder(
        course=course,
        reorder_data=serializer.validated_data['lessons'],
        instructor=request.user,
    )
    return Response(LessonSerializer(lessons, many=True, context={'request': request}).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsInstructor])
def lesson_inline_update(request, lesson_id):
    from .serializers import LessonInlineUpdateSerializer
    from .services import LessonInlineUpdateService
    lesson = get_object_or_404(
        Lesson.objects.select_related('course', 'course__instructor'),
        id=lesson_id,
        deleted_at=None,
    )
    if not PermissionService.can_publish_course(request.user, lesson.course):
        raise PermissionError('You do not own this lesson.')
    serializer = LessonInlineUpdateSerializer(lesson, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    lesson = LessonInlineUpdateService.update(
        lesson=lesson,
        data=serializer.validated_data,
        instructor=request.user,
    )
    return Response(LessonSerializer(lesson, context={'request': request}).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def mediaconvert_webhook_v2(request):
    from django.conf import settings
    from apps.courses.models import VideoLesson, TranscodingStatus

    try:
        WebhookSecurityService.verify_static_secret(
            request,
            setting_name="MEDIACONVERT_WEBHOOK_SECRET",
        )
    except Exception:
        logger.warning("MediaConvert webhook: invalid secret from %s", request.META.get("REMOTE_ADDR"))
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
                        hls_url = output_uri.replace(f"s3://{bucket}/", f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/")
                    else:
                        hls_url = output_uri.replace("s3://", f"https://s3.{settings.AWS_REGION}.amazonaws.com/")
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
            video_lesson.save(update_fields=["transcoding_status", "hls_url", "thumbnail_url", "updated_at"])
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
