from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("create/", views.course_create, name="course-create"),
    path("mine/", views.instructor_courses, name="instructor-courses"),
    path("author-analytics/", views.author_analytics, name="author-analytics"),
    path("quality-dashboard/", views.content_quality_dashboard, name="content-quality-dashboard"),
    path("reviewer/dashboard/", views.reviewer_dashboard, name="reviewer-dashboard"),
    path("reviewer/queue/", views.reviewer_queue, name="reviewer-queue"),
    path(
        "reviewer/assignments/<uuid:assignment_id>/reassign/",
        views.reviewer_assignment_reassign,
        name="reviewer-assignment-reassign",
    ),
    path(
        "reviewer/assignments/<uuid:assignment_id>/response/",
        views.reviewer_assignment_response,
        name="reviewer-assignment-response",
    ),
    path("academic-audit/", views.academic_audit, name="academic-audit"),
    path("resources/", views.resource_library, name="resource-library"),
    path("resources/upload-url/", views.resource_upload_url, name="resource-upload-url"),
    path("resources/<uuid:resource_id>/review/", views.resource_review, name="resource-review"),
    path("resources/<uuid:resource_id>/scan/", views.resource_scan, name="resource-scan"),
    path(
        "resources/<uuid:resource_id>/download/", views.resource_download, name="resource-download"
    ),
    path("enrollments/", views.my_enrollments, name="my-enrollments"),
    path("webhooks/mediaconvert/", views.mediaconvert_webhook_v2, name="mediaconvert-webhook"),
    path("<uuid:course_id>/update/", views.course_update, name="course-update"),
    path("<uuid:course_id>/publish/", views.course_publish, name="course-publish"),
    path("<uuid:course_id>/delete/", views.course_delete, name="course-delete"),
    path("<uuid:course_id>/quality/", views.course_quality, name="course-quality"),
    path(
        "<uuid:course_id>/publish-blockers/",
        views.course_publish_blockers,
        name="course-publish-blockers",
    ),
    path("<uuid:course_id>/reviews/", views.course_reviews, name="course-reviews"),
    path(
        "<uuid:course_id>/reviews/submit/", views.submit_course_review, name="submit-course-review"
    ),
    path("<uuid:course_id>/reviews/decision/", views.review_course, name="review-course"),
    path("<uuid:course_id>/project/", views.course_project, name="course-project"),
    path(
        "<uuid:course_id>/project/review/",
        views.review_course_project,
        name="review-course-project",
    ),
    path(
        "<uuid:course_id>/project/structured-review/",
        views.structured_course_project_review,
        name="structured-course-project-review",
    ),
    path("<uuid:course_id>/lessons/", views.lesson_list, name="lesson-list"),
    path("<uuid:course_id>/lessons/create/", views.lesson_create, name="lesson-create"),
    path("<uuid:course_id>/lessons/reorder/", views.lesson_reorder, name="lesson-reorder"),
    path("<uuid:course_id>/lessons/<uuid:lesson_id>/", views.lesson_detail, name="lesson-detail"),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/update/",
        views.lesson_update,
        name="lesson-update",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/review/",
        views.lesson_review,
        name="lesson-review",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/structured-review/",
        views.structured_lesson_review,
        name="structured-lesson-review",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/versions/",
        views.lesson_versions,
        name="lesson-versions",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/versions/compare/",
        views.lesson_version_compare,
        name="lesson-version-compare",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/versions/<uuid:version_id>/rollback/",
        views.lesson_version_rollback,
        name="lesson-version-rollback",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/upload-url/",
        views.lesson_upload_url,
        name="lesson-upload-url",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/confirm-upload/",
        views.lesson_confirm_upload,
        name="lesson-confirm-upload",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/progress/",
        views.update_progress,
        name="update-progress",
    ),
    path(
        "<uuid:course_id>/lessons/<uuid:lesson_id>/complete/",
        views.complete_text_lesson,
        name="complete-text-lesson",
    ),
    path("lessons/<uuid:lesson_id>/", views.lesson_inline_update, name="lesson-inline-update"),
    path("<uuid:course_id>/enroll/", views.enroll, name="enroll"),
    path("<uuid:course_id>/progress/", views.course_progress, name="course-progress"),
    path("", views.course_list, name="course-list"),
    path("<slug:slug>/", views.course_detail, name="course-detail"),
]
