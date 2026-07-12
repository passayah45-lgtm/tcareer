"""
Views for the careers domain.

All views follow the same pattern as the rest of the codebase:
- Function-based views with @api_view decorator
- Thin controllers that delegate logic to services
- Consistent error responses via the standard renderer
"""

import logging
import json
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.users.models import User
from apps.ai_platform.services import AIService
from apps.analytics.services import AnalyticsService
from apps.organizations.models import CandidateProfileUnlock, Organization
from common.candidate_visibility import CandidateVisibilityService
from common.entitlements import EntitlementService
from common.exceptions import PermissionError
from common.privacy import PrivacyService
from common.storage import generate_private_download_url
from common.uploads import UploadValidationService
from common.audit import AuditService
from common.throttles import ResumeDownloadRateThrottle
from .models import (
    CareerResume,
    Portfolio,
    PortfolioAIReview,
    PortfolioAIReviewType,
    PortfolioSkill,
    PortfolioProject,
    PortfolioProjectMedia,
    Resume,
    ResumeAnalytics,
    ResumeAIReview,
    ResumeAIReviewType,
    ResumeFile,
    ResumeVersion,
    VisibilityChoice,
)
from .serializers import (
    PortfolioSerializer, PortfolioUpdateSerializer,
    PortfolioSkillSerializer, PortfolioSkillCreateSerializer,
    PortfolioProjectSerializer,
    PortfolioProjectMediaSerializer,
    PortfolioAIJobMatchRequestSerializer, PortfolioAIProjectRequestSerializer,
    PortfolioAIRecruiterSummarySerializer, PortfolioAIReviewSerializer,
    PublicPortfolioSerializer, RecruiterPortfolioSerializer,
    ResumeSerializer, ResumeUpdateSerializer,
    CareerResumeSerializer, CareerResumeWriteSerializer, ResumeFileSerializer,
    ResumeAIComparisonRequestSerializer, ResumeAIJobMatchRequestSerializer,
    ResumeAIRecruiterSummarySerializer, ResumeAIReviewSerializer,
)
from .services import PortfolioIntelligenceService, PortfolioService, ResumeIntelligenceService, ResumeService

logger = logging.getLogger(__name__)


def _success(data=None, status_code=status.HTTP_200_OK, meta=None):
    return Response(
        {
            "success": True,
            "data": data,
            "errors": {},
            "meta": meta or {},
        },
        status=status_code,
    )


