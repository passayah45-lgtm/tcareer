from django.urls import path
from . import views

app_name = "community"

urlpatterns = [
    path("courses/<uuid:course_id>/reviews/", views.course_reviews, name="course-reviews"),
    path("courses/<uuid:course_id>/reviews/create/", views.create_review, name="create-review"),
    path("reviews/<uuid:review_id>/helpful/", views.mark_review_helpful, name="review-helpful"),
    path("lessons/<uuid:lesson_id>/discussions/", views.lesson_discussions, name="lesson-discussions"),
    path("lessons/<uuid:lesson_id>/discussions/create/", views.create_thread, name="create-thread"),
    path("threads/<uuid:thread_id>/replies/", views.create_reply, name="create-reply"),
    path("threads/<uuid:thread_id>/delete/", views.delete_thread, name="delete-thread"),
]
