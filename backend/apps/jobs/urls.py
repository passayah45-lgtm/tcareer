from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="job-list"),
    path("recruit/", views.recruiter_waitlist, name="recruiter-waitlist"),
    path("student/dashboard/", views.student_dashboard, name="student-dashboard"),
    path("student/applications/", views.student_applications, name="student-applications"),
    path("student/applications/<uuid:application_id>/", views.student_application_detail, name="student-application-detail"),
    path("student/applications/<uuid:application_id>/submit/", views.application_submit, name="student-application-submit"),
    path("student/saved/", views.saved_jobs, name="student-saved-jobs"),
    path("student/saved/<uuid:job_id>/", views.saved_job_delete, name="student-saved-job-delete"),
    path("student/collections/", views.saved_job_collections, name="student-saved-job-collections"),
    path("student/recently-viewed/", views.recently_viewed_jobs, name="student-recently-viewed-jobs"),
    path("student/alerts/", views.job_alerts, name="student-job-alerts"),
    path("applications/<uuid:application_id>/withdraw/", views.application_withdraw, name="application-withdraw"),
    path("<uuid:job_id>/preview/", views.application_preview, name="application-preview"),
    path("<uuid:job_id>/recommended-click/", views.recommended_job_click, name="recommended-job-click"),
    path("organizations/<uuid:organization_id>/", views.organization_jobs, name="organization-jobs"),
    path("organizations/<uuid:organization_id>/dashboard/", views.recruiter_dashboard, name="recruiter-dashboard"),
    path("organizations/<uuid:organization_id>/pipeline/", views.pipeline_applications, name="pipeline-applications"),
    path("organizations/<uuid:organization_id>/candidates/", views.candidate_search, name="candidate-search"),
    path(
        "organizations/<uuid:organization_id>/candidates/<uuid:candidate_id>/unlock/",
        views.candidate_unlock,
        name="candidate-unlock",
    ),
    path("organizations/<uuid:organization_id>/saved-candidates/", views.saved_candidates, name="saved-candidates"),
    path(
        "organizations/<uuid:organization_id>/saved-candidates/<uuid:candidate_id>/",
        views.saved_candidate_delete,
        name="saved-candidate-delete",
    ),
    path("organizations/<uuid:organization_id>/talent-pools/", views.talent_pools, name="talent-pools"),
    path("organizations/<uuid:organization_id>/interviews/", views.interviews, name="interviews"),
    path(
        "organizations/<uuid:organization_id>/interviews/<uuid:interview_id>/",
        views.interview_update,
        name="interview-update",
    ),
    path(
        "organizations/<uuid:organization_id>/interviews/<uuid:interview_id>/feedback/",
        views.interview_feedback,
        name="interview-feedback",
    ),
    path(
        "organizations/<uuid:organization_id>/interviews/<uuid:interview_id>/scorecard/",
        views.interview_scorecard,
        name="interview-scorecard",
    ),
    path("organizations/<uuid:organization_id>/applications/bulk-stage/", views.bulk_stage_update, name="bulk-stage-update"),
    path("organizations/<uuid:organization_id>/applications/bulk-archive/", views.bulk_archive, name="bulk-archive"),
    path("organizations/<uuid:organization_id>/applications/bulk-reject/", views.bulk_reject, name="bulk-reject"),
    path(
        "organizations/<uuid:organization_id>/applications/<uuid:application_id>/",
        views.application_detail,
        name="application-detail",
    ),
    path(
        "organizations/<uuid:organization_id>/applications/<uuid:application_id>/timeline/",
        views.application_timeline,
        name="application-timeline",
    ),
    path(
        "organizations/<uuid:organization_id>/applications/<uuid:application_id>/stage/",
        views.application_stage_update,
        name="application-stage-update",
    ),
    path(
        "organizations/<uuid:organization_id>/applications/<uuid:application_id>/assign/",
        views.application_assign,
        name="application-assign",
    ),
    path(
        "organizations/<uuid:organization_id>/applications/<uuid:application_id>/notes/",
        views.application_notes,
        name="application-notes",
    ),
    path(
        "organizations/<uuid:organization_id>/<uuid:job_id>/questions/",
        views.organization_job_questions,
        name="organization-job-questions",
    ),
    path(
        "organizations/<uuid:organization_id>/<uuid:job_id>/questions/<uuid:question_id>/",
        views.organization_job_question_detail,
        name="organization-job-question-detail",
    ),
    path(
        "organizations/<uuid:organization_id>/<uuid:job_id>/",
        views.organization_job_update,
        name="organization-job-update",
    ),
    path(
        "organizations/<uuid:organization_id>/<uuid:job_id>/publish/",
        views.organization_job_publish,
        name="organization-job-publish",
    ),
    path(
        "organizations/<uuid:organization_id>/<uuid:job_id>/archive/",
        views.organization_job_archive,
        name="organization-job-archive",
    ),
    path("<uuid:job_id>/apply/", views.apply_to_job, name="job-apply"),
    path("<uuid:job_id>/draft/", views.job_save_draft, name="job-save-draft"),
    path("<uuid:job_id>/", views.job_detail, name="job-detail"),
]
