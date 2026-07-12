import logging
from django.db import transaction
from django.utils import timezone

from common.exceptions import ServiceError, ConflictError, NotFoundError, PermissionError
from common.audit import AuditService
from common.entitlements import EntitlementService
from common.storage import generate_presigned_upload_url
from apps.analytics.services import AnalyticsService
from .models import (
    Course, Lesson, VideoLesson, Enrollment, LessonProgress,
    CourseStatus, EnrollmentStatus, TranscodingStatus,
)

logger = logging.getLogger(__name__)

VIDEO_COMPLETION_THRESHOLD = 90  # percent


class CourseService:

    @staticmethod
    def get_published_courses(filters=None):
        qs = Course.objects.filter(
            status=CourseStatus.PUBLISHED,
            deleted_at=None,
        ).select_related("instructor")
        if filters:
            if filters.get("level"):
                qs = qs.filter(level=filters["level"])
            if filters.get("search"):
                qs = qs.filter(title__icontains=filters["search"])
            if filters.get("is_free"):
                qs = qs.filter(price=0)
        return qs

    @staticmethod
    def get_instructor_courses(instructor):
        return Course.objects.filter(
            instructor=instructor,
            deleted_at=None,
        ).order_by("-created_at")

    @staticmethod
    def publish_course(course, instructor):
        if course.instructor != instructor:
            raise PermissionError("You do not own this course.")
        if not course.lessons.filter(is_published=True, deleted_at=None).exists():
            raise ServiceError("Publish at least one lesson before publishing the course.")
        course.status = CourseStatus.PUBLISHED
        course.save(update_fields=["status", "updated_at"])
        AuditService.record(
            actor=instructor,
            action="course_publish",
            target=course,
            metadata={"course_title": course.title},
        )
        logger.info("Course published: %s by %s", course.title, instructor.email)
        return course

    @staticmethod
    def soft_delete_course(course, instructor):
        if course.instructor != instructor:
            raise PermissionError("You do not own this course.")
        course.deleted_at = timezone.now()
        course.status = CourseStatus.ARCHIVED
        course.save(update_fields=["deleted_at", "status", "updated_at"])
        logger.info("Course soft-deleted: %s", course.id)


class LessonService:

    @staticmethod
    def get_upload_url(lesson, file_name, content_type="video/mp4"):
        """
        Generate a presigned S3 URL for direct browser-to-S3 video upload.
        The browser uploads directly. Django never receives the video bytes.
        """
        folder = f"courses/{lesson.course.id}/lessons/{lesson.id}/original"
        result = generate_presigned_upload_url(
            file_name=file_name,
            folder=folder,
            content_type=content_type,
            expiry_seconds=3600,
        )

        video_lesson, _ = VideoLesson.objects.get_or_create(
            lesson=lesson,
            defaults={
                "original_s3_key": result["key"],
                "transcoding_status": TranscodingStatus.PENDING,
            },
        )
        if video_lesson.original_s3_key != result["key"]:
            video_lesson.original_s3_key = result["key"]
            video_lesson.transcoding_status = TranscodingStatus.PENDING
            video_lesson.save(update_fields=["original_s3_key", "transcoding_status"])

        return result

    @staticmethod
    def confirm_upload(lesson, s3_key, file_size_bytes=0):
        """
        Called after the browser confirms the S3 upload completed.
        Triggers the MediaConvert transcoding job via Celery.
        """
        try:
            video_lesson = lesson.video
        except VideoLesson.DoesNotExist:
            video_lesson = VideoLesson.objects.create(
                lesson=lesson,
                original_s3_key=s3_key,
            )

        video_lesson.original_s3_key = s3_key
        video_lesson.file_size_bytes = file_size_bytes
        video_lesson.transcoding_status = TranscodingStatus.PROCESSING
        video_lesson.save(update_fields=[
            "original_s3_key", "file_size_bytes", "transcoding_status"
        ])

        from tasks.video import trigger_transcoding
        trigger_transcoding.delay(
            s3_key=s3_key,
            lesson_id=str(lesson.id),
            video_lesson_id=str(video_lesson.id),
        )

        logger.info("Transcoding triggered for lesson %s", lesson.id)
        return video_lesson

    @staticmethod
    def handle_transcoding_complete(video_lesson_id, hls_s3_key, hls_url,
                                     thumbnail_url, duration_seconds):
        """
        Called by the MediaConvert completion webhook.
        Updates the VideoLesson with the HLS stream URL.
        """
        try:
            video_lesson = VideoLesson.objects.get(id=video_lesson_id)
        except VideoLesson.DoesNotExist:
            logger.error("VideoLesson %s not found on transcoding complete", video_lesson_id)
            return

        video_lesson.hls_s3_key = hls_s3_key
        video_lesson.hls_url = hls_url
        video_lesson.thumbnail_url = thumbnail_url
        video_lesson.duration_seconds = duration_seconds
        video_lesson.transcoding_status = TranscodingStatus.COMPLETE
        video_lesson.save(update_fields=[
            "hls_s3_key", "hls_url", "thumbnail_url",
            "duration_seconds", "transcoding_status", "updated_at",
        ])
        logger.info("Transcoding complete for VideoLesson %s", video_lesson_id)


