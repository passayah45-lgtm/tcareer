from django.urls import path
from . import views

app_name = "careers"

urlpatterns = [
    # Portfolio - owner
    path("portfolio/me/", views.portfolio_me, name="portfolio-me"),

    # Skills
    path("portfolio/me/skills/", views.skill_list, name="skill-list"),
    path("portfolio/me/skills/sync/", views.skill_sync, name="skill-sync"),
    path("portfolio/me/skills/<uuid:skill_id>/", views.skill_delete, name="skill-delete"),

    # Projects
    path("portfolio/me/projects/", views.project_list, name="project-list"),
    path("portfolio/me/projects/<uuid:project_id>/", views.project_detail, name="project-detail"),
    path("portfolio/me/projects/<uuid:project_id>/media/", views.project_media_create, name="project-media-create"),
    path("portfolio/me/projects/<uuid:project_id>/media/<uuid:media_id>/", views.project_media_detail, name="project-media-detail"),
    path("portfolio/me/ai/review/", views.portfolio_ai_review, name="portfolio-ai-review"),
    path("portfolio/me/ai/review/stream/", views.portfolio_ai_review_stream, name="portfolio-ai-review-stream"),
    path("portfolio/me/ai/project-review/", views.portfolio_ai_project_review, name="portfolio-ai-project-review"),
    path("portfolio/me/ai/github/", views.portfolio_ai_github_review, name="portfolio-ai-github"),
    path("portfolio/me/ai/skills/", views.portfolio_ai_skills, name="portfolio-ai-skills"),
    path("portfolio/me/ai/job-match/", views.portfolio_ai_job_match, name="portfolio-ai-job-match"),
    path("portfolio/me/ai/history/", views.portfolio_ai_history, name="portfolio-ai-history"),
    path("portfolio/me/ai/analytics/", views.portfolio_ai_analytics, name="portfolio-ai-analytics"),

    # Public portfolio
    path("portfolio/<slug:username>/", views.portfolio_public, name="portfolio-public"),
    path("portfolio/<slug:username>/recruiter-view/", views.portfolio_recruiter_view, name="portfolio-recruiter"),
    path("portfolio/<slug:username>/ai/recruiter-summary/", views.portfolio_ai_recruiter_summary, name="portfolio-ai-recruiter-summary"),

    # Resume
    path("resume/me/", views.resume_me, name="resume-me"),
    path("resume/me/generate-pdf/", views.resume_generate_pdf, name="resume-generate-pdf"),
    path("resumes/", views.career_resumes, name="career-resumes"),
    path("resumes/<uuid:resume_id>/", views.career_resume_detail, name="career-resume-detail"),
    path("resumes/<uuid:resume_id>/duplicate/", views.career_resume_duplicate, name="career-resume-duplicate"),
    path("resumes/<uuid:resume_id>/default/", views.career_resume_set_default, name="career-resume-default"),
    path("resumes/<uuid:resume_id>/archive/", views.career_resume_archive, name="career-resume-archive"),
    path("resumes/<uuid:resume_id>/files/", views.career_resume_file_upload, name="career-resume-file-upload"),
    path("resumes/<uuid:resume_id>/download/", views.career_resume_download, name="career-resume-download"),
    path("resumes/<uuid:resume_id>/ai/review/", views.career_resume_ai_review, name="career-resume-ai-review"),
    path("resumes/<uuid:resume_id>/ai/review/stream/", views.career_resume_ai_review_stream, name="career-resume-ai-review-stream"),
    path("resumes/<uuid:resume_id>/ai/skills/", views.career_resume_ai_skills, name="career-resume-ai-skills"),
    path("resumes/<uuid:resume_id>/ai/ats/", views.career_resume_ai_ats, name="career-resume-ai-ats"),
    path("resumes/<uuid:resume_id>/ai/job-match/", views.career_resume_ai_job_match, name="career-resume-ai-job-match"),
    path("resumes/<uuid:resume_id>/ai/compare/", views.career_resume_ai_comparison, name="career-resume-ai-comparison"),
    path("resumes/<uuid:resume_id>/ai/history/", views.career_resume_ai_history, name="career-resume-ai-history"),
    path("resumes/<uuid:resume_id>/ai/analytics/", views.career_resume_ai_analytics, name="career-resume-ai-analytics"),
    path("resumes/<uuid:resume_id>/ai/recruiter-summary/", views.career_resume_ai_recruiter_summary, name="career-resume-ai-recruiter-summary"),
]
