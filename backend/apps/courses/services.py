import logging
from pathlib import Path

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.analytics.services import AnalyticsService
from apps.notifications.models import NotificationCategory, NotificationService, NotificationType
from common.audit import AuditService
from common.entitlements import EntitlementService
from common.exceptions import ConflictError, NotFoundError, PermissionError, ServiceError
from common.permission_service import PermissionService
from common.storage import generate_presigned_download_url, generate_presigned_upload_url
from common.uploads import UploadValidationService

from .models import (
    AcademicOverrideLog,
    AcademicOverrideReason,
    AcademicReviewerProfile,
    ContentReviewStatus,
    Course,
    CourseProject,
    CourseProjectReviewDecision,
    CourseReview,
    CourseStatus,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonProgress,
    LessonStructuredReview,
    LessonVersion,
    MalwareScanStatus,
    ResourceLibraryItem,
    ResourceType,
    ResourceVisibility,
    ReviewAssignment,
    ReviewDecision,
    ReviewerRole,
    ReviewPriority,
    ReviewTargetType,
    TranscodingStatus,
    VideoLesson,
)

logger = logging.getLogger(__name__)

VIDEO_COMPLETION_THRESHOLD = 90  # percent


class CourseService:
    @staticmethod
    def publish_blockers(course) -> list[dict]:
        blockers = []

        def add(code: str, message: str, severity: str = "error"):
            blockers.append({"code": code, "message": message, "severity": severity})

        if not course.instructor_id or not getattr(course.instructor, "is_active", False):
            add("inactive_instructor", "Course must have an active instructor.")
        if not course.description.strip() or not course.short_description.strip():
            add("missing_description", "Course description and short description are required.")
        if not course.what_you_learn:
            add("missing_objectives", "Course learning objectives are required.")
        if not course.requirements:
            add("missing_prerequisites", "Course prerequisites are required.")

        lessons = course.lessons.filter(deleted_at=None)
        published_lessons = lessons.filter(is_published=True)
        if not published_lessons.exists():
            add("no_published_lessons", "Publish at least one lesson before publishing the course.")
        if published_lessons.filter(content__exact="").exists():
            add("empty_published_lesson", "Published lessons cannot have empty content.")
        if published_lessons.filter(published_version=0).exists():
            add(
                "missing_published_version",
                "Every published lesson must be tied to an approved published version.",
            )
        if published_lessons.exclude(
            review_status__in=[ContentReviewStatus.APPROVED, ContentReviewStatus.PUBLISHED]
        ).exists():
            add("unapproved_published_lesson", "Every published lesson must be approved.")
        for lesson in published_lessons:
            if (
                "[REVIEW REQUIRED]" in lesson.content
                or "Content status: review_required" in lesson.content
            ):
                add("review_marker", "Published lessons cannot contain review-required markers.")
                break

        unresolved_lesson_reviews = lessons.filter(
            review_status__in=[
                ContentReviewStatus.DRAFT,
                ContentReviewStatus.NEEDS_REVIEW,
                ContentReviewStatus.UNDER_REVIEW,
                ContentReviewStatus.CHANGES_REQUESTED,
                ContentReviewStatus.REJECTED,
            ]
        )
        if unresolved_lesson_reviews.exists():
            add("lesson_review_unresolved", "All lessons must be approved before publishing.")

        try:
            from apps.assessments.models import QuestionReviewStatus, QuizQuestion

            approved_count = QuizQuestion.objects.filter(
                course=course,
                review_status=QuestionReviewStatus.APPROVED,
                is_certificate_eligible=True,
            ).count()
            if course.quiz_questions.exists() and approved_count < 5:
                add(
                    "assessment_coverage",
                    "Courses with assessments need at least five approved "
                    "certificate-eligible questions before publishing.",
                )
            if course.quiz_questions.filter(explanation__icontains="[REVIEW REQUIRED]").exists():
                add(
                    "assessment_review_marker",
                    "Assessment content still contains review-required markers.",
                )
            if (
                course.quiz_questions.filter(is_certificate_eligible=True)
                .exclude(review_status=QuestionReviewStatus.APPROVED)
                .exists()
            ):
                add(
                    "certificate_question_unapproved",
                    "Certificate-eligible questions must be approved.",
                )
        except Exception as exc:
            logger.warning("Course publish assessment validation skipped: %s", exc)

        if "requires-final-project" in (course.tags or []):
            project = getattr(course, "project", None)
            if not project or project.approval_state != ContentReviewStatus.APPROVED:
                add(
                    "project_not_approved",
                    "Final project completion rules must be approved before publishing.",
                )

        rejected_or_missing_resources = course.resources.filter(
            review_status__in=[ContentReviewStatus.REJECTED, ContentReviewStatus.CHANGES_REQUESTED]
        )
        if rejected_or_missing_resources.exists():
            add(
                "resource_not_approved",
                "Approved course content cannot reference rejected resources.",
            )
        if course.resources.filter(storage_key="", file_url="").exists():
            add(
                "resource_missing_file",
                "Course resources must include a valid storage key or file URL.",
            )
        if course.resources.exclude(
            review_status__in=[ContentReviewStatus.APPROVED, ContentReviewStatus.PUBLISHED]
        ).exists():
            add(
                "resource_review_unresolved", "Course resources must be approved before publishing."
            )
        unsafe_scan_states = [
            MalwareScanStatus.PENDING,
            MalwareScanStatus.SCANNING,
            MalwareScanStatus.INFECTED,
            MalwareScanStatus.FAILED,
        ]
        if course.resources.filter(malware_scan_status__in=unsafe_scan_states).exists():
            add(
                "resource_scan_not_clean",
                "Course resources must pass malware scanning or be explicitly skipped "
                "by a disabled scanner before publishing.",
            )

        latest_review = course.academic_reviews.order_by("-created_at").first()
        if not latest_review or latest_review.status != ContentReviewStatus.APPROVED:
            add("course_review_not_approved", "Course must pass academic review before publishing.")

        if course.review_assignments.filter(
            review_status=ContentReviewStatus.CHANGES_REQUESTED
        ).exists():
            add("changes_requested_unresolved", "Resolve all requested changes before publishing.")

        return blockers

    @staticmethod
    def publish_validation_errors(course) -> list[str]:
        return [blocker["message"] for blocker in CourseService.publish_blockers(course)]

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
        errors = CourseService.publish_validation_errors(course)
        if errors:
            AuditService.record(
                actor=instructor,
                action="course_publication_blocked",
                target=course,
                metadata={"blockers": CourseService.publish_blockers(course)},
            )
            raise ServiceError("Course is not ready to publish: " + " ".join(errors))
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
        video_lesson.save(
            update_fields=["original_s3_key", "file_size_bytes", "transcoding_status"]
        )

        from tasks.video import trigger_transcoding

        trigger_transcoding.delay(
            s3_key=s3_key,
            lesson_id=str(lesson.id),
            video_lesson_id=str(video_lesson.id),
        )

        logger.info("Transcoding triggered for lesson %s", lesson.id)
        return video_lesson

    @staticmethod
    def handle_transcoding_complete(
        video_lesson_id, hls_s3_key, hls_url, thumbnail_url, duration_seconds
    ):
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
        video_lesson.save(
            update_fields=[
                "hls_s3_key",
                "hls_url",
                "thumbnail_url",
                "duration_seconds",
                "transcoding_status",
                "updated_at",
            ]
        )
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
            raise PermissionError(
                "An active subscription or entitlement is required to enroll in paid courses."
            )
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
        except Enrollment.DoesNotExist as exc:
            raise NotFoundError("You are not enrolled in this course.") from exc


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

        progress.save(
            update_fields=[
                "watch_percentage",
                "last_position_seconds",
                "is_completed",
                "completed_at",
                "updated_at",
            ]
        )

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
            progress.save(
                update_fields=["is_completed", "watch_percentage", "completed_at", "updated_at"]
            )
            ProgressService._check_course_completion(enrollment)
        return progress

    @staticmethod
    def get_course_progress(enrollment):
        total = enrollment.course.lessons.filter(is_published=True, deleted_at=None).count()
        completed = enrollment.lesson_progress.filter(is_completed=True).count()
        percentage = round(completed / total * 100) if total > 0 else 0
        return {
            "total_lessons": total,
            "completed_lessons": completed,
            "percentage": percentage,
        }

    @staticmethod
    def _check_course_completion(enrollment):
        total = enrollment.course.lessons.filter(is_published=True, deleted_at=None).count()
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
        import logging

        from django.db import transaction

        from common.exceptions import PermissionError, ServiceError

        logger = logging.getLogger(__name__)

        if course.instructor != instructor:
            raise PermissionError("You do not own this course.")

        submitted_ids = {str(item["id"]) for item in reorder_data}
        existing_lessons = list(course.lessons.filter(deleted_at=None).only("id", "position"))
        existing_ids = {str(lesson.id) for lesson in existing_lessons}

        missing = existing_ids - submitted_ids
        extra = submitted_ids - existing_ids

        if missing:
            raise ServiceError(
                "Missing lesson IDs in reorder payload: "
                + ", ".join(missing)
                + ". All lessons must be included."
            )
        if extra:
            raise ServiceError("Unknown lesson IDs submitted: " + ", ".join(extra) + ".")

        position_map = {str(item["id"]): item["position"] for item in reorder_data}

        with transaction.atomic():
            for lesson in existing_lessons:
                lesson.position = position_map[str(lesson.id)]
            Lesson.objects.bulk_update(existing_lessons, ["position"])

        logger.info(
            "Reordered %d lessons in course %s by %s",
            len(existing_lessons),
            course.id,
            instructor.email,
        )
        return list(course.lessons.filter(deleted_at=None).order_by("position"))

    @staticmethod
    def validate_unique_positions(course, exclude_lesson_id=None):
        qs = course.lessons.filter(deleted_at=None)
        if exclude_lesson_id:
            qs = qs.exclude(id=exclude_lesson_id)
        positions = list(qs.values_list("position", flat=True))
        return len(positions) == len(set(positions))