class EnrollmentService:

    @staticmethod
    @transaction.atomic
    def enroll(user, course):
        if course.status != CourseStatus.PUBLISHED:
            raise ServiceError("This course is not available for enrollment.")
        if course.deleted_at is not None:
            raise ServiceError("This course is no longer available.")
        if Enrollment.objects.filter(user=user, course=course).exists():
            raise ConflictError("You are already enrolled in this course.")
        if course.price > 0 and not EntitlementService.can_access_course(user, course):
            raise PermissionError("An active subscription or entitlement is required to enroll in paid courses.")
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
            status=EnrollmentStatus.ACTIVE,
            amount_paid=course.price,
        )
        AnalyticsService.track(
            name="course_started",
            user=user,
            target=course,
            metadata={"enrollment_id": str(enrollment.id)},
        )
        logger.info("User %s enrolled in course %s", user.email, course.title)
        return enrollment

    @staticmethod
    def get_enrollment(user, course):
        try:
            return Enrollment.objects.get(user=user, course=course)
        except Enrollment.DoesNotExist:
            raise NotFoundError("You are not enrolled in this course.")


class ProgressService:

    @staticmethod
    @transaction.atomic
    def update_progress(enrollment, lesson, watch_percentage, last_position_seconds=0):
        if lesson.course != enrollment.course:
            raise ServiceError("This lesson does not belong to the enrolled course.")

        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )

        progress.watch_percentage = max(progress.watch_percentage, watch_percentage)
        progress.last_position_seconds = last_position_seconds

        if not progress.is_completed and watch_percentage >= VIDEO_COMPLETION_THRESHOLD:
            progress.is_completed = True
            progress.completed_at = timezone.now()

        progress.save(update_fields=[
            "watch_percentage", "last_position_seconds",
            "is_completed", "completed_at", "updated_at",
        ])

        enrollment.last_accessed_at = timezone.now()
        enrollment.save(update_fields=["last_accessed_at"])

        if progress.is_completed:
            AnalyticsService.track(
                name="lesson_completed",
                user=enrollment.user,
                target=lesson,
                metadata={"course_id": str(enrollment.course_id)},
            )
            ProgressService._check_course_completion(enrollment)

        return progress

    @staticmethod
    def mark_text_lesson_complete(enrollment, lesson):
        if lesson.lesson_type not in ("text",):
            raise ServiceError("This endpoint is only for text lessons.")
        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )
        if not progress.is_completed:
            progress.is_completed = True
            progress.watch_percentage = 100
            progress.completed_at = timezone.now()
            progress.save(update_fields=[
                "is_completed", "watch_percentage", "completed_at", "updated_at"
            ])
            ProgressService._check_course_completion(enrollment)
        return progress

    @staticmethod
    def get_course_progress(enrollment):
        total = enrollment.course.lessons.filter(
            is_published=True, deleted_at=None
        ).count()
        completed = enrollment.lesson_progress.filter(is_completed=True).count()
        percentage = round((completed / total * 100)) if total > 0 else 0
        return {
            "total_lessons": total,
            "completed_lessons": completed,
            "percentage": percentage,
        }

    @staticmethod
    def _check_course_completion(enrollment):
        total = enrollment.course.lessons.filter(
            is_published=True, deleted_at=None
        ).count()
        completed = enrollment.lesson_progress.filter(is_completed=True).count()

        if total > 0 and completed >= total:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = timezone.now()
            enrollment.save(update_fields=["status", "completed_at", "updated_at"])
            logger.info(
                "Course completed: user=%s course=%s",
                enrollment.user.email,
                enrollment.course.title,
            )
            from tasks.certificates import generate_certificate
            generate_certificate.delay(str(enrollment.id))


