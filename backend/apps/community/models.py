"""
Community models for T-Career.

Includes:
- CourseReview: extended review with text, helpful votes, instructor reply
- DiscussionThread: lesson-level discussion started by a student
- DiscussionReply: reply to a thread, one level deep at MVP

Design decisions:

1. DiscussionThread belongs to a Lesson, not a Course.
   Lesson-level discussions are more specific and useful.
   A student who is stuck on lesson 4 does not want to scroll through
   discussions from all 12 lessons.

2. Soft delete on threads and replies via deleted_at.
   We do not hard delete content because it breaks conversation threads.
   A deleted message shows as [deleted] instead of disappearing.

3. CourseReview.helpful_count is a denormalized counter.
   Avoids a join on every review list request.
   Incremented by a service method, not directly.

4. instructor_reply on CourseReview.
   Instructors can respond to reviews publicly.
   This improves trust and gives instructors a feedback loop.
"""

from django.conf import settings
from django.db import models
from common.models import BaseModel


class CourseReview(BaseModel):
    """
    Extended course rating with review text.
    One review per student per course, only after completion.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_reviews",
        db_index=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    stars = models.PositiveSmallIntegerField(help_text="Rating from 1 to 5.")
    title = models.CharField(max_length=200, blank=True, default="")
    body = models.TextField(blank=True, default="")
    helpful_count = models.PositiveIntegerField(default=0)
    is_reported = models.BooleanField(default=False)
    instructor_reply = models.TextField(blank=True, default="")
    instructor_replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "course_reviews"
        unique_together = [("user", "course")]
        indexes = [
            models.Index(fields=["course", "stars"]),
            models.Index(fields=["course", "helpful_count"]),
        ]
        ordering = ["-helpful_count", "-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.course.title}: {self.stars} stars"


class DiscussionThread(BaseModel):
    """
    A discussion thread attached to a specific lesson.
    Created by enrolled students or the instructor.
    """

    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="discussions",
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discussion_threads",
    )
    title = models.CharField(max_length=300)
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    reply_count = models.PositiveIntegerField(default=0)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "discussion_threads"
        ordering = ["-is_pinned", "-created_at"]
        indexes = [
            models.Index(fields=["lesson", "deleted_at"]),
            models.Index(fields=["lesson", "is_pinned"]),
        ]

    def __str__(self):
        return f"{self.lesson.title}: {self.title}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class DiscussionReply(BaseModel):
    """
    A reply to a discussion thread.
    One level of nesting only at MVP.
    """

    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name="replies",
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discussion_replies",
    )
    body = models.TextField()
    is_instructor_reply = models.BooleanField(
        default=False,
        help_text="True when the instructor of the course replies.",
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "discussion_replies"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread", "deleted_at"]),
        ]

    def __str__(self):
        return f"Reply by {self.author.email} on {self.thread.title}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