class LessonInlineUpdateService:
    ALLOWED_FIELDS = {"title", "lesson_type", "content", "is_published", "is_free_preview"}

    @staticmethod
    def update(lesson, data, instructor):
        import logging

        from common.exceptions import PermissionError, ServiceError

        logger = logging.getLogger(__name__)

        if lesson.course.instructor != instructor:
            raise PermissionError("You do not own this course.")

        if data.get("is_published") is True and lesson.review_status not in {
            ContentReviewStatus.APPROVED,
            ContentReviewStatus.PUBLISHED,
        }:
            raise ServiceError("Lesson must be academically approved before publishing.")

        if data.get("is_published") is True and lesson.lesson_type == "video":
            try:
                video = lesson.video
                if video.transcoding_status != "complete":
                    raise ServiceError(
                        "Cannot publish a video lesson until transcoding is complete."
                    )
            except Exception as e:
                if "DoesNotExist" in type(e).__name__:
                    raise ServiceError(
                        "Cannot publish a video lesson that has no video uploaded."
                    ) from e
                raise

        update_fields = []
        for field in LessonInlineUpdateService.ALLOWED_FIELDS:
            if field in data:
                setattr(lesson, field, data[field])
                update_fields.append(field)

        if update_fields:
            update_fields.append("updated_at")
            lesson.save(update_fields=update_fields)
            logger.info(
                "Lesson %s updated fields %s by %s", lesson.id, update_fields, instructor.email
            )

        return lesson


class AuthoringPermissionMixin:
    @staticmethod
    def can_author(user, course) -> bool:
        from common.permission_service import PermissionService

        return PermissionService.can_publish_course(user, course)

    @staticmethod
    def can_review(user, course) -> bool:
        from common.permission_service import PermissionService

        return PermissionService.is_platform_admin(user) or bool(
            user
            and user.is_authenticated
            and (course.instructor_id == user.id or user.role == "content_moderator")
        )


