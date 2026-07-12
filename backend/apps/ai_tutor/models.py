"""
AI Tutor conversation models.

Design decisions:

1. TutorConversation belongs to a user and a lesson.
   Each lesson gets its own conversation thread.
   This keeps context focused on the current topic.

2. TutorMessage stores role (user/assistant) and content.
   The last N messages are sent to OpenAI as the conversation history.
   N is configurable via MAX_HISTORY_MESSAGES.

3. We store token counts for cost monitoring.
   At scale, per-user daily token limits are enforced via Redis.

4. Conversations are soft-never-deleted.
   Students may want to review past explanations.
"""

from django.conf import settings
from django.db import models
from common.models import BaseModel


class TutorConversation(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_conversations",
        db_index=True,
    )
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="tutor_conversations",
        db_index=True,
    )
    total_tokens_used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "tutor_conversations"
        unique_together = [("user", "lesson")]
        indexes = [
            models.Index(fields=["user", "lesson"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.lesson.title}"


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class TutorMessage(BaseModel):
    conversation = models.ForeignKey(
        TutorConversation,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    role = models.CharField(max_length=10, choices=MessageRole.choices)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "tutor_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
