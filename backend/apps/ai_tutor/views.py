import json
import logging
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers

from apps.courses.models import Lesson
from apps.analytics.services import AnalyticsService
from apps.ai_platform.models import AIFeature
from apps.ai_platform.services import AIService
from common.entitlements import EntitlementService
from .models import TutorConversation, TutorMessage, MessageRole

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 10
MAX_DAILY_QUESTIONS = 20
DAILY_LIMIT_CACHE_KEY = "tutor_daily:{user_id}:{date}"


def check_daily_limit(user_id: str) -> bool:
    """Returns True if user is within daily limit."""
    from django.core.cache import cache
    from django.utils import timezone
    key = DAILY_LIMIT_CACHE_KEY.format(
        user_id=user_id,
        date=timezone.now().date(),
    )
    count = cache.get(key, 0)
    if count >= MAX_DAILY_QUESTIONS:
        return False
    cache.set(key, count + 1, timeout=60 * 60 * 24)
    return True


def get_conversation_history(conversation: TutorConversation) -> list:
    """Returns the last N messages formatted for OpenAI."""
    messages = conversation.messages.order_by("-created_at")[:MAX_HISTORY_MESSAGES]
    return [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(list(messages))
    ]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ask_tutor(request):
    """
    POST /api/v1/ai/ask/

    Streams an AI tutor response using SSE.
    Stores conversation history for multi-turn context.

    Request: { "lesson_id": "uuid", "question": "What is a variable?" }
    """
    lesson_id = request.data.get("lesson_id")
    question = request.data.get("question", "").strip()

    if not lesson_id or not question:
        return Response({"detail": "lesson_id and question are required."}, status=400)

    if len(question) > 1000:
        return Response({"detail": "Question must be under 1000 characters."}, status=400)

    if not check_daily_limit(str(request.user.id)):
        return Response(
            {"detail": f"You have reached the daily limit of {MAX_DAILY_QUESTIONS} questions."},
            status=429,
        )

    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not EntitlementService.can_use_ai_tutor(request.user, lesson.course):
        return Response({"detail": "AI tutor access requires an active entitlement."}, status=403)
    AnalyticsService.track(
        name="ai_tutor_used",
        user=request.user,
        target=lesson,
        metadata={"course_id": str(lesson.course_id)},
    )

    conversation, _ = TutorConversation.objects.get_or_create(
        user=request.user,
        lesson=lesson,
    )

    history = get_conversation_history(conversation)

    TutorMessage.objects.create(
        conversation=conversation,
        role=MessageRole.USER,
        content=question,
    )

    system_prompt = f"""You are an AI tutor for T-Career, an online learning platform.
The student is currently studying: {lesson.course.title if hasattr(lesson, 'course') else 'a course'}.
The current lesson is: {lesson.title}.

Your role is to help students understand concepts from their lessons.
Keep your answers clear, concise, and focused on the lesson topic.
Use simple examples. Do not write code unless the student asks.
If a question is unrelated to the lesson, gently redirect the student.
"""

    def stream_response():
        try:
            result = AIService.generate_text(
                user=request.user,
                course=lesson.course,
                feature=AIFeature.COURSE_TUTOR,
                input_text=question,
                variables={
                    "lesson_title": lesson.title,
                    "course_title": lesson.course.title,
                    "history": history,
                    "system_prompt": system_prompt,
                },
            )
            full_response = result["text"]
            yield f"data: {json.dumps({'chunk': full_response})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

            TutorMessage.objects.create(
                conversation=conversation,
                role=MessageRole.ASSISTANT,
                content=full_response,
            )

        except Exception as exc:
            logger.error("AI tutor error for user %s: %s", request.user.email, exc)
            yield f"data: {json.dumps({'error': 'The AI tutor is unavailable. Please try again.'})}\n\n"

    response = StreamingHttpResponse(
        stream_response(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_history(request, lesson_id):
    """
    GET /api/v1/ai/history/{lesson_id}/

    Returns the conversation history for a lesson.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)

    try:
        conversation = TutorConversation.objects.get(
            user=request.user, lesson=lesson
        )
        messages = conversation.messages.order_by("created_at")
        return Response([
            {"role": msg.role, "content": msg.content, "created_at": msg.created_at}
            for msg in messages
        ])
    except TutorConversation.DoesNotExist:
        return Response([])


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def clear_conversation(request, lesson_id):
    """
    DELETE /api/v1/ai/history/{lesson_id}/

    Clears conversation history for a lesson so the student can start fresh.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    TutorConversation.objects.filter(
        user=request.user, lesson=lesson
    ).delete()
    return Response({"detail": "Conversation cleared."})
