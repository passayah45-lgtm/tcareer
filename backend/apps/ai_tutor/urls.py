from django.urls import path
from . import views

app_name = "ai_tutor"

urlpatterns = [
    path("ask/", views.ask_tutor, name="ask"),
    path("history/<uuid:lesson_id>/", views.conversation_history, name="history"),
    path("history/<uuid:lesson_id>/clear/", views.clear_conversation, name="clear"),
]
