import logging
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import CareerTrack, UserTrackEnrollment
from .serializers import (
    CareerTrackListSerializer,
    CareerTrackDetailSerializer,
    UserTrackEnrollmentSerializer,
)

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def track_list(request):
    """
    GET /api/v1/tracks/

    Returns all active career tracks grouped by category.
    Public endpoint - no auth required.
    """
    category = request.query_params.get("category")
    tracks = CareerTrack.objects.filter(is_active=True).order_by("position", "title")

    if category:
        tracks = tracks.filter(category=category)

    serializer = CareerTrackListSerializer(
        tracks, many=True, context={"request": request}
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def track_detail(request, slug):
    """
    GET /api/v1/tracks/{slug}/

    Returns full track detail including courses by stage.
    """
    track = get_object_or_404(CareerTrack, slug=slug, is_active=True)
    serializer = CareerTrackDetailSerializer(track, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enroll_in_track(request, slug):
    """
    POST /api/v1/tracks/{slug}/enroll/

    Enroll the authenticated student in a career track.
    A student can be enrolled in multiple tracks simultaneously.
    """
    track = get_object_or_404(CareerTrack, slug=slug, is_active=True)

    enrollment, created = UserTrackEnrollment.objects.get_or_create(
        user=request.user,
        track=track,
    )

    if not created:
        return Response(
            {"detail": "You are already enrolled in this track."},
            status=status.HTTP_200_OK,
        )

    logger.info("Track enrollment: user=%s track=%s", request.user.email, track.title)
    return Response(
        UserTrackEnrollmentSerializer(enrollment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_tracks(request):
    """
    GET /api/v1/tracks/mine/

    Returns all tracks the authenticated student is enrolled in.
    """
    enrollments = UserTrackEnrollment.objects.filter(
        user=request.user
    ).select_related("track").order_by("-last_activity_at")

    return Response(UserTrackEnrollmentSerializer(enrollments, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_track_progress(request, slug):
    """
    POST /api/v1/tracks/{slug}/progress/

    Called when a student completes a course that belongs to this track.
    Updates courses_completed count and stage if needed.
    This is also called automatically from the course completion signal.
    """
    track = get_object_or_404(CareerTrack, slug=slug, is_active=True)

    try:
        enrollment = UserTrackEnrollment.objects.get(
            user=request.user, track=track
        )
    except UserTrackEnrollment.DoesNotExist:
        return Response(
            {"detail": "You are not enrolled in this track."},
            status=status.HTTP_404_NOT_FOUND,
        )

    from apps.courses.models import Enrollment, EnrollmentStatus
    completed_course_ids = set(
        Enrollment.objects.filter(
            user=request.user,
            status=EnrollmentStatus.COMPLETED,
        ).values_list("course_id", flat=True)
    )

    track_course_ids = set(
        track.track_courses.filter(is_required=True).values_list("course_id", flat=True)
    )
    completed_in_track = len(completed_course_ids & track_course_ids)
    enrollment.courses_completed = completed_in_track

    # Advance stage based on completion
    foundation_ids = set(
        track.track_courses.filter(
            is_required=True, stage=1
        ).values_list("course_id", flat=True)
    )
    core_ids = set(
        track.track_courses.filter(
            is_required=True, stage=2
        ).values_list("course_id", flat=True)
    )

    if foundation_ids and foundation_ids.issubset(completed_course_ids):
        if core_ids and core_ids.issubset(completed_course_ids):
            enrollment.current_stage = 3
        else:
            enrollment.current_stage = 2

    if completed_in_track >= track.required_courses_count and not enrollment.is_completed:
        from django.utils import timezone
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()
        logger.info(
            "Track completed: user=%s track=%s",
            request.user.email,
            track.title,
        )

    enrollment.save()
    return Response(UserTrackEnrollmentSerializer(enrollment).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def track_categories(request):
    """
    GET /api/v1/tracks/categories/

    Returns available track categories with counts.
    """
    from django.db.models import Count
    from .models import TrackCategory

    categories = []
    for value, label in TrackCategory.choices:
        count = CareerTrack.objects.filter(category=value, is_active=True).count()
        if count > 0:
            categories.append({
                "value": value,
                "label": label,
                "count": count,
            })

    return Response(categories)


def _update_enrollment_progress(enrollment):
    """
    Helper to update track progress from outside the view layer.
    Called when a course is completed that belongs to the track.
    """
    from apps.courses.models import Enrollment, EnrollmentStatus
    from django.utils import timezone

    completed_course_ids = set(
        Enrollment.objects.filter(
            user=enrollment.user,
            status=EnrollmentStatus.COMPLETED,
        ).values_list("course_id", flat=True)
    )

    track_course_ids = set(
        enrollment.track.track_courses.filter(
            is_required=True
        ).values_list("course_id", flat=True)
    )

    completed_in_track = len(completed_course_ids & track_course_ids)
    old_stage = enrollment.current_stage
    enrollment.courses_completed = completed_in_track

    foundation_ids = set(
        enrollment.track.track_courses.filter(
            is_required=True, stage=1
        ).values_list("course_id", flat=True)
    )
    core_ids = set(
        enrollment.track.track_courses.filter(
            is_required=True, stage=2
        ).values_list("course_id", flat=True)
    )

    if foundation_ids and foundation_ids.issubset(completed_course_ids):
        if core_ids and core_ids.issubset(completed_course_ids):
            enrollment.current_stage = 3
        else:
            enrollment.current_stage = 2

    if completed_in_track >= enrollment.track.required_courses_count and not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()

    enrollment.save()

    # Send stage advancement notification if stage changed
    if enrollment.current_stage > old_stage:
        try:
            from apps.notifications.models import NotificationService
            NotificationService.track_stage_advanced(
                enrollment.user, enrollment.track, enrollment.current_stage
            )
        except Exception:
            pass
