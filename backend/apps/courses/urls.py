from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("create/", views.course_create, name="course-create"),
    path("mine/", views.instructor_courses, name="instructor-courses"),
    path("enrollments/", views.my_enrollments, name="my-enrollments"),
    path("webhooks/mediaconvert/", views.mediaconvert_webhook_v2, name="mediaconvert-webhook"),
    path("<uuid:course_id>/update/", views.course_update, name="course-update"),
    path("<uuid:course_id>/publish/", views.course_publish, name="course-publish"),
    path("<uuid:course_id>/delete/", views.course_delete, name="course-delete"),
    path("<uuid:course_id>/lessons/", views.lesson_list, name="lesson-list"),
    path("<uuid:course_id>/lessons/create/", views.lesson_create, name="lesson-create"),
    path("<uuid:course_id>/lessons/reorder/", views.lesson_reorder, name="lesson-reorder"),
    path("<uuid:course_id>/lessons/<uuid:lesson_id>/", views.lesson_detail, name="lesson-detail"),
    path("<uuid:course_id>/lessons/<uuid:lesson_id>/update/", views.lesson_update, name="lesson-update"),
    path("<uuid:course_id>/lessons/<uuid:lesson_id>/upload-url/", views.lesson_upload_url, name="lesson-upload-url"),
    path("<uuid:course_id>/lessons/<uuid:lesson_id>/confirm-upload/", views.lesson_confirm_upload, name="lesson-confirm-upload"),
    path("<uuid:course_id>/lessons/<uuid:lesson_id>/progress/", views.update_progress, name="update-progress"),
    path("<uuid:course_id>/lessons/<uuid:lesson_id>/complete/", views.complete_text_lesson, name="complete-text-lesson"),
    path("lessons/<uuid:lesson_id>/", views.lesson_inline_update, name="lesson-inline-update"),
    path("<uuid:course_id>/enroll/", views.enroll, name="enroll"),
    path("<uuid:course_id>/progress/", views.course_progress, name="course-progress"),
    path("", views.course_list, name="course-list"),
    path("<slug:slug>/", views.course_detail, name="course-detail"),
]
