from django.urls import path
from . import views

app_name = "assessments"

urlpatterns = [
    path("<uuid:course_id>/questions/", views.quiz_questions, name="questions"),
    path("<uuid:course_id>/questions/create/", views.create_question, name="create-question"),
    path("<uuid:course_id>/questions/<uuid:question_id>/", views.manage_question, name="manage-question"),
    path("<uuid:course_id>/submit/", views.submit_quiz, name="submit-quiz"),
    path("<uuid:course_id>/attempts/", views.quiz_attempt_history, name="attempt-history"),
    path("<uuid:course_id>/can-attempt/", views.can_attempt_quiz, name="can-attempt"),
    path("<uuid:course_id>/questions/bulk/", views.bulk_create_questions, name="bulk-create-questions"),
    path("<uuid:course_id>/questions/reorder/", views.reorder_questions, name="reorder-questions"),
    path("<uuid:course_id>/questions/bulk/", views.bulk_create_questions, name="bulk-create-questions"),
    path("<uuid:course_id>/questions/reorder/", views.reorder_questions, name="reorder-questions"),
    path("<uuid:course_id>/rate/", views.submit_rating, name="submit-rating"),
    path("<uuid:course_id>/ratings/", views.course_ratings, name="course-ratings"),
]


