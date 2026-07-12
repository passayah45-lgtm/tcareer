import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.courses.models import Course, Lesson, Enrollment, EnrollmentStatus
from .models import CourseReview, DiscussionThread, DiscussionReply

logger = logging.getLogger(__name__)


# ── Serializers ───────────────────────────────────────────────────────────────

class CourseReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="user.full_name", read_only=True)
    author_avatar = serializers.CharField(source="user.avatar_url", read_only=True)

    class Meta:
        model = CourseReview
        fields = [
            "id", "author_name", "author_avatar", "stars", "title",
            "body", "helpful_count", "instructor_reply",
            "instructor_replied_at", "created_at",
        ]
        read_only_fields = [
            "id", "author_name", "author_avatar", "helpful_count",
            "instructor_reply", "instructor_replied_at", "created_at",
        ]


class CreateReviewSerializer(serializers.Serializer):
    stars = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=200, allow_blank=True, default="")
    body = serializers.CharField(max_length=3000, allow_blank=True, default="")


class DiscussionReplySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_avatar = serializers.CharField(source="author.avatar_url", read_only=True)

    class Meta:
        model = DiscussionReply
        fields = [
            "id", "author_name", "author_avatar", "body",
            "is_instructor_reply", "deleted_at", "created_at",
        ]
        read_only_fields = fields


class DiscussionThreadSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_avatar = serializers.CharField(source="author.avatar_url", read_only=True)
    replies = DiscussionReplySerializer(many=True, read_only=True)

    class Meta:
        model = DiscussionThread
        fields = [
            "id", "author_name", "author_avatar", "title", "body",
            "is_pinned", "is_resolved", "reply_count",
            "deleted_at", "created_at", "replies",
        ]
        read_only_fields = [
            "id", "author_name", "author_avatar", "is_pinned",
            "reply_count", "deleted_at", "created_at",
        ]


class DiscussionThreadListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = DiscussionThread
        fields = [
            "id", "author_name", "title", "is_pinned",
            "is_resolved", "reply_count", "created_at",
        ]


# ── Reviews ───────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def course_reviews(request, course_id):
    """
    GET /api/v1/community/courses/{course_id}/reviews/

    Public endpoint. Returns reviews and rating distribution.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)
    reviews = CourseReview.objects.filter(
        course=course, is_reported=False
    ).select_related("user").order_by("-helpful_count", "-created_at")

    # Rating distribution
    distribution = {i: 0 for i in range(1, 6)}
    total = reviews.count()
    for r in reviews:
        distribution[r.stars] = distribution.get(r.stars, 0) + 1

    avg = sum(r.stars for r in reviews) / total if total > 0 else 0

    return Response({
        "average": round(avg, 1),
        "total": total,
        "distribution": distribution,
        "reviews": CourseReviewSerializer(reviews[:20], many=True).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_review(request, course_id):
    """
    POST /api/v1/community/courses/{course_id}/reviews/

    Submit a review. Only allowed after course completion.
    One review per student per course.
    """
    course = get_object_or_404(Course, id=course_id, deleted_at=None)

    if not Enrollment.objects.filter(
        user=request.user, course=course, status=EnrollmentStatus.COMPLETED
    ).exists():
        return Response(
            {"detail": "Complete this course before leaving a review."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if CourseReview.objects.filter(user=request.user, course=course).exists():
        return Response(
            {"detail": "You have already reviewed this course."},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = CreateReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    review = CourseReview.objects.create(
        user=request.user,
        course=course,
        **serializer.validated_data,
    )
    return Response(
        CourseReviewSerializer(review).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_review_helpful(request, review_id):
    """POST /api/v1/community/reviews/{review_id}/helpful/"""
    review = get_object_or_404(CourseReview, id=review_id)
    CourseReview.objects.filter(id=review_id).update(
        helpful_count=review.helpful_count + 1
    )
    return Response({"helpful_count": review.helpful_count + 1})


# ── Discussions ───────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def lesson_discussions(request, lesson_id):
    """
    GET /api/v1/community/lessons/{lesson_id}/discussions/

    Returns all non-deleted discussion threads for a lesson.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    threads = DiscussionThread.objects.filter(
        lesson=lesson, deleted_at=None
    ).select_related("author").prefetch_related(
        "replies__author"
    ).order_by("-is_pinned", "-created_at")

    return Response(DiscussionThreadSerializer(threads, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_thread(request, lesson_id):
    """
    POST /api/v1/community/lessons/{lesson_id}/discussions/

    Create a new discussion thread. Must be enrolled in the course.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    if not Enrollment.objects.filter(
        user=request.user, course=course
    ).exists() and request.user != course.instructor:
        return Response(
            {"detail": "You must be enrolled to post in discussions."},
            status=status.HTTP_403_FORBIDDEN,
        )

    title = request.data.get("title", "").strip()
    body = request.data.get("body", "").strip()

    if not title or not body:
        return Response(
            {"detail": "Title and body are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    thread = DiscussionThread.objects.create(
        lesson=lesson,
        author=request.user,
        title=title[:300],
        body=body,
    )

    logger.info(
        "Discussion thread created: lesson=%s user=%s",
        lesson_id, request.user.email,
    )

    return Response(
        DiscussionThreadSerializer(thread).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_reply(request, thread_id):
    """
    POST /api/v1/community/threads/{thread_id}/replies/

    Reply to a discussion thread.
    """
    thread = get_object_or_404(DiscussionThread, id=thread_id, deleted_at=None)
    body = request.data.get("body", "").strip()

    if not body:
        return Response(
            {"detail": "Reply body is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    course = thread.lesson.course
    is_instructor = request.user == course.instructor

    reply = DiscussionReply.objects.create(
        thread=thread,
        author=request.user,
        body=body,
        is_instructor_reply=is_instructor,
    )

    # Increment reply count
    DiscussionThread.objects.filter(id=thread_id).update(
        reply_count=thread.reply_count + 1
    )

    # Notify thread author
    if thread.author != request.user:
        from apps.notifications.models import NotificationService
        NotificationService.discussion_reply(thread.author, thread)

    return Response(
        DiscussionReplySerializer(reply).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_thread(request, thread_id):
    """DELETE /api/v1/community/threads/{thread_id}/"""
    thread = get_object_or_404(DiscussionThread, id=thread_id)
    if thread.author != request.user:
        return Response(
            {"detail": "You can only delete your own threads."},
            status=status.HTTP_403_FORBIDDEN,
        )
    thread.soft_delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