# ── Portfolio - Owner endpoints ────────────────────────────────────────────────

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def portfolio_me(request):
    """Get or update the authenticated student's portfolio."""
    portfolio = PortfolioService.get_or_create(request.user)

    if request.method == "GET":
        serializer = PortfolioSerializer(portfolio)
        return _success(serializer.data)

    serializer = PortfolioUpdateSerializer(portfolio, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return _success(PortfolioSerializer(portfolio).data)


# ── Skills ─────────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def skill_list(request):
    """List or add skills on the authenticated student's portfolio."""
    portfolio = PortfolioService.get_or_create(request.user)

    if request.method == "GET":
        serializer = PortfolioSkillSerializer(portfolio.skills.all(), many=True)
        return _success(serializer.data)

    serializer = PortfolioSkillCreateSerializer(
        data=request.data,
        context={"portfolio": portfolio},
    )
    serializer.is_valid(raise_exception=True)
    position = portfolio.skills.count()
    skill = PortfolioSkill.objects.create(
        portfolio=portfolio,
        position=position,
        **serializer.validated_data,
    )
    return _success(PortfolioSkillSerializer(skill).data, status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def skill_delete(request, skill_id):
    """Remove a skill from the authenticated student's portfolio."""
    portfolio = PortfolioService.get_or_create(request.user)
    skill = get_object_or_404(PortfolioSkill, id=skill_id, portfolio=portfolio)
    skill.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def skill_sync(request):
    """
    Auto-import skills from completed courses and enrolled career tracks.
    Idempotent - safe to call multiple times.
    """
    portfolio = PortfolioService.get_or_create(request.user)
    course_result = PortfolioService.sync_skills_from_courses(portfolio)
    track_result = PortfolioService.sync_skills_from_tracks(portfolio)
    return _success({
        "from_courses": course_result,
        "from_tracks": track_result,
        "total_added": course_result["added"] + track_result["added"],
    })


# ── Projects ───────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def project_list(request):
    """List or create projects on the authenticated student's portfolio."""
    portfolio = PortfolioService.get_or_create(request.user)

    if request.method == "GET":
        serializer = PortfolioProjectSerializer(portfolio.projects.all(), many=True, context={"request": request})
        return _success(serializer.data)

    serializer = PortfolioProjectSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    position = portfolio.projects.count()
    project = PortfolioProject.objects.create(
        portfolio=portfolio,
        position=position,
        **serializer.validated_data,
    )
    AnalyticsService.track(name="portfolio_project_created", user=request.user, target=project)
    return _success(PortfolioProjectSerializer(project, context={"request": request}).data, status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def project_detail(request, project_id):
    """Get, update, or delete a specific project."""
    portfolio = PortfolioService.get_or_create(request.user)
    project = get_object_or_404(PortfolioProject, id=project_id, portfolio=portfolio)

    if request.method == "GET":
        return _success(PortfolioProjectSerializer(project, context={"request": request}).data)

    if request.method == "PATCH":
        serializer = PortfolioProjectSerializer(project, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AnalyticsService.track(name="portfolio_project_updated", user=request.user, target=project)
        return _success(PortfolioProjectSerializer(project, context={"request": request}).data)

    project.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def project_media_create(request, project_id):
    portfolio = PortfolioService.get_or_create(request.user)
    project = get_object_or_404(PortfolioProject, id=project_id, portfolio=portfolio)
    data = request.data.copy()
    uploaded = request.FILES.get("file")
    if uploaded:
        UploadValidationService.validate_metadata(
            file_name=uploaded.name,
            content_type=uploaded.content_type,
            file_size=uploaded.size,
            allowed_extensions={".png", ".jpg", ".jpeg", ".webp"},
            allowed_mime_types={"image/png", "image/jpeg", "image/webp"},
            max_size_bytes=8 * 1024 * 1024,
        )
        data["file_name"] = uploaded.name
        data["content_type"] = uploaded.content_type
        data["file_size"] = uploaded.size
        data["media_type"] = data.get("media_type") or PortfolioProjectMedia.MediaType.IMAGE
    if not uploaded and not data.get("url"):
        return Response({"detail": "Provide either a file upload or media URL."}, status=status.HTTP_400_BAD_REQUEST)
    serializer = PortfolioProjectMediaSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    media = PortfolioProjectMedia.objects.create(project=project, file=uploaded, **serializer.validated_data)
    AnalyticsService.track(name="portfolio_project_updated", user=request.user, target=project, metadata={"media_id": str(media.id)})
    return _success(PortfolioProjectMediaSerializer(media).data, status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def project_media_detail(request, project_id, media_id):
    portfolio = PortfolioService.get_or_create(request.user)
    project = get_object_or_404(PortfolioProject, id=project_id, portfolio=portfolio)
    media = get_object_or_404(PortfolioProjectMedia, id=media_id, project=project)
    if request.method == "PATCH":
        serializer = PortfolioProjectMediaSerializer(media, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AnalyticsService.track(name="portfolio_project_updated", user=request.user, target=project, metadata={"media_id": str(media.id)})
        return _success(PortfolioProjectMediaSerializer(media).data)
    media.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Public portfolio ───────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def portfolio_public(request, username):
    """
    Public portfolio page. No authentication required.
    Returns 404 for private portfolios.
    Returns limited data for unlisted portfolios (no search indexing).
    """
    user = get_object_or_404(User, username=username, is_active=True)

    try:
        portfolio = user.portfolio
    except Portfolio.DoesNotExist:
        return Response(
            {"detail": "This user has not set up a portfolio yet."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if portfolio.visibility == VisibilityChoice.PRIVATE:
        # Only the owner can see their private portfolio
        if not request.user.is_authenticated or request.user != user:
            return Response(
                {"detail": "This portfolio is private."},
                status=status.HTTP_404_NOT_FOUND,
            )

    # Increment view count for non-owners
    if not request.user.is_authenticated or request.user != user:
        PortfolioService.increment_profile_views(portfolio)

    serializer = PublicPortfolioSerializer(portfolio)
    AnalyticsService.track(name="portfolio_viewed", user=request.user if request.user.is_authenticated else None, target=user)
    return _success(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_recruiter_view(request, username):
    """
    Extended portfolio view for authenticated recruiters.
    Adds profile completeness score and aggregate counts.
    Requires the viewer to be authenticated.
    Private portfolios are not accessible even to recruiters.
    """
    user = get_object_or_404(User, username=username, is_active=True)
    organization_id = request.query_params.get("organization_id") or request.data.get("organization_id")
    if not organization_id:
        raise PermissionError("organization_id is required.")
    organization = get_object_or_404(Organization, id=organization_id)

    try:
        portfolio = user.portfolio
    except Portfolio.DoesNotExist:
        return Response(
            {"detail": "This user has not set up a portfolio yet."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if portfolio.visibility == VisibilityChoice.PRIVATE:
        return Response(
            {"detail": "This portfolio is private."},
            status=status.HTTP_404_NOT_FOUND,
        )
    if not CandidateVisibilityService.can_view_portfolio(request.user, user, organization=organization):
        return Response(
            {"detail": "This portfolio is hidden from recruiters."},
            status=status.HTTP_404_NOT_FOUND,
        )

    AnalyticsService.track(
        name="recruiter_viewed_candidate",
        user=request.user,
        organization=organization,
        target=user,
        metadata={"candidate_user_id": str(user.id)},
    )
    serializer = RecruiterPortfolioSerializer(portfolio)
    return _success(serializer.data)


# ── Resume ─────────────────────────────────────────────────────────────────────

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def resume_me(request):
    """Get or update the authenticated student's resume."""
    resume = ResumeService.get_or_create(request.user)

    if request.method == "GET":
        serializer = ResumeSerializer(resume)
        return _success(serializer.data)

    serializer = ResumeUpdateSerializer(resume, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return _success(ResumeSerializer(resume).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resume_generate_pdf(request):
    """
    Trigger resume PDF generation.
    Generates the PDF, uploads to S3, and returns the download URL.
    This is a synchronous operation. For large resumes, move to a Celery task.
    """
    resume = ResumeService.get_or_create(request.user)
    pdf_url = ResumeService.generate_pdf(resume)

    if not pdf_url:
        return Response(
            {"detail": "PDF generation failed. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return _success({
        "pdf_url": pdf_url,
        "generated_at": resume.last_generated_at,
    })


def _resume_snapshot(resume: CareerResume):
    return {
        "title": resume.title,
        "summary": resume.summary,
        "target_role": resume.target_role,
        "education": resume.education,
        "experience": resume.experience,
        "skills": resume.skills,
        "is_default": resume.is_default,
    }


def _create_resume_version(resume: CareerResume, summary=""):
    latest = resume.versions.order_by("-version_number").first()
    version = (latest.version_number + 1) if latest else 1
    return ResumeVersion.objects.create(
        resume=resume,
        version_number=version,
        snapshot=_resume_snapshot(resume),
        change_summary=summary,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def career_resumes(request):
    if request.method == "GET":
        resumes = CareerResume.objects.filter(user=request.user).prefetch_related("files", "versions", "analytics", "ai_reviews")
        return _success(CareerResumeSerializer(resumes, many=True).data)
    serializer = CareerResumeWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    is_default = serializer.validated_data.get("is_default", False) or not CareerResume.objects.filter(user=request.user, is_archived=False).exists()
    resume = CareerResume.objects.create(user=request.user, **{**serializer.validated_data, "is_default": is_default})
    _create_resume_version(resume, "Resume created.")
    AnalyticsService.track(name="resume_created", user=request.user, target=resume)
    return _success(CareerResumeSerializer(resume).data, status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def career_resume_detail(request, resume_id):
    resume = get_object_or_404(CareerResume.objects.prefetch_related("files", "versions", "analytics", "ai_reviews"), id=resume_id, user=request.user)
    if request.method == "GET":
        return _success(CareerResumeSerializer(resume).data)
    serializer = CareerResumeWriteSerializer(resume, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    _create_resume_version(resume, "Resume updated.")
    AnalyticsService.track(name="resume_updated", user=request.user, target=resume)
    return _success(CareerResumeSerializer(resume).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_duplicate(request, resume_id):
    resume = get_object_or_404(CareerResume, id=resume_id, user=request.user)
    duplicate = CareerResume.objects.create(
        user=request.user,
        title=f"{resume.title} Copy",
        summary=resume.summary,
        target_role=resume.target_role,
        education=resume.education,
        experience=resume.experience,
        skills=resume.skills,
        is_default=False,
    )
    _create_resume_version(duplicate, "Duplicated from another resume.")
    AnalyticsService.track(name="resume_created", user=request.user, target=duplicate, metadata={"source_resume_id": str(resume.id)})
    return _success(CareerResumeSerializer(duplicate).data, status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_set_default(request, resume_id):
    resume = get_object_or_404(CareerResume, id=resume_id, user=request.user)
    resume.is_default = True
    resume.is_archived = False
    resume.save(update_fields=["is_default", "is_archived", "updated_at"])
    return _success(CareerResumeSerializer(resume).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_archive(request, resume_id):
    resume = get_object_or_404(CareerResume, id=resume_id, user=request.user)
    resume.is_archived = True
    if resume.is_default:
        resume.is_default = False
    resume.save(update_fields=["is_archived", "is_default", "updated_at"])
    if not CareerResume.objects.filter(user=request.user, is_default=True, is_archived=False).exists():
        next_resume = CareerResume.objects.filter(user=request.user, is_archived=False).exclude(id=resume.id).first()
        if next_resume:
            next_resume.is_default = True
            next_resume.save(update_fields=["is_default", "updated_at"])
    return _success(CareerResumeSerializer(resume).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_file_upload(request, resume_id):
    resume = get_object_or_404(CareerResume, id=resume_id, user=request.user)
    data = request.data.copy()
    uploaded = request.FILES.get("file")
    if uploaded:
        UploadValidationService.validate_metadata(
            file_name=uploaded.name,
            content_type=uploaded.content_type,
            file_size=uploaded.size,
            allowed_extensions={".pdf", ".doc", ".docx"},
            allowed_mime_types={
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            max_size_bytes=5 * 1024 * 1024,
        )
        data["file_name"] = uploaded.name
        data["content_type"] = uploaded.content_type
        data["file_size"] = uploaded.size
        data["is_private"] = True
    if not uploaded and not data.get("file_url"):
        return Response({"detail": "Provide either a private file upload or compatible file_url."}, status=status.HTTP_400_BAD_REQUEST)
    serializer = ResumeFileSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    file = ResumeFile.objects.create(resume=resume, uploaded_by=request.user, file=uploaded, **serializer.validated_data)
    return _success(ResumeFileSerializer(file).data, status.HTTP_201_CREATED)


def _can_access_resume(request, resume):
    if request.user == resume.user:
        return True
    if getattr(request.user, "role", "") in {"platform_admin", "super_admin", "admin"} or request.user.is_staff:
        return True
    organization_id = request.query_params.get("organization_id")
    if organization_id:
        organization = get_object_or_404(Organization, id=organization_id)
        return CandidateVisibilityService.can_view_resume(request.user, resume.user, organization=organization)
    return False


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ResumeDownloadRateThrottle])
def career_resume_download(request, resume_id):
    resume = get_object_or_404(CareerResume, id=resume_id)
    if not _can_access_resume(request, resume):
        logger.warning(
            "resume_download_denied",
            extra={"actor_id": str(request.user.id), "resume_id": str(resume.id), "owner_id": str(resume.user_id)},
        )
        raise PermissionError("You cannot access this resume file.")
    file = resume.files.order_by("-created_at").first()
    ResumeAnalytics.objects.create(resume=resume, event_type=ResumeAnalytics.EventType.DOWNLOADED, actor=request.user)
    AnalyticsService.track(name="resume_downloaded", user=request.user, target=resume)
    AuditService.record(
        actor=request.user,
        action="resume_downloaded",
        target=resume,
        request=request,
        metadata={"resume_owner_id": str(resume.user_id)},
    )
    logger.info(
        "resume_downloaded",
        extra={"actor_id": str(request.user.id), "resume_id": str(resume.id), "owner_id": str(resume.user_id)},
    )
    download_url = ""
    file_name = ""
    if file:
        download_url = generate_private_download_url(file.file, fallback_url=file.file_url)
        file_name = file.file_name
    return _success({
        "resume_id": str(resume.id),
        "download_url": download_url,
        "file_url": download_url,
        "file_name": file_name,
        "download_tracked": True,
    })


def _owned_resume(user, resume_id):
    return get_object_or_404(CareerResume.objects.prefetch_related("ai_reviews"), id=resume_id, user=user)


def _resume_ai_response(review):
    return _success(ResumeAIReviewSerializer(review).data, status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_ai_review(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    review = ResumeIntelligenceService.create_review(user=request.user, resume=resume, review_type=ResumeAIReviewType.REVIEW)
    return _resume_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_ai_skills(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    review = ResumeIntelligenceService.create_review(user=request.user, resume=resume, review_type=ResumeAIReviewType.SKILL_EXTRACTION)
    return _resume_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_ai_ats(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    review = ResumeIntelligenceService.create_review(user=request.user, resume=resume, review_type=ResumeAIReviewType.ATS)
    return _resume_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_ai_job_match(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    serializer = ResumeAIJobMatchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    from apps.jobs.models import JobListing

    job = get_object_or_404(JobListing, id=serializer.validated_data["job_id"], is_active=True)
    review = ResumeIntelligenceService.create_review(user=request.user, resume=resume, review_type=ResumeAIReviewType.JOB_MATCH, job=job)
    return _resume_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_ai_comparison(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    serializer = ResumeAIComparisonRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    comparison_resume = get_object_or_404(CareerResume, id=serializer.validated_data["comparison_resume_id"], user=request.user)
    review = ResumeIntelligenceService.create_review(
        user=request.user,
        resume=resume,
        review_type=ResumeAIReviewType.COMPARISON,
        comparison_resume=comparison_resume,
    )
    return _resume_ai_response(review)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def career_resume_ai_history(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    reviews = resume.ai_reviews.select_related("job", "comparison_resume").order_by("-created_at")
    return _success(ResumeAIReviewSerializer(reviews, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def career_resume_ai_analytics(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    return _success(ResumeIntelligenceService.analytics(request.user, resume=resume))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def career_resume_ai_review_stream(request, resume_id):
    resume = _owned_resume(request.user, resume_id)
    input_text = ResumeIntelligenceService.resume_text(resume)

    def event_stream():
        for event in AIService.stream_text(
            user=request.user,
            feature="resume_review",
            input_text=f"Stream a concise resume review progress summary for:\n{input_text}",
            metadata={"resume_id": str(resume.id), "review_type": "review_stream"},
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def career_resume_ai_recruiter_summary(request, resume_id):
    resume = get_object_or_404(CareerResume, id=resume_id)
    organization_id = request.query_params.get("organization_id")
    organization = get_object_or_404(Organization, id=organization_id) if organization_id else None
    if not CandidateVisibilityService.can_view_resume(request.user, resume.user, organization=organization):
        raise PermissionError("You cannot view this resume intelligence summary.")
    latest = ResumeAIReview.objects.filter(resume=resume).order_by("-created_at").first()
    if not latest:
        return _success(None)
    ResumeAnalytics.objects.create(resume=resume, event_type=ResumeAnalytics.EventType.VIEWED_BY_RECRUITER, actor=request.user, metadata={"ai_summary": True})
    return _success(ResumeAIRecruiterSummarySerializer(latest).data)


def _portfolio_ai_response(review):
    return _success(PortfolioAIReviewSerializer(review).data, status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portfolio_ai_review(request):
    portfolio = PortfolioService.get_or_create(request.user)
    review = PortfolioIntelligenceService.create_portfolio_review(user=request.user, portfolio=portfolio, review_type=PortfolioAIReviewType.PORTFOLIO_REVIEW)
    return _portfolio_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portfolio_ai_project_review(request):
    portfolio = PortfolioService.get_or_create(request.user)
    serializer = PortfolioAIProjectRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    project = get_object_or_404(PortfolioProject, id=serializer.validated_data["project_id"], portfolio=portfolio)
    review = PortfolioIntelligenceService.create_portfolio_review(user=request.user, portfolio=portfolio, project=project, review_type=PortfolioAIReviewType.PROJECT_REVIEW)
    return _portfolio_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portfolio_ai_github_review(request):
    portfolio = PortfolioService.get_or_create(request.user)
    project = None
    project_id = request.data.get("project_id")
    if project_id:
        project = get_object_or_404(PortfolioProject, id=project_id, portfolio=portfolio)
    review = PortfolioIntelligenceService.create_portfolio_review(user=request.user, portfolio=portfolio, project=project, review_type=PortfolioAIReviewType.GITHUB_REVIEW)
    return _portfolio_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portfolio_ai_skills(request):
    portfolio = PortfolioService.get_or_create(request.user)
    review = PortfolioIntelligenceService.create_portfolio_review(user=request.user, portfolio=portfolio, review_type=PortfolioAIReviewType.SKILL_EXTRACTION)
    return _portfolio_ai_response(review)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portfolio_ai_job_match(request):
    portfolio = PortfolioService.get_or_create(request.user)
    serializer = PortfolioAIJobMatchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    from apps.jobs.models import JobListing

    job = get_object_or_404(JobListing, id=serializer.validated_data["job_id"], is_active=True)
    review = PortfolioIntelligenceService.create_portfolio_review(user=request.user, portfolio=portfolio, job=job, review_type=PortfolioAIReviewType.JOB_MATCH)
    return _portfolio_ai_response(review)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_ai_history(request):
    portfolio = PortfolioService.get_or_create(request.user)
    reviews = portfolio.ai_reviews.select_related("project", "job").order_by("-created_at")
    return _success(PortfolioAIReviewSerializer(reviews, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_ai_analytics(request):
    portfolio = PortfolioService.get_or_create(request.user)
    return _success(PortfolioIntelligenceService.portfolio_analytics(request.user, portfolio=portfolio))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def portfolio_ai_review_stream(request):
    portfolio = PortfolioService.get_or_create(request.user)
    input_text = PortfolioIntelligenceService.portfolio_text(portfolio)

    def event_stream():
        for event in AIService.stream_text(
            user=request.user,
            feature="portfolio_review",
            input_text=f"Stream a concise portfolio review progress summary for:\n{input_text}",
            metadata={"portfolio_id": str(portfolio.id), "review_type": "portfolio_stream"},
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def portfolio_ai_recruiter_summary(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    organization_id = request.query_params.get("organization_id")
    organization = get_object_or_404(Organization, id=organization_id) if organization_id else None
    try:
        portfolio = user.portfolio
    except Portfolio.DoesNotExist:
        return Response({"detail": "This user has not set up a portfolio yet."}, status=status.HTTP_404_NOT_FOUND)
    if not CandidateVisibilityService.can_view_portfolio(request.user, user, organization=organization):
        raise PermissionError("You cannot view this portfolio intelligence summary.")
    latest = PortfolioAIReview.objects.filter(portfolio=portfolio).order_by("-created_at").first()
    if not latest:
        return _success(None)
    AnalyticsService.track(name="recruiter_viewed_portfolio_ai_summary", user=request.user, organization=organization, target=user)
    return _success(PortfolioAIRecruiterSummarySerializer(latest).data)