class AcademicReviewAssignmentService:
    ACTIVE_ASSIGNMENT_STATES = {
        ContentReviewStatus.NEEDS_REVIEW,
        ContentReviewStatus.UNDER_REVIEW,
        ContentReviewStatus.CHANGES_REQUESTED,
    }

    @staticmethod
    def ensure_reviewer_profile(
        user, *, role=ReviewerRole.COURSE_REVIEWER, organization=None, subject_tags=None
    ):
        profile, _ = AcademicReviewerProfile.objects.update_or_create(
            user=user,
            defaults={
                "reviewer_role": role,
                "organization": organization,
                "subject_tags": subject_tags or [],
                "is_active": True,
            },
        )
        return profile

    @staticmethod
    def _target_context(target_type: str, target_id):
        if target_type == ReviewTargetType.COURSE:
            course = Course.objects.get(id=target_id, deleted_at=None)
            return {"course": course, "lesson": None, "organization": None}
        if target_type == ReviewTargetType.LESSON:
            lesson = Lesson.objects.select_related("course").get(id=target_id, deleted_at=None)
            return {"course": lesson.course, "lesson": lesson, "organization": None}
        if target_type == ReviewTargetType.PROJECT:
            project = CourseProject.objects.select_related("course").get(id=target_id)
            return {"course": project.course, "lesson": None, "organization": None}
        if target_type == ReviewTargetType.RESOURCE:
            resource = ResourceLibraryItem.objects.select_related("course").get(id=target_id)
            return {"course": resource.course, "lesson": None, "organization": None}
        if target_type == ReviewTargetType.ASSESSMENT:
            from apps.assessments.models import QuizQuestion

            question = QuizQuestion.objects.select_related("course").get(id=target_id)
            return {"course": question.course, "lesson": None, "organization": None}
        raise ServiceError("Unsupported review target type.")

    @staticmethod
    def active_assignment_count(reviewer) -> int:
        return ReviewAssignment.objects.filter(
            assigned_reviewer=reviewer,
            completed_at__isnull=True,
            review_status__in=AcademicReviewAssignmentService.ACTIVE_ASSIGNMENT_STATES,
        ).count()

    @staticmethod
    def validate_reviewer_for_assignment(*, reviewer, course=None, organization=None, subject=""):
        if course and course.instructor_id == reviewer.id:
            raise PermissionError("Instructors cannot be assigned to approve their own content.")
        profile = getattr(reviewer, "academic_reviewer_profile", None)
        if not profile or not profile.is_active:
            raise PermissionError("Reviewer must have an active academic reviewer profile.")
        if profile.organization_id and organization is not None:
            if profile.organization_id != getattr(organization, "id", None):
                raise PermissionError("Reviewer organization scope does not match this content.")
        if subject and profile.subject_tags:
            normalized = {str(item).strip().lower() for item in profile.subject_tags}
            if subject.strip().lower() not in normalized:
                raise PermissionError("Reviewer subject scope does not match this assignment.")
        active_count = AcademicReviewAssignmentService.active_assignment_count(reviewer)
        if active_count >= profile.max_active_assignments:
            raise ConflictError("Reviewer has reached the maximum active assignment limit.")

    @staticmethod
    def auto_select_reviewer(*, course=None, organization=None, subject=""):
        qs = AcademicReviewerProfile.objects.select_related("user").filter(
            is_active=True,
            automatic_assignment_enabled=True,
            user__is_active=True,
        )
        if organization is not None:
            qs = qs.filter(
                models.Q(organization=organization) | models.Q(organization__isnull=True)
            )
        candidates = []
        for profile in qs:
            if subject and profile.subject_tags:
                normalized = {str(item).strip().lower() for item in profile.subject_tags}
                if subject.strip().lower() not in normalized:
                    continue
            if course and course.instructor_id == profile.user_id:
                continue
            active_count = AcademicReviewAssignmentService.active_assignment_count(profile.user)
            if active_count < profile.max_active_assignments:
                candidates.append((active_count, profile.user))
        if not candidates:
            raise NotFoundError("No available academic reviewer matched the assignment rules.")
        return sorted(candidates, key=lambda item: item[0])[0][1]

    @staticmethod
    def assign(
        *,
        assigner,
        reviewer,
        target_type: str,
        target_id,
        due_date=None,
        priority=ReviewPriority.NORMAL,
        subject="",
    ):
        context = AcademicReviewAssignmentService._target_context(target_type, target_id)
        course = context["course"]
        if not PermissionService.can_assign_academic_review(
            assigner, course=course, organization=context["organization"]
        ):
            raise PermissionError("You cannot assign academic reviews.")
        if not PermissionService.is_academic_reviewer(reviewer):
            AcademicReviewAssignmentService.ensure_reviewer_profile(reviewer)
        AcademicReviewAssignmentService.validate_reviewer_for_assignment(
            reviewer=reviewer,
            course=course,
            organization=context["organization"],
            subject=subject,
        )

        assignment = ReviewAssignment.objects.create(
            target_type=target_type,
            target_id=target_id,
            course=course,
            lesson=context["lesson"],
            assigned_reviewer=reviewer,
            assigned_by=assigner,
            organization=context["organization"],
            subject=subject,
            priority=priority,
            due_date=due_date,
        )
        AuditService.record(
            actor=assigner,
            action="academic_review_assigned",
            target=assignment,
            metadata={
                "target_type": target_type,
                "target_id": str(target_id),
                "reviewer_id": str(reviewer.id),
            },
        )
        NotificationService.notify(
            recipient=reviewer,
            notification_type=NotificationType.ACADEMIC_REVIEW_ASSIGNED,
            title="Academic review assigned",
            body=f"You have been assigned a {target_type} review.",
            action_url="/reviewer/queue",
            payload={
                "category": NotificationCategory.COURSE_UPDATES,
                "assignment_id": str(assignment.id),
            },
        )
        return assignment

    @staticmethod
    def reassign(assignment, *, assigner, reviewer, reason: str = ""):
        if not PermissionService.can_assign_academic_review(
            assigner, course=assignment.course, organization=assignment.organization
        ):
            raise PermissionError("You cannot reassign academic reviews.")
        if assignment.course_id and assignment.course.instructor_id == reviewer.id:
            raise PermissionError("Instructors cannot be assigned to approve their own content.")
        AcademicReviewAssignmentService.validate_reviewer_for_assignment(
            reviewer=reviewer,
            course=assignment.course,
            organization=assignment.organization,
            subject=assignment.subject,
        )
        old_reviewer_id = str(assignment.assigned_reviewer_id)
        history = list(assignment.reassignment_history or [])
        history.append(
            {
                "from": old_reviewer_id,
                "to": str(reviewer.id),
                "assigned_by": str(assigner.id),
                "reason": reason,
                "at": timezone.now().isoformat(),
            }
        )
        assignment.assigned_reviewer = reviewer
        assignment.assigned_by = assigner
        assignment.reassignment_history = history
        assignment.review_status = ContentReviewStatus.NEEDS_REVIEW
        assignment.completed_at = None
        assignment.save(
            update_fields=[
                "assigned_reviewer",
                "assigned_by",
                "reassignment_history",
                "review_status",
                "completed_at",
                "updated_at",
            ]
        )
        AuditService.record(
            actor=assigner,
            action="academic_review_reassigned",
            target=assignment,
            metadata=history[-1],
        )
        return assignment

    @staticmethod
    def escalate_overdue(*, actor, lead_reviewer=None, reason: str = "overdue"):
        if not PermissionService.is_academic_admin(
            actor
        ) and not PermissionService.can_assign_academic_review(actor):
            raise PermissionError("You cannot escalate academic reviews.")
        overdue = ReviewAssignment.objects.filter(
            due_date__lt=timezone.now(),
            completed_at__isnull=True,
        ).exclude(review_status__in=[ContentReviewStatus.APPROVED, ContentReviewStatus.REJECTED])
        updated = 0
        for assignment in overdue.select_related("assigned_reviewer", "course"):
            assignment.escalation_level += 1
            assignment.escalated_to = lead_reviewer
            assignment.escalation_reason = reason
            assignment.escalated_at = timezone.now()
            assignment.priority = ReviewPriority.URGENT
            assignment.review_status = ContentReviewStatus.UNDER_REVIEW
            assignment.save(
                update_fields=[
                    "escalation_level",
                    "escalated_to",
                    "escalation_reason",
                    "escalated_at",
                    "priority",
                    "review_status",
                    "updated_at",
                ]
            )
            AuditService.record(
                actor=actor,
                action="academic_review_escalated",
                target=assignment,
                metadata={
                    "reason": reason,
                    "lead_reviewer_id": str(getattr(lead_reviewer, "id", "")),
                },
            )
            updated += 1
        return updated

    @staticmethod
    def queue_for(user, filters=None):
        filters = filters or {}
        qs = ReviewAssignment.objects.select_related(
            "course", "lesson", "assigned_reviewer", "assigned_by"
        )
        if not PermissionService.is_academic_admin(user):
            profile = getattr(user, "academic_reviewer_profile", None)
            if (
                profile
                and profile.is_active
                and profile.reviewer_role
                in {
                    ReviewerRole.LEAD_REVIEWER,
                    ReviewerRole.PLATFORM_ACADEMIC_REVIEWER,
                }
            ):
                if profile.organization_id:
                    qs = qs.filter(organization=profile.organization)
            else:
                qs = qs.filter(assigned_reviewer=user)
        if filters.get("assigned") == "me":
            qs = qs.filter(assigned_reviewer=user)
        if filters.get("status"):
            qs = qs.filter(review_status=filters["status"])
        if filters.get("priority"):
            qs = qs.filter(priority=filters["priority"])
        if filters.get("target_type"):
            qs = qs.filter(target_type=filters["target_type"])
        if filters.get("course"):
            qs = qs.filter(course_id=filters["course"])
        if filters.get("overdue"):
            qs = qs.filter(due_date__lt=timezone.now(), completed_at__isnull=True)
        return qs.order_by("due_date", "-created_at")

    @staticmethod
    def metrics(user):
        qs = AcademicReviewAssignmentService.queue_for(user)
        total = qs.count()
        completed = qs.filter(completed_at__isnull=False).count()
        overdue = qs.filter(due_date__lt=timezone.now(), completed_at__isnull=True).count()
        due_soon_cutoff = timezone.now() + timezone.timedelta(days=3)
        due_soon = qs.filter(
            due_date__gte=timezone.now(),
            due_date__lte=due_soon_cutoff,
            completed_at__isnull=True,
        ).count()
        completed_qs = qs.filter(completed_at__isnull=False)
        review_seconds = [
            (item.completed_at - item.created_at).total_seconds()
            for item in completed_qs
            if item.completed_at
        ]
        return {
            "total": total,
            "assigned": qs.filter(completed_at__isnull=True).count(),
            "completed": completed,
            "overdue": overdue,
            "due_soon": due_soon,
            "high_priority": qs.filter(
                priority__in=[ReviewPriority.HIGH, ReviewPriority.URGENT]
            ).count(),
            "average_review_time_hours": round(sum(review_seconds) / len(review_seconds) / 3600, 1)
            if review_seconds
            else 0,
            "approval_rate": round(
                qs.filter(review_status=ContentReviewStatus.APPROVED).count() / total * 100
            )
            if total
            else 0,
            "changes_requested": qs.filter(
                review_status=ContentReviewStatus.CHANGES_REQUESTED
            ).count(),
            "rejected": qs.filter(review_status=ContentReviewStatus.REJECTED).count(),
            "subject_distribution": list(
                qs.values("subject").annotate(count=models.Count("id")).order_by("subject")
            ),
            "organization_distribution": list(
                qs.values("organization_id")
                .annotate(count=models.Count("id"))
                .order_by("organization_id")
            ),
        }