class LessonReorderService:

    @staticmethod
    def reorder(course, reorder_data, instructor):
        from django.db import transaction
        from common.exceptions import PermissionError, ServiceError
        from .models import Lesson
        import logging
        logger = logging.getLogger(__name__)

        if course.instructor != instructor:
            raise PermissionError('You do not own this course.')

        submitted_ids = {str(item['id']) for item in reorder_data}
        existing_lessons = list(course.lessons.filter(deleted_at=None).only('id', 'position'))
        existing_ids = {str(lesson.id) for lesson in existing_lessons}

        missing = existing_ids - submitted_ids
        extra = submitted_ids - existing_ids

        if missing:
            raise ServiceError(
                'Missing lesson IDs in reorder payload: ' + ', '.join(missing) + '. All lessons must be included.'
            )
        if extra:
            raise ServiceError('Unknown lesson IDs submitted: ' + ', '.join(extra) + '.')

        position_map = {str(item['id']): item['position'] for item in reorder_data}

        with transaction.atomic():
            for lesson in existing_lessons:
                lesson.position = position_map[str(lesson.id)]
            Lesson.objects.bulk_update(existing_lessons, ['position'])

        logger.info('Reordered %d lessons in course %s by %s', len(existing_lessons), course.id, instructor.email)
        return list(course.lessons.filter(deleted_at=None).order_by('position'))

    @staticmethod
    def validate_unique_positions(course, exclude_lesson_id=None):
        qs = course.lessons.filter(deleted_at=None)
        if exclude_lesson_id:
            qs = qs.exclude(id=exclude_lesson_id)
        positions = list(qs.values_list('position', flat=True))
        return len(positions) == len(set(positions))


class LessonInlineUpdateService:

    ALLOWED_FIELDS = {'title', 'lesson_type', 'content', 'is_published', 'is_free_preview'}

    @staticmethod
    def update(lesson, data, instructor):
        from common.exceptions import PermissionError, ServiceError
        import logging
        logger = logging.getLogger(__name__)

        if lesson.course.instructor != instructor:
            raise PermissionError('You do not own this course.')

        if data.get('is_published') is True and lesson.lesson_type == 'video':
            try:
                video = lesson.video
                if video.transcoding_status != 'complete':
                    raise ServiceError('Cannot publish a video lesson until transcoding is complete.')
            except Exception as e:
                if 'DoesNotExist' in type(e).__name__:
                    raise ServiceError('Cannot publish a video lesson that has no video uploaded.')
                raise

        update_fields = []
        for field in LessonInlineUpdateService.ALLOWED_FIELDS:
            if field in data:
                setattr(lesson, field, data[field])
                update_fields.append(field)

        if update_fields:
            update_fields.append('updated_at')
            lesson.save(update_fields=update_fields)
            logger.info('Lesson %s updated fields %s by %s', lesson.id, update_fields, instructor.email)

        return lesson