class LessonVersionService(AuthoringPermissionMixin):
    @staticmethod
    def capture(lesson, editor, *, summary: str = ""):
        if not LessonVersionService.can_author(editor, lesson.course):
            raise PermissionError("You cannot edit this lesson.")
        next_version = (
            lesson.versions.order_by("-version_number")
            .values_list("version_number", flat=True)
            .first()
            or 0
        ) + 1
        version = LessonVersion.objects.create(
            lesson=lesson,
            version_number=next_version,
            editor=editor,
            title=lesson.title,
            lesson_type=lesson.lesson_type,
            content=lesson.content,
            summary_of_changes=summary,
            is_published_version=lesson.is_published,
        )
        lesson.draft_version = next_version
        lesson.save(update_fields=["draft_version", "updated_at"])
        return version

    @staticmethod
    def rollback(lesson, version, editor):
        if version.lesson_id != lesson.id:
            raise ServiceError("Version does not belong to this lesson.")
        if not LessonVersionService.can_author(editor, lesson.course):
            raise PermissionError("You cannot rollback this lesson.")
        LessonVersionService.capture(lesson, editor, summary="Snapshot before rollback")
        lesson.title = version.title
        lesson.lesson_type = version.lesson_type
        lesson.content = version.content
        lesson.review_status = ContentReviewStatus.DRAFT
        lesson.is_published = False
        lesson.save(
            update_fields=[
                "title",
                "lesson_type",
                "content",
                "review_status",
                "is_published",
                "updated_at",
            ]
        )
        AuditService.record(
            actor=editor,
            action="lesson_version_rollback",
            target=lesson,
            metadata={"version_number": version.version_number, "course_id": str(lesson.course_id)},
        )
        return lesson

    @staticmethod
    def compare(lesson, left, right):
        if left.lesson_id != lesson.id or right.lesson_id != lesson.id:
            raise ServiceError("Versions must belong to the same lesson.")
        return {
            "left_version": left.version_number,
            "right_version": right.version_number,
            "title_changed": left.title != right.title,
            "lesson_type_changed": left.lesson_type != right.lesson_type,
            "content_changed": left.content != right.content,
            "content_delta": len(right.content) - len(left.content),
        }


class AcademicReviewService(AuthoringPermissionMixin):
    @staticmethod
    def submit_course(course, user, *, comments: str = ""):
        if not AcademicReviewService.can_author(user, course):
            raise PermissionError("You cannot submit this course for review.")
        review = CourseReview.objects.create(
            course=course,
            status=ContentReviewStatus.NEEDS_REVIEW,
            submitted_by=user,
            comments=comments,
        )
        AuditService.record(actor=user, action="course_submitted_for_review", target=course)
        return review

    @staticmethod
    def review_course(course, reviewer, *, status: str, comments: str = "", required_fixes=None):
        if status not in ContentReviewStatus.values:
            raise ServiceError("Invalid review status.")
        if course.instructor_id == getattr(reviewer, "id", None) and not getattr(
            reviewer, "is_superuser", False
        ):
            raise PermissionError("Instructors cannot approve their own course.")
        assignment = (
            ReviewAssignment.objects.filter(
                course=course,
                target_type=ReviewTargetType.COURSE,
                assigned_reviewer=reviewer,
                completed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if assignment and not PermissionService.can_decide_academic_review(reviewer, assignment):
            raise PermissionError("You cannot review this course.")
        if not assignment and not PermissionService.is_academic_admin(reviewer):
            raise PermissionError("You cannot review this course.")
        review = CourseReview.objects.create(
            course=course,
            status=status,
            reviewer=reviewer,
            submitted_by=course.instructor,
            comments=comments,
            required_fixes=required_fixes or [],
            reviewed_at=timezone.now(),
        )
        AuditService.record(
            actor=reviewer,
            action="course_review_status_changed",
            target=course,
            metadata={"status": status},
        )
        if assignment:
            assignment.review_status = status
            assignment.completed_at = (
                timezone.now()
                if status
                in {
                    ContentReviewStatus.APPROVED,
                    ContentReviewStatus.REJECTED,
                }
                else None
            )
            assignment.save(update_fields=["review_status", "completed_at", "updated_at"])
        notification_type = (
            NotificationType.ACADEMIC_CONTENT_APPROVED
            if status == ContentReviewStatus.APPROVED
            else NotificationType.ACADEMIC_CHANGES_REQUESTED
            if status == ContentReviewStatus.CHANGES_REQUESTED
            else NotificationType.ACADEMIC_CONTENT_REJECTED
            if status == ContentReviewStatus.REJECTED
            else NotificationType.ACADEMIC_CONTENT_RESUBMITTED
        )
        NotificationService.notify(
            recipient=course.instructor,
            notification_type=notification_type,
            title="Course review updated",
            body=f"Review status for {course.title}: {status}.",
            action_url=f"/instructor/courses/{course.id}/review",
            payload={"category": NotificationCategory.COURSE_UPDATES, "course_id": str(course.id)},
        )
        return review

    @staticmethod
    def review_lesson(lesson, reviewer, *, status: str, comments: str = ""):
        if status not in ContentReviewStatus.values:
            raise ServiceError("Invalid lesson review status.")
        if lesson.course.instructor_id == getattr(reviewer, "id", None) and not getattr(
            reviewer, "is_superuser", False
        ):
            raise PermissionError("Instructors cannot approve their own lesson.")
        assignment = (
            ReviewAssignment.objects.filter(
                lesson=lesson,
                target_type=ReviewTargetType.LESSON,
                assigned_reviewer=reviewer,
                completed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if assignment and not PermissionService.can_decide_academic_review(reviewer, assignment):
            raise PermissionError("You cannot review this lesson.")
        if not assignment and not PermissionService.is_academic_admin(reviewer):
            raise PermissionError("You cannot review this lesson.")
        lesson.review_status = status
        if status == ContentReviewStatus.PUBLISHED:
            lesson.published_version = lesson.draft_version
            lesson.is_published = True
        elif status != ContentReviewStatus.APPROVED:
            lesson.is_published = False
        lesson.save(
            update_fields=[
                "review_status",
                "published_version",
                "is_published",
                "updated_at",
            ]
        )
        AuditService.record(
            actor=reviewer,
            action="lesson_review_status_changed",
            target=lesson,
            metadata={"status": status, "comments": comments},
        )
        if assignment:
            assignment.review_status = status
            assignment.completed_at = (
                timezone.now()
                if status
                in {
                    ContentReviewStatus.APPROVED,
                    ContentReviewStatus.PUBLISHED,
                    ContentReviewStatus.REJECTED,
                }
                else None
            )
            assignment.save(update_fields=["review_status", "completed_at", "updated_at"])
        return lesson

    @staticmethod
    def structured_lesson_review(
        lesson, reviewer, *, decision: str, section_comments=None, required_changes=None
    ):
        if decision not in ReviewDecision.values:
            raise ServiceError("Invalid review decision.")
        assignment = (
            ReviewAssignment.objects.filter(
                lesson=lesson,
                target_type=ReviewTargetType.LESSON,
                assigned_reviewer=reviewer,
                completed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if assignment and not PermissionService.can_decide_academic_review(reviewer, assignment):
            raise PermissionError("You cannot review this lesson.")
        if not assignment and not PermissionService.is_academic_admin(reviewer):
            raise PermissionError("You cannot review this lesson.")

        status_map = {
            ReviewDecision.APPROVE: ContentReviewStatus.APPROVED,
            ReviewDecision.APPROVE_MINOR_EDITS: ContentReviewStatus.APPROVED,
            ReviewDecision.REQUEST_CHANGES: ContentReviewStatus.CHANGES_REQUESTED,
            ReviewDecision.REJECT: ContentReviewStatus.REJECTED,
            ReviewDecision.ESCALATE: ContentReviewStatus.UNDER_REVIEW,
        }
        review = LessonStructuredReview.objects.create(
            lesson=lesson,
            assignment=assignment,
            reviewer=reviewer,
            decision=decision,
            section_comments=section_comments or {},
            required_changes=required_changes or [],
            completed_at=timezone.now(),
        )
        AcademicReviewService.review_lesson(
            lesson,
            reviewer,
            status=status_map[decision],
            comments="Structured lesson review completed.",
        )
        AuditService.record(
            actor=reviewer,
            action="structured_lesson_review_completed",
            target=review,
            metadata={"decision": decision, "lesson_id": str(lesson.id)},
        )
        return review

    @staticmethod
    def instructor_response(assignment, instructor, *, response: str, addressed: bool = False):
        if not assignment.course_id or assignment.course.instructor_id != getattr(
            instructor, "id", None
        ):
            raise PermissionError("You cannot respond to this review.")
        assignment.review_status = (
            ContentReviewStatus.NEEDS_REVIEW if addressed else ContentReviewStatus.CHANGES_REQUESTED
        )
        assignment.save(update_fields=["review_status", "updated_at"])
        AuditService.record(
            actor=instructor,
            action="academic_instructor_response",
            target=assignment,
            metadata={"response": response, "addressed": addressed},
        )
        NotificationService.notify(
            recipient=assignment.assigned_reviewer,
            notification_type=NotificationType.ACADEMIC_INSTRUCTOR_RESPONDED,
            title="Instructor responded to review",
            body=f"{assignment.course.title} has a new instructor response.",
            action_url="/reviewer/queue",
            payload={
                "category": NotificationCategory.COURSE_UPDATES,
                "assignment_id": str(assignment.id),
            },
        )
        return assignment


class CourseProjectService(AuthoringPermissionMixin):
    @staticmethod
    def upsert(course, user, data):
        if not CourseProjectService.can_author(user, course):
            raise PermissionError("You cannot edit this project.")
        project, created = CourseProject.objects.get_or_create(course=course)
        for field in [
            "instructions",
            "required_deliverables",
            "rubric",
            "evaluation_criteria",
            "passing_score",
            "reviewer_notes",
            "example_solution",
            "resources",
        ]:
            if field in data:
                setattr(project, field, data[field])
        if not created:
            project.version += 1
        if not created and project.approval_state == ContentReviewStatus.APPROVED:
            AuditService.record(
                actor=user,
                action="course_project_review_reopened",
                target=project,
                metadata={"reason": "approved_project_changed", "version": project.version},
            )
        project.approval_state = ContentReviewStatus.DRAFT
        project.save()
        AuditService.record(actor=user, action="course_project_updated", target=project)
        return project

    @staticmethod
    def review(project, reviewer, *, status: str, notes: str = ""):
        if status not in ContentReviewStatus.values:
            raise ServiceError("Invalid project review status.")
        if project.course.instructor_id == getattr(reviewer, "id", None) and not getattr(
            reviewer, "is_superuser", False
        ):
            raise PermissionError("Instructors cannot approve their own project.")
        if not CourseProjectService.can_review(
            reviewer, project.course
        ) and not PermissionService.is_academic_reviewer(reviewer):
            raise PermissionError("You cannot review this project.")
        project.approval_state = status
        project.reviewer_notes = notes
        project.reviewed_by = reviewer
        project.reviewed_at = timezone.now()
        project.save(
            update_fields=[
                "approval_state",
                "reviewer_notes",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )
        AuditService.record(
            actor=reviewer,
            action="course_project_reviewed",
            target=project,
            metadata={"status": status},
        )
        return project

    @staticmethod
    def structured_review(
        project,
        reviewer,
        *,
        decision: str,
        review_sections=None,
        required_changes=None,
        notes: str = "",
    ):
        if decision not in ReviewDecision.values:
            raise ServiceError("Invalid project review decision.")
        assignment = (
            ReviewAssignment.objects.filter(
                target_type=ReviewTargetType.PROJECT,
                target_id=project.id,
                assigned_reviewer=reviewer,
                completed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if assignment and not PermissionService.can_decide_academic_review(reviewer, assignment):
            raise PermissionError("You cannot review this project.")
        if not assignment and not PermissionService.is_academic_admin(reviewer):
            raise PermissionError("You cannot review this project.")
        status_map = {
            ReviewDecision.APPROVE: ContentReviewStatus.APPROVED,
            ReviewDecision.APPROVE_MINOR_EDITS: ContentReviewStatus.APPROVED,
            ReviewDecision.REQUEST_CHANGES: ContentReviewStatus.CHANGES_REQUESTED,
            ReviewDecision.REJECT: ContentReviewStatus.REJECTED,
            ReviewDecision.ESCALATE: ContentReviewStatus.UNDER_REVIEW,
        }
        decision_record = CourseProjectReviewDecision.objects.create(
            project=project,
            assignment=assignment,
            reviewer=reviewer,
            decision=decision,
            project_version=project.version,
            review_sections=review_sections or {},
            required_changes=required_changes or [],
            notes=notes,
        )
        CourseProjectService.review(project, reviewer, status=status_map[decision], notes=notes)
        if assignment:
            assignment.review_status = status_map[decision]
            assignment.completed_at = (
                timezone.now()
                if status_map[decision]
                in {
                    ContentReviewStatus.APPROVED,
                    ContentReviewStatus.REJECTED,
                }
                else None
            )
            assignment.save(update_fields=["review_status", "completed_at", "updated_at"])
        return decision_record


class MalwareScanService:
    PROVIDER_DISABLED = "disabled"
    PROVIDER_MOCK = "mock"
    PROVIDER_CLAMAV = "clamav"
    PROVIDER_EXTERNAL = "external"

    BLOCKING_STATES = {
        MalwareScanStatus.PENDING,
        MalwareScanStatus.SCANNING,
        MalwareScanStatus.INFECTED,
        MalwareScanStatus.FAILED,
    }

    @staticmethod
    def configured_provider() -> str:
        return getattr(settings, "ACADEMIC_MALWARE_SCANNER", "disabled") or "disabled"

    @staticmethod
    def is_download_blocked(resource) -> bool:
        return resource.malware_scan_status in {
            MalwareScanStatus.SCANNING,
            MalwareScanStatus.INFECTED,
            MalwareScanStatus.FAILED,
        } or (
            resource.malware_scan_status == MalwareScanStatus.PENDING
            and (resource.metadata or {}).get("malware_scan_required", False)
        )

    @staticmethod
    def is_approval_blocked(resource) -> bool:
        provider = resource.malware_scanner or MalwareScanService.configured_provider()
        if provider == MalwareScanService.PROVIDER_DISABLED:
            return resource.malware_scan_status not in {
                MalwareScanStatus.SKIPPED,
                MalwareScanStatus.CLEAN,
            }
        return resource.malware_scan_status != MalwareScanStatus.CLEAN

    @staticmethod
    def scan_resource(resource, *, actor=None, provider: str | None = None, sample_text: str = ""):
        provider = provider or MalwareScanService.configured_provider()
        started_at = timezone.now()
        resource.malware_scan_status = MalwareScanStatus.SCANNING
        resource.malware_scanner = provider
        resource.malware_scan_result = {"provider": provider, "started_at": started_at.isoformat()}
        resource.save(
            update_fields=[
                "malware_scan_status",
                "malware_scanner",
                "malware_scan_result",
                "updated_at",
            ]
        )

        evidence = " ".join(
            [
                resource.file_name or "",
                resource.checksum or "",
                sample_text or "",
                str((resource.metadata or {}).get("scan_sample", "")),
            ]
        ).lower()
        if provider == MalwareScanService.PROVIDER_DISABLED:
            status = MalwareScanStatus.SKIPPED
            result = {"reason": "scanner_disabled"}
        elif provider == MalwareScanService.PROVIDER_MOCK:
            infected = "eicar" in evidence or "x5o!p%@ap" in evidence
            status = MalwareScanStatus.INFECTED if infected else MalwareScanStatus.CLEAN
            result = {"signature": "EICAR-Test-File" if infected else "", "mock": True}
        elif provider == MalwareScanService.PROVIDER_CLAMAV:
            status = MalwareScanStatus.FAILED
            result = {
                "error": "ClamAV adapter configured but no daemon/client is wired in this runtime."
            }
        else:
            status = MalwareScanStatus.FAILED
            result = {"error": f"Unsupported malware scanner provider: {provider}"}

        resource.malware_scan_status = status
        resource.malware_scanned_at = timezone.now()
        resource.malware_scan_result = {
            **resource.malware_scan_result,
            **result,
            "status": status,
            "finished_at": resource.malware_scanned_at.isoformat(),
        }
        resource.save(
            update_fields=[
                "malware_scan_status",
                "malware_scanned_at",
                "malware_scan_result",
                "updated_at",
            ]
        )
        AuditService.record(
            actor=actor or resource.owner,
            action="academic_resource_malware_scanned",
            target=resource,
            metadata={
                "provider": provider,
                "status": status,
                "result": resource.malware_scan_result,
            },
        )
        return resource


class AcademicOverrideService:
    ALLOWED_REASONS = set(AcademicOverrideReason.values)
    PROHIBITED_TARGETS = {
        "certificate_question_approval",
        "infected_resource_approval",
        "missing_lesson_content",
        "audit_history_deletion",
    }

    @staticmethod
    def record_override(
        *,
        actor,
        target,
        reason_code: str,
        reason: str,
        previous_state: dict,
        new_state: dict,
        metadata=None,
    ):
        if not PermissionService.is_academic_admin(actor):
            raise PermissionError("Only platform academic admins can perform academic overrides.")
        if reason_code not in AcademicOverrideService.ALLOWED_REASONS:
            raise ServiceError("This academic override reason is not allowed.")
        if not reason.strip():
            raise ServiceError("Academic override reason is required.")
        target_type = target.__class__.__name__
        if target_type in AcademicOverrideService.PROHIBITED_TARGETS:
            raise ServiceError("This target cannot be overridden.")
        log = AcademicOverrideLog.objects.create(
            actor=actor,
            target_type=target_type,
            target_id=target.id,
            reason_code=reason_code,
            reason=reason,
            previous_state=previous_state,
            new_state=new_state,
            metadata=metadata or {},
        )
        AuditService.record(
            actor=actor,
            action="academic_override_recorded",
            target=target,
            metadata={
                "override_id": str(log.id),
                "reason_code": reason_code,
                "previous_state": previous_state,
                "new_state": new_state,
            },
        )
        return log


class ResourceLibraryService(AuthoringPermissionMixin):
    ALLOWED_RESOURCE_EXTENSIONS = {
        ".csv",
        ".xlsx",
        ".pdf",
        ".pptx",
        ".docx",
        ".ipynb",
        ".sql",
        ".txt",
        ".zip",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }
    ALLOWED_RESOURCE_MIME_TYPES = {
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/x-ipynb+json",
        "application/sql",
        "text/plain",
        "application/zip",
        "image/png",
        "image/jpeg",
        "image/webp",
    }
    BLOCKED_EXTENSIONS = {".exe", ".dll", ".bat", ".cmd", ".sh", ".msi", ".ps1", ".scr", ".js"}
    MAX_RESOURCE_SIZE_BYTES = 50 * 1024 * 1024

    @staticmethod
    def create(owner, data):
        course = data.get("course")
        if course and not ResourceLibraryService.can_author(owner, course):
            raise PermissionError("You cannot attach resources to this course.")
        if data.get("file_name") or data.get("content_type") or data.get("file_size_bytes"):
            ResourceLibraryService.validate_resource_metadata(
                file_name=data.get("file_name", data.get("title", "")),
                content_type=data.get("content_type", ""),
                file_size=int(data.get("file_size_bytes") or 0),
            )
        return ResourceLibraryItem.objects.create(owner=owner, **data)

    @staticmethod
    def list_for_user(user):
        if PermissionService.is_platform_admin(user):
            return ResourceLibraryItem.objects.select_related("owner", "course").all()
        return ResourceLibraryItem.objects.select_related("owner", "course").filter(owner=user)

    @staticmethod
    def validate_resource_metadata(*, file_name: str, content_type: str, file_size: int):
        extension = Path(file_name).suffix.lower()
        if extension in ResourceLibraryService.BLOCKED_EXTENSIONS:
            raise ServiceError("Executable files are not allowed as academic resources.")
        UploadValidationService.validate_metadata(
            file_name=file_name,
            content_type=content_type,
            file_size=file_size,
            allowed_extensions=ResourceLibraryService.ALLOWED_RESOURCE_EXTENSIONS,
            allowed_mime_types=ResourceLibraryService.ALLOWED_RESOURCE_MIME_TYPES,
            max_size_bytes=ResourceLibraryService.MAX_RESOURCE_SIZE_BYTES,
        )

    @staticmethod
    def request_upload(
        owner,
        *,
        course=None,
        file_name: str,
        content_type: str,
        file_size: int,
        checksum: str = "",
        visibility: str = ResourceVisibility.PRIVATE,
    ):
        if course and not ResourceLibraryService.can_author(owner, course):
            raise PermissionError("You cannot upload resources to this course.")
        ResourceLibraryService.validate_resource_metadata(
            file_name=file_name,
            content_type=content_type,
            file_size=file_size,
        )
        duplicate = None
        if checksum:
            duplicate = ResourceLibraryItem.objects.filter(owner=owner, checksum=checksum).first()
        if duplicate:
            raise ConflictError("A resource with the same checksum already exists.")
        folder = f"academic-resources/{owner.id}"
        if course:
            folder = f"academic-resources/courses/{course.id}"
        upload = generate_presigned_upload_url(
            file_name=file_name,
            folder=folder,
            content_type=content_type,
        )
        resource_type = ResourceLibraryService.resource_type_for_file(file_name)
        resource = ResourceLibraryItem.objects.create(
            owner=owner,
            course=course,
            title=Path(file_name).stem[:255],
            resource_type=resource_type,
            file_url=upload.get("file_url", ""),
            storage_key=upload.get("key", ""),
            file_name=file_name,
            content_type=content_type,
            file_size_bytes=file_size,
            checksum=checksum,
            visibility=visibility,
            review_status=ContentReviewStatus.NEEDS_REVIEW,
            malware_scan_status="pending",
            malware_scanner=MalwareScanService.configured_provider(),
            metadata={"malware_scan_required": True},
        )
        AuditService.record(
            actor=owner,
            action="academic_resource_upload_requested",
            target=resource,
            metadata={"file_name": file_name, "content_type": content_type, "file_size": file_size},
        )
        return {"resource": resource, "upload": upload, "malware_scan_required": True}

    @staticmethod
    def resource_type_for_file(file_name: str) -> str:
        ext = Path(file_name).suffix.lower()
        return {
            ".csv": ResourceType.CSV,
            ".xlsx": ResourceType.EXCEL,
            ".pdf": ResourceType.PDF,
            ".pptx": ResourceType.POWERPOINT,
            ".docx": ResourceType.DOCX,
            ".ipynb": ResourceType.NOTEBOOK,
            ".sql": ResourceType.SQL,
            ".txt": ResourceType.TXT,
            ".zip": ResourceType.ZIP,
            ".png": ResourceType.IMAGE,
            ".jpg": ResourceType.IMAGE,
            ".jpeg": ResourceType.IMAGE,
            ".webp": ResourceType.IMAGE,
        }.get(ext, ResourceType.OTHER)

    @staticmethod
    def review(resource, reviewer, *, status: str, notes: str = ""):
        if status not in ContentReviewStatus.values:
            raise ServiceError("Invalid resource review status.")
        if (
            resource.course_id
            and resource.course.instructor_id == getattr(reviewer, "id", None)
            and not getattr(reviewer, "is_superuser", False)
        ):
            raise PermissionError("Instructors cannot approve their own resources.")
        if not PermissionService.is_academic_reviewer(reviewer):
            raise PermissionError("You cannot review this resource.")
        if status in {ContentReviewStatus.APPROVED, ContentReviewStatus.PUBLISHED}:
            if MalwareScanService.is_approval_blocked(resource):
                raise ServiceError("Resource cannot be approved until malware scan is clean.")
        resource.review_status = status
        resource.reviewed_by = reviewer
        resource.reviewed_at = timezone.now()
        resource.review_notes = notes
        resource.save(
            update_fields=[
                "review_status",
                "reviewed_by",
                "reviewed_at",
                "review_notes",
                "updated_at",
            ]
        )
        AuditService.record(
            actor=reviewer,
            action="academic_resource_reviewed",
            target=resource,
            metadata={
                "status": status,
                "malware_scan_status": resource.malware_scan_status,
                "malware_scanner": resource.malware_scanner,
            },
        )
        return resource

    @staticmethod
    def download(resource, user):
        if MalwareScanService.is_download_blocked(resource):
            AuditService.record(
                actor=user,
                action="academic_resource_download_blocked",
                target=resource,
                metadata={"malware_scan_status": resource.malware_scan_status},
            )
            raise PermissionError("Resource download is blocked by malware scan status.")
        if resource.visibility == ResourceVisibility.PRIVATE and resource.owner_id != getattr(
            user, "id", None
        ):
            if not PermissionService.is_academic_reviewer(
                user
            ) and not PermissionService.is_platform_admin(user):
                raise PermissionError("You cannot download this private resource.")
        if resource.visibility == ResourceVisibility.COURSE and resource.course_id:
            if not PermissionService.can_publish_course(
                user, resource.course
            ) and not PermissionService.is_academic_reviewer(user):
                raise PermissionError("You cannot download this course resource.")
        resource.download_count += 1
        resource.save(update_fields=["download_count", "updated_at"])
        AuditService.record(actor=user, action="academic_resource_downloaded", target=resource)
        if resource.storage_key:
            return generate_presigned_download_url(resource.storage_key)
        return resource.file_url


class CourseQualityService:
    @staticmethod
    def readiness(course) -> dict:
        lessons = course.lessons.filter(deleted_at=None)
        published_lessons = lessons.filter(is_published=True)
        approved_lessons = lessons.filter(
            review_status__in=[
                ContentReviewStatus.APPROVED,
                ContentReviewStatus.PUBLISHED,
            ]
        )
        questions = course.quiz_questions.all()
        approved_cert_questions = questions.filter(
            review_status="approved",
            is_certificate_eligible=True,
        )
        project = getattr(course, "project", None)
        blockers = CourseService.publish_validation_errors(course)
        lesson_count = lessons.count()
        published_count = published_lessons.count()
        approved_count = approved_lessons.count()
        approved_question_count = approved_cert_questions.count()
        draft_count = lessons.filter(review_status=ContentReviewStatus.DRAFT).count()
        raw_checks = [
            {
                "key": "learning_objectives",
                "label": "Learning objectives",
                "passed": bool(course.what_you_learn),
                "detail": "Course outcomes are defined."
                if course.what_you_learn
                else "Add clear learning outcomes.",
            },
            {
                "key": "prerequisites",
                "label": "Prerequisites",
                "passed": bool(course.requirements),
                "detail": "Prerequisites are defined."
                if course.requirements
                else "Add required background knowledge.",
            },
            {
                "key": "lesson_count",
                "label": "Lessons",
                "passed": lesson_count >= 1,
                "detail": f"{lesson_count} lessons configured.",
            },
            {
                "key": "lesson_approval",
                "label": "Lesson review",
                "passed": lesson_count > 0 and approved_count == lesson_count,
                "detail": f"{approved_count} of {lesson_count} lessons approved.",
            },
            {
                "key": "assessment_coverage",
                "label": "Assessment coverage",
                "passed": approved_question_count >= 5 or not questions.exists(),
                "detail": f"{approved_question_count} approved certificate questions.",
            },
            {
                "key": "project_complete",
                "label": "Final project",
                "passed": "requires-final-project" not in (course.tags or [])
                or bool(project and project.approval_state == ContentReviewStatus.APPROVED),
                "detail": "Final project gate is satisfied.",
            },
            {
                "key": "resources",
                "label": "Resources",
                "passed": course.resources.exists()
                or "requires-dataset" not in (course.tags or []),
                "detail": "Required course resources are available.",
            },
            {
                "key": "empty_lessons",
                "label": "Lesson content",
                "passed": not lessons.filter(content__exact="").exists(),
                "detail": "Published lesson content is not empty.",
            },
            {
                "key": "draft_content",
                "label": "Draft cleanup",
                "passed": draft_count == 0,
                "detail": f"{draft_count} lessons remain in draft review state.",
            },
        ]
        score = round(sum(1 for check in raw_checks if check["passed"]) / len(raw_checks) * 100)
        return {
            "course_id": str(course.id),
            "course_title": course.title,
            "title": course.title,
            "status": course.status,
            "quality_score": score,
            "publish_ready": not blockers,
            "checks": raw_checks,
            "blockers": blockers,
            "metrics": {
                "lesson_count": lesson_count,
                "published_lessons": published_count,
                "approved_lessons": approved_count,
                "draft_lessons": draft_count,
                "question_count": questions.count(),
                "approved_certificate_questions": approved_question_count,
            },
            "lesson_counts": {
                "total": lesson_count,
                "published": published_count,
                "approved": approved_count,
                "draft": draft_count,
            },
            "assessment_counts": {
                "total": questions.count(),
                "approved_certificate_eligible": approved_question_count,
                "review_required": questions.filter(review_status="review_required").count(),
            },
        }

    @staticmethod
    def dashboard(user):
        qs = Course.objects.filter(deleted_at=None)
        if not PermissionService.is_platform_admin(user):
            qs = qs.filter(instructor=user)
        courses = list(
            qs.select_related("instructor").prefetch_related("lessons", "quiz_questions")
        )
        readiness = [CourseQualityService.readiness(course) for course in courses]
        return {
            "courses": readiness,
            "summary": {
                "total_courses": len(courses),
                "publish_ready": sum(1 for item in readiness if item["publish_ready"]),
                "average_quality_score": round(
                    sum(item["quality_score"] for item in readiness) / len(readiness)
                )
                if readiness
                else 0,
                "average_score": round(
                    sum(item["quality_score"] for item in readiness) / len(readiness)
                )
                if readiness
                else 0,
            },
        }


class InstructorAnalyticsService:
    @staticmethod
    def summary(user):
        qs = Course.objects.filter(deleted_at=None)
        if not PermissionService.is_platform_admin(user):
            qs = qs.filter(instructor=user)
        lessons = Lesson.objects.filter(course__in=qs, deleted_at=None)
        return {
            "courses_authored": qs.count(),
            "lessons_created": lessons.count(),
            "lessons_approved": lessons.filter(
                review_status__in=[
                    ContentReviewStatus.APPROVED,
                    ContentReviewStatus.PUBLISHED,
                ]
            ).count(),
            "reviews_completed": CourseReview.objects.filter(reviewer=user).count(),
            "courses_published": qs.filter(status=CourseStatus.PUBLISHED).count(),
            "resources_created": ResourceLibraryItem.objects.filter(owner=user).count(),
        }
