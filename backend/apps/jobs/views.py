import logging
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers

from apps.analytics.services import AnalyticsService
from apps.analytics.models import AnalyticsEvent
from apps.audit.models import AuditLog
from apps.careers.models import CareerResume, Portfolio, ResumeAnalytics, VisibilityChoice
from apps.certificates.models import Certificate
from apps.courses.models import Enrollment, EnrollmentStatus
from apps.organizations.models import CandidateProfileUnlock, Organization
from apps.users.models import User
from common.audit import AuditService
from common.entitlements import EntitlementService
from common.candidate_visibility import CandidateVisibilityService
from common.exceptions import PermissionError
from common.permission_service import PermissionService
from apps.notifications.models import NotificationService, NotificationType
from common.throttles import ApplicationSubmitRateThrottle, CandidateUnlockRateThrottle, RecruiterSearchRateThrottle

from .models import (
    ApplicationNote,
    ApplicationActivity,
    ApplicationAttachment,
    ApplicationQuestionType,
    ApplicationStage,
    ApplicationTimeline,
    Interview,
    InterviewFeedback,
    InterviewScorecard,
    InterviewStatus,
    JobAlert,
    JobApplication,
    JobApplicationAnswer,
    JobApplicationQuestion,
    JobListing,
    RecentlyViewedJob,
    RecruiterWaitlist,
    SavedJob,
    SavedJobCollection,
    SavedCandidate,
    TalentPool,
)
from .services import RecruitingService

logger = logging.getLogger(__name__)


class JobListingSerializer(serializers.ModelSerializer):
    salary_display = serializers.ReadOnlyField()
    job_type_display = serializers.CharField(source="get_job_type_display", read_only=True)
    experience_level_display = serializers.CharField(source="get_experience_level_display", read_only=True)
    required_track_title = serializers.CharField(source="required_track.title", read_only=True, default=None)
    required_track_slug = serializers.CharField(source="required_track.slug", read_only=True, default=None)
    organization_name = serializers.CharField(source="organization.name", read_only=True, default="")
    organization_type = serializers.CharField(source="organization.organization_type", read_only=True, default="")
    posted_by_name = serializers.CharField(source="posted_by.full_name", read_only=True, default="")
    application_questions = serializers.SerializerMethodField()

    class Meta:
        model = JobListing
        fields = [
            "id", "organization", "title", "company_name", "company_logo_url", "location",
            "job_type", "job_type_display", "experience_level", "experience_level_display",
            "description", "requirements", "salary_min", "salary_max", "salary_display",
            "apply_url", "required_track_title", "required_track_slug", "is_active",
            "views_count", "created_at", "country_code", "city", "is_remote", "remote_regions",
            "salary_currency", "salary_visible", "work_authorization_required", "visa_required",
            "visa_sponsorship", "citizenship_requirement", "languages_required", "required_skills",
            "preferred_skills", "expires_at", "organization_name", "organization_type", "posted_by_name",
            "application_questions",
        ]
        read_only_fields = ["id", "organization", "is_active", "views_count", "created_at"]

    def get_application_questions(self, obj):
        return JobApplicationQuestionSerializer(
            obj.application_questions.filter(is_active=True),
            many=True,
        ).data


class JobListingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobListing
        fields = [
            "title",
            "company_name",
            "company_logo_url",
            "description",
            "requirements",
            "job_type",
            "experience_level",
            "location",
            "country_code",
            "city",
            "is_remote",
            "remote_regions",
            "salary_min",
            "salary_max",
            "salary_currency",
            "salary_visible",
            "work_authorization_required",
            "visa_required",
            "visa_sponsorship",
            "citizenship_requirement",
            "languages_required",
            "apply_url",
            "required_track",
            "required_skills",
            "preferred_skills",
            "expires_at",
        ]


class RecruiterWaitlistSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    company_name = serializers.CharField(max_length=255)
    company_size = serializers.ChoiceField(choices=["1-10", "11-50", "51-200", "201-500", "500+"])
    roles_hiring_for = serializers.CharField(max_length=1000, allow_blank=True, default="")
    monthly_hires = serializers.ChoiceField(choices=["1-2", "3-5", "6-10", "10+"])


class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company_name", read_only=True)
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    candidate_email = serializers.SerializerMethodField()
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    answers = serializers.SerializerMethodField()

    class Meta:
        model = JobApplication
        fields = [
            "id", "job", "job_title", "company_name", "candidate", "candidate_name",
            "candidate_email", "organization", "stage", "stage_display", "cover_letter",
            "source", "assigned_recruiter", "hiring_manager", "is_archived",
            "selected_resume", "answers", "withdrawn_at", "created_at", "updated_at",
        ]

    def get_answers(self, obj):
        return JobApplicationAnswerSerializer(obj.answers.select_related("question"), many=True).data

    def get_candidate_email(self, obj):
        organization = self.context.get("organization") if hasattr(self, "context") else None
        actor = self.context.get("request").user if self.context.get("request") else None
        if actor is None:
            return obj.candidate.email
        if obj.candidate_id and CandidateVisibilityService.can_contact(actor, obj.candidate, organization=organization or obj.organization):
            return obj.candidate.email
        return ""


class JobApplicationQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplicationQuestion
        fields = ["id", "job", "question_text", "question_type", "is_required", "choices", "position", "is_active"]
        read_only_fields = ["id", "job"]

    def validate(self, attrs):
        question_type = attrs.get("question_type", getattr(self.instance, "question_type", ApplicationQuestionType.SHORT_TEXT))
        choices = attrs.get("choices", getattr(self.instance, "choices", []))
        if question_type == ApplicationQuestionType.MULTIPLE_CHOICE and not choices:
            raise serializers.ValidationError({"choices": "Multiple choice questions require choices."})
        return attrs


class JobApplicationAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)
    question_type = serializers.CharField(source="question.question_type", read_only=True)

    class Meta:
        model = JobApplicationAnswer
        fields = ["id", "question", "question_text", "question_type", "answer", "created_at", "updated_at"]
        read_only_fields = ["id", "question_text", "question_type", "created_at", "updated_at"]
        read_only_fields = [
            "id", "organization", "stage", "is_archived", "withdrawn_at",
            "created_at", "updated_at",
        ]


class JobApplicationCreateSerializer(serializers.Serializer):
    cover_letter = serializers.CharField(allow_blank=True, default="")
    source = serializers.CharField(max_length=50, allow_blank=True, default="direct")
    resume_id = serializers.UUIDField(required=False, allow_null=True)
    portfolio_id = serializers.UUIDField(required=False, allow_null=True)
    answers = serializers.ListField(child=serializers.DictField(), required=False)


class JobApplicationDraftSerializer(serializers.Serializer):
    cover_letter = serializers.CharField(allow_blank=True, default="")
    resume_id = serializers.UUIDField(required=False, allow_null=True)
    portfolio_id = serializers.UUIDField(required=False, allow_null=True)
    answers = serializers.ListField(child=serializers.DictField(), required=False)


class StageTransitionSerializer(serializers.Serializer):
    stage = serializers.ChoiceField(choices=ApplicationStage.choices)
    message = serializers.CharField(max_length=500, allow_blank=True, required=False)


class ApplicationNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = ApplicationNote
        fields = ["id", "application", "author", "author_name", "body", "is_internal", "created_at"]
        read_only_fields = ["id", "application", "author", "created_at"]


class ApplicationAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationAttachment
        fields = ["id", "file_url", "file_name", "content_type", "is_private", "created_at"]


class ApplicationActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True, default="")

    class Meta:
        model = ApplicationActivity
        fields = ["id", "actor", "actor_name", "activity_type", "metadata", "created_at"]


class ApplicationAssignmentSerializer(serializers.Serializer):
    assigned_recruiter = serializers.UUIDField(required=False, allow_null=True)
    hiring_manager = serializers.UUIDField(required=False, allow_null=True)


class BulkApplicationSerializer(serializers.Serializer):
    application_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    stage = serializers.ChoiceField(choices=ApplicationStage.choices, required=False)
    assigned_recruiter = serializers.UUIDField(required=False, allow_null=True)
    hiring_manager = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(max_length=500, allow_blank=True, required=False)


class TalentPoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentPool
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class SavedCandidateSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    candidate_email = serializers.SerializerMethodField()
    talent_pool_name = serializers.CharField(source="talent_pool.name", read_only=True, default="")

    class Meta:
        model = SavedCandidate
        fields = [
            "id", "candidate", "candidate_name", "candidate_email", "talent_pool",
            "talent_pool_name", "labels", "private_notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_candidate_email(self, obj):
        request = self.context.get("request") if hasattr(self, "context") else None
        actor = request.user if request else None
        if actor is None:
            return obj.candidate.email
        return obj.candidate.email if CandidateVisibilityService.can_contact(actor, obj.candidate, organization=obj.organization) else ""


class SavedCandidateCreateSerializer(serializers.Serializer):
    candidate_id = serializers.UUIDField()
    labels = serializers.ListField(child=serializers.CharField(max_length=80), required=False)
    private_notes = serializers.CharField(allow_blank=True, required=False)
    talent_pool = serializers.UUIDField(required=False, allow_null=True)


class SavedJobCollectionSerializer(serializers.ModelSerializer):
    saved_count = serializers.IntegerField(source="saved_jobs.count", read_only=True)

    class Meta:
        model = SavedJobCollection
        fields = ["id", "name", "description", "saved_count", "created_at"]
        read_only_fields = ["id", "saved_count", "created_at"]


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)
    job_id = serializers.UUIDField(write_only=True)
    collection_name = serializers.CharField(source="collection.name", read_only=True, default="")

    class Meta:
        model = SavedJob
        fields = [
            "id", "job", "job_id", "collection", "collection_name", "notes",
            "is_favorite_company", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "job", "collection_name", "created_at", "updated_at"]


class JobAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAlert
        fields = [
            "id", "name", "filters", "is_active",
            "last_run_at", "last_matched_count", "total_matched_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "last_run_at", "last_matched_count", "total_matched_count", "created_at", "updated_at"]


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            "id", "application", "organization", "interview_type", "status",
            "scheduled_start", "scheduled_end", "timezone", "meeting_link",
            "location", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]


class InterviewCreateSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    interview_type = serializers.CharField(max_length=20)
    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField(required=False, allow_null=True)
    timezone = serializers.CharField(max_length=50, default="UTC")
    meeting_link = serializers.URLField(max_length=1000, allow_blank=True, required=False)
    location = serializers.CharField(max_length=255, allow_blank=True, required=False)
    participant_ids = serializers.ListField(child=serializers.UUIDField(), required=False)


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = ["id", "interview", "author", "rating", "recommendation", "feedback", "created_at"]
        read_only_fields = ["id", "interview", "author", "created_at"]


class InterviewScorecardSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewScorecard
        fields = ["id", "interview", "author", "criteria", "total_score", "recommendation", "created_at"]
        read_only_fields = ["id", "interview", "author", "created_at"]


class InterviewDetailSerializer(serializers.ModelSerializer):
    feedback = InterviewFeedbackSerializer(many=True, read_only=True)
    scorecards = InterviewScorecardSerializer(many=True, read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id", "application", "organization", "interview_type", "status",
            "scheduled_start", "scheduled_end", "timezone", "meeting_link",
            "location", "created_by", "created_at", "updated_at", "feedback", "scorecards",
        ]


def _success(data=None, status_code=status.HTTP_200_OK, meta=None):
    return Response({"success": True, "data": data, "errors": {}, "meta": meta or {}}, status=status_code)


def _paginate(request, queryset):
    page = max(int(request.query_params.get("page", 1)), 1)
    page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
    total = queryset.count()
    start = (page - 1) * page_size
    return queryset[start:start + page_size], {"count": total, "page": page, "page_size": page_size}


def _active_jobs():
    now = timezone.now()
    return JobListing.objects.filter(is_active=True).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    ).select_related("required_track", "organization", "posted_by")


def _filter_jobs(request, jobs):
    q = request.query_params
    search = q.get("search")
    job_type = q.get("job_type")
    experience = q.get("experience_level") or q.get("experience")
    track_slug = q.get("track")
    country = q.get("country")
    city = q.get("city")
    company = q.get("company")
    work_mode = q.get("work_mode")
    remote = q.get("remote")
    skills = [s.strip() for s in q.get("skills", "").split(",") if s.strip()]
    salary_min = q.get("salary_min")
    salary_max = q.get("salary_max")
    posted_date = q.get("posted_date")
    verification_status = q.get("verification_status")
    sort = q.get("sort", "-created_at")

    if search:
        jobs = jobs.filter(
            models.Q(title__icontains=search)
            | models.Q(company_name__icontains=search)
            | models.Q(description__icontains=search)
            | models.Q(required_skills__icontains=search)
        )
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if experience:
        jobs = jobs.filter(experience_level=experience)
    if track_slug:
        jobs = jobs.filter(required_track__slug=track_slug)
    if country:
        jobs = jobs.filter(country_code__iexact=country)
    if city:
        jobs = jobs.filter(city__icontains=city)
    if company:
        jobs = jobs.filter(company_name__icontains=company)
    if remote in {"true", "1"} or work_mode == "remote":
        jobs = jobs.filter(is_remote=True)
    elif work_mode == "onsite":
        jobs = jobs.filter(is_remote=False)
    elif work_mode == "hybrid":
        jobs = jobs.filter(models.Q(location__icontains="hybrid") | models.Q(remote_regions__icontains="Hybrid"))
    for skill in skills:
        jobs = jobs.filter(models.Q(required_skills__icontains=skill) | models.Q(preferred_skills__icontains=skill))
    if salary_min:
        jobs = jobs.filter(models.Q(salary_max__gte=salary_min) | models.Q(salary_max__isnull=True))
    if salary_max:
        jobs = jobs.filter(models.Q(salary_min__lte=salary_max) | models.Q(salary_min__isnull=True))
    if posted_date == "7d":
        jobs = jobs.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
    elif posted_date == "30d":
        jobs = jobs.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
    if verification_status == "verified":
        jobs = jobs.filter(organization__status="active")
    if sort.lstrip("-") in {"created_at", "salary_min", "salary_max", "views_count", "title"}:
        jobs = jobs.order_by(sort)
    return jobs


def _profile_completion(user):
    score = 0
    if user.full_name:
        score += 10
    if user.avatar_url:
        score += 10
    if user.profile_headline:
        score += 10
    if user.profile_bio:
        score += 10
    if user.profile_location:
        score += 10
    if user.linkedin_url or user.github_url:
        score += 10
    try:
        portfolio = user.portfolio
        if portfolio.desired_role:
            score += 10
        if portfolio.skills.count() >= 3:
            score += 15
        if portfolio.projects.count() >= 1:
            score += 15
    except Portfolio.DoesNotExist:
        pass
    return min(score, 100)


def _resume_completion(user):
    try:
        resume = user.resume
    except Exception:
        return 0
    score = 0
    if resume.title:
        score += 15
    if resume.summary:
        score += 20
    if resume.target_role:
        score += 20
    if resume.education:
        score += 20
    if resume.experience:
        score += 15
    if resume.pdf_url:
        score += 10
    return min(score, 100)


def _portfolio_completion(user):
    try:
        portfolio = user.portfolio
    except Portfolio.DoesNotExist:
        return 0
    score = 0
    if portfolio.headline:
        score += 15
    if portfolio.bio:
        score += 15
    if portfolio.desired_role:
        score += 15
    if portfolio.skills.count() >= 3:
        score += 20
    if portfolio.projects.count() >= 1:
        score += 20
    if portfolio.visibility in {VisibilityChoice.PUBLIC, VisibilityChoice.UNLISTED}:
        score += 15
    return min(score, 100)


def _recommended_jobs_for_user(user, limit=6):
    try:
        portfolio = user.portfolio
        skills = list(portfolio.skills.values_list("name", flat=True))
        desired_role = portfolio.desired_role
        remote_preference = portfolio.remote_preference
        country = portfolio.preferred_work_country
        experience = portfolio.experience_level
    except Portfolio.DoesNotExist:
        skills = []
        desired_role = ""
        remote_preference = ""
        country = getattr(user, "current_country", "")
        experience = ""
    applied_job_ids = set(JobApplication.objects.filter(candidate=user).values_list("job_id", flat=True))
    scored = []
    for job in _active_jobs()[:100]:
        score = 0
        reasons = []
        matched_skills = [skill for skill in skills if skill.lower() in [s.lower() for s in (job.required_skills + job.preferred_skills)]]
        if matched_skills:
            score += len(matched_skills) * 10
            reasons.append(f"Matches {len(matched_skills)} of your skills")
        if country and job.country_code.upper() == country.upper():
            score += 10
            reasons.append("Located in your preferred country")
        if remote_preference in {"remote", "flexible"} and job.is_remote:
            score += 10
            reasons.append("Remote role matching your preference")
        if experience and job.experience_level == experience:
            score += 8
            reasons.append("Matches your experience level")
        if desired_role and desired_role.lower() in job.title.lower():
            score += 12
            reasons.append(f"Good fit for your {desired_role} goal")
        completeness = (_profile_completion(user) + _resume_completion(user) + _portfolio_completion(user)) // 3
        if completeness >= 70:
            score += 5
            reasons.append("Your profile is ready for this role")
        if job.id in applied_job_ids:
            score -= 20
            reasons.append("Already in your application history")
        if not reasons:
            reasons.append("Relevant active opportunity")
        data = JobListingSerializer(job).data
        data["recommendation_score"] = score
        data["recommendation_reasons"] = reasons[:3]
        scored.append((score, data))
    return [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:limit]]


def _get_recruiting_org(user, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    RecruitingService.ensure_can_recruit(user, organization)
    return organization


def _validate_application_answers(job, raw_answers):
    def value_from(item):
        answer = item.get("answer")
        if isinstance(answer, dict) and "value" in answer:
            return answer["value"]
        return answer

    answers_by_question = {
        str(item.get("question")): value_from(item)
        for item in (raw_answers or [])
        if item.get("question")
    }
    validated = []
    questions = list(job.application_questions.filter(is_active=True))
    for question in questions:
        value = answers_by_question.get(str(question.id))
        if question.is_required and value in (None, "", []):
            raise serializers.ValidationError({"answers": f"Answer required for: {question.question_text}"})
        if value in (None, "", []):
            continue
        if question.question_type == ApplicationQuestionType.YES_NO and not isinstance(value, bool):
            raise serializers.ValidationError({"answers": f"{question.question_text} must be yes/no."})
        if question.question_type == ApplicationQuestionType.NUMBER and not isinstance(value, (int, float)):
            raise serializers.ValidationError({"answers": f"{question.question_text} must be a number."})
        if question.question_type == ApplicationQuestionType.MULTIPLE_CHOICE and value not in question.choices:
            raise serializers.ValidationError({"answers": f"{question.question_text} must use one of the configured choices."})
        if question.question_type == ApplicationQuestionType.URL:
            field = serializers.URLField()
            field.run_validation(value)
        validated.append((question, {"value": value}))
    return validated


def _save_application_answers(application, answers):
    for question, answer in answers:
        JobApplicationAnswer.objects.update_or_create(
            application=application,
            question=question,
            defaults={"answer": answer},
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def job_list(request):
    """
    GET /api/v1/jobs/

    Public job listings. Filters: job_type, experience_level, track_slug, search.
    """
    jobs = _filter_jobs(request, _active_jobs())
    page, meta = _paginate(request, jobs)

    return Response({
        "count": jobs.count(),
        "results": JobListingSerializer(page, many=True).data,
        "meta": meta,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def job_detail(request, job_id):
    """
    GET /api/v1/jobs/{job_id}/

    Returns job detail and increments view count.
    """
    job = get_object_or_404(_active_jobs(), id=job_id)
    JobListing.objects.filter(id=job_id).update(views_count=models.F("views_count") + 1)
    if request.user.is_authenticated:
        RecentlyViewedJob.objects.update_or_create(
            user=request.user,
            job=job,
            defaults={"last_viewed_at": timezone.now()},
        )
        RecentlyViewedJob.objects.filter(user=request.user, job=job).update(viewed_count=models.F("viewed_count") + 1)
        AnalyticsService.track(name="job_viewed", user=request.user, target=job, metadata={"job_id": str(job.id)})
    return Response(JobListingSerializer(job).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    user = request.user
    applications = JobApplication.objects.filter(candidate=user).select_related("job", "organization").order_by("-created_at")
    active_applications = applications.filter(is_archived=False)
    upcoming_interviews = Interview.objects.filter(
        application__candidate=user,
        scheduled_start__gte=timezone.now(),
        status__in=[InterviewStatus.SCHEDULED, InterviewStatus.RESCHEDULED],
    ).select_related("application", "application__job")[:5]
    try:
        portfolio = user.portfolio
        skills = list(portfolio.skills.values_list("name", flat=True)[:12])
        desired_role = portfolio.desired_role
        remote_preference = portfolio.remote_preference
    except Portfolio.DoesNotExist:
        skills = []
        desired_role = ""
        remote_preference = ""
    certificates = Certificate.objects.filter(user=user, is_revoked=False)
    enrollments = Enrollment.objects.filter(user=user).select_related("course")
    data = {
        "profile_completion": _profile_completion(user),
        "resume_completion": _resume_completion(user),
        "portfolio_completion": _portfolio_completion(user),
        "skills_summary": skills,
        "certificates_earned": certificates.count(),
        "courses_in_progress": list(enrollments.filter(status=EnrollmentStatus.ACTIVE).values("id", "course__title", "course__slug", "status")[:6]),
        "applications_submitted": active_applications.exclude(stage=ApplicationStage.DRAFT).count(),
        "applications": JobApplicationSerializer(active_applications[:8], many=True).data,
        "application_status_timeline": list(ApplicationTimeline.objects.filter(application__candidate=user).values("id", "event_type", "from_stage", "to_stage", "message", "created_at")[:20]),
        "upcoming_interviews": InterviewSerializer(upcoming_interviews, many=True).data,
        "saved_jobs": SavedJobSerializer(SavedJob.objects.filter(user=user).select_related("job", "collection")[:6], many=True).data,
        "recommended_jobs": _recommended_jobs_for_user(user),
        "career_goals": {
            "desired_role": desired_role,
            "open_to_work": getattr(user, "is_public_profile", False),
            "remote_preference": remote_preference,
        },
        "recent_recruiter_activity": list(AnalyticsEvent.objects.filter(name__in=["recruiter_viewed_candidate", "candidate_unlocked"], target_id=str(user.id)).values("id", "name", "metadata", "occurred_at")[:10]),
        "ai_usage_summary": {
            "ai_tutor_used": AnalyticsEvent.objects.filter(user=user, name="ai_tutor_used").count(),
            "resume_analysis_available": True,
            "portfolio_analysis_available": True,
        },
        "student_analytics": {
            "profile_views": getattr(locals().get("portfolio", None), "profile_views", 0),
            "recruiter_views": AnalyticsEvent.objects.filter(name="recruiter_viewed_candidate", target_id=str(user.id)).count(),
            "resume_downloads": ResumeAnalytics.objects.filter(resume__user=user, event_type=ResumeAnalytics.EventType.DOWNLOADED).count(),
            "portfolio_views": AnalyticsEvent.objects.filter(name="portfolio_viewed", target_id=str(user.id)).count(),
            "applications_by_status": {
                row["stage"]: row["count"]
                for row in active_applications.values("stage").annotate(count=models.Count("id"))
            },
            "saved_jobs": SavedJob.objects.filter(user=user).count(),
            "job_alert_matches": JobAlert.objects.filter(user=user).aggregate(total=models.Sum("total_matched_count"))["total"] or 0,
            "recommended_job_clicks": AnalyticsEvent.objects.filter(user=user, name="recommended_job_viewed").count(),
        },
    }
    return _success(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_applications(request):
    applications = JobApplication.objects.filter(candidate=request.user).select_related("job", "organization").order_by("-created_at")
    return _success(JobApplicationSerializer(applications, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_application_detail(request, application_id):
    application = get_object_or_404(JobApplication.objects.select_related("job", "organization"), id=application_id, candidate=request.user)
    data = {
        "application": JobApplicationSerializer(application).data,
        "job": JobListingSerializer(application.job).data,
        "timeline": list(application.timeline.values("id", "event_type", "from_stage", "to_stage", "message", "metadata", "created_at")),
        "interviews": InterviewSerializer(application.interviews.all(), many=True).data,
        "attachments": ApplicationAttachmentSerializer(application.attachments.filter(is_private=False), many=True).data,
        "answers": JobApplicationAnswerSerializer(application.answers.select_related("question"), many=True).data,
    }
    return _success(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def job_save_draft(request, job_id):
    job = get_object_or_404(_active_jobs(), id=job_id)
    serializer = JobApplicationDraftSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    answers = _validate_application_answers(job, serializer.validated_data.get("answers", []))
    selected_resume = None
    resume_id = serializer.validated_data.get("resume_id")
    if resume_id:
        selected_resume = get_object_or_404(CareerResume, id=resume_id, user=request.user, is_archived=False)
    application, _ = JobApplication.objects.update_or_create(
        job=job,
        candidate=request.user,
        defaults={
            "organization": job.organization,
            "stage": ApplicationStage.DRAFT,
            "cover_letter": serializer.validated_data.get("cover_letter", ""),
            "source": "student_draft",
            "selected_resume": selected_resume,
        },
    )
    _save_application_answers(application, answers)
    RecruitingService.create_timeline(application, request.user, "application_draft_saved", to_stage=ApplicationStage.DRAFT, message="Draft saved.")
    return _success(JobApplicationSerializer(application).data, status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def application_preview(request, job_id):
    job = get_object_or_404(_active_jobs(), id=job_id)
    serializer = JobApplicationDraftSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    answers = _validate_application_answers(job, serializer.validated_data.get("answers", []))
    selected_resume = None
    resume_id = serializer.validated_data.get("resume_id")
    if resume_id:
        selected_resume = get_object_or_404(CareerResume, id=resume_id, user=request.user, is_archived=False)
    try:
        portfolio = request.user.portfolio
        portfolio_summary = {
            "id": str(portfolio.id),
            "headline": portfolio.headline,
            "public_url": portfolio.public_url,
            "visibility": portfolio.visibility,
            "skills": list(portfolio.skills.values_list("name", flat=True)[:10]),
        }
    except Portfolio.DoesNotExist:
        portfolio_summary = None
    return _success({
        "job": JobListingSerializer(job).data,
        "company": job.company_name,
        "selected_resume": {
            "id": str(selected_resume.id),
            "title": selected_resume.title,
            "target_role": selected_resume.target_role,
            "summary": selected_resume.summary,
            "file_count": selected_resume.files.count(),
        } if selected_resume else None,
        "portfolio": portfolio_summary,
        "cover_letter": serializer.validated_data.get("cover_letter", ""),
        "answers": [
            {
                "question": str(question.id),
                "question_text": question.question_text,
                "question_type": question.question_type,
                "answer": answer,
            }
            for question, answer in answers
        ],
        "profile_summary": {
            "name": request.user.full_name,
            "email": request.user.email,
            "profile_completion": _profile_completion(request.user),
            "resume_completion": _resume_completion(request.user),
            "portfolio_completion": _portfolio_completion(request.user),
        },
        "can_submit": bool(selected_resume or portfolio_summary),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def application_submit(request, application_id):
    application = get_object_or_404(JobApplication.objects.select_related("job"), id=application_id, candidate=request.user)
    if application.stage != ApplicationStage.DRAFT:
        return _success(JobApplicationSerializer(application).data)
    application.stage = ApplicationStage.APPLIED
    application.source = "student_application"
    application.save(update_fields=["stage", "source", "updated_at"])
    JobListing.objects.filter(id=application.job_id).update(applications_count=models.F("applications_count") + 1)
    RecruitingService.create_timeline(application, request.user, "application_created", from_stage=ApplicationStage.DRAFT, to_stage=ApplicationStage.APPLIED, message="Application submitted.")
    RecruitingService.create_activity(application, request.user, "application_created")
    AuditService.record(actor=request.user, action="application_created", target=application, organization=application.organization, metadata={"job_id": str(application.job_id)})
    AnalyticsService.track(name="job_applied", user=request.user, organization=application.organization, target=application, metadata={"job_id": str(application.job_id)})
    if application.selected_resume_id:
        ResumeAnalytics.objects.create(
            resume=application.selected_resume,
            actor=request.user,
            event_type=ResumeAnalytics.EventType.USED_FOR_APPLICATION,
            metadata={"application_id": str(application.id), "job_id": str(application.job_id)},
        )
        AnalyticsService.track(
            name="resume_used_for_application",
            user=request.user,
            organization=application.organization,
            target=application.selected_resume,
            metadata={"application_id": str(application.id), "job_id": str(application.job_id)},
        )
    return _success(JobApplicationSerializer(application).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def saved_job_collections(request):
    if request.method == "GET":
        return _success(SavedJobCollectionSerializer(SavedJobCollection.objects.filter(user=request.user), many=True).data)
    serializer = SavedJobCollectionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    collection, _ = SavedJobCollection.objects.update_or_create(
        user=request.user,
        name=serializer.validated_data["name"],
        defaults={"description": serializer.validated_data.get("description", "")},
    )
    return _success(SavedJobCollectionSerializer(collection).data, status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def saved_jobs(request):
    if request.method == "GET":
        saved = SavedJob.objects.filter(user=request.user).select_related("job", "collection", "job__organization")
        return _success(SavedJobSerializer(saved, many=True).data)
    serializer = SavedJobSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    job = get_object_or_404(JobListing, id=serializer.validated_data["job_id"])
    collection = serializer.validated_data.get("collection")
    if collection and collection.user_id != request.user.id:
        raise PermissionError("Collection does not belong to you.")
    saved, _ = SavedJob.objects.update_or_create(
        user=request.user,
        job=job,
        defaults={
            "collection": collection,
            "notes": serializer.validated_data.get("notes", ""),
            "is_favorite_company": serializer.validated_data.get("is_favorite_company", False),
        },
    )
    AnalyticsService.track(name="job_saved", user=request.user, target=job, metadata={"job_id": str(job.id)})
    return _success(SavedJobSerializer(saved).data, status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def saved_job_delete(request, job_id):
    deleted, _ = SavedJob.objects.filter(user=request.user, job_id=job_id).delete()
    return _success({"deleted": deleted})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recently_viewed_jobs(request):
    views = RecentlyViewedJob.objects.filter(user=request.user).select_related("job", "job__organization")[:20]
    return _success([{"id": str(view.id), "last_viewed_at": view.last_viewed_at, "viewed_count": view.viewed_count, "job": JobListingSerializer(view.job).data} for view in views])


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def job_alerts(request):
    if request.method == "GET":
        return _success(JobAlertSerializer(JobAlert.objects.filter(user=request.user), many=True).data)
    serializer = JobAlertSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    alert = JobAlert.objects.create(user=request.user, **serializer.validated_data)
    AnalyticsService.track(name="job_alert_created", user=request.user, target=alert)
    return _success(JobAlertSerializer(alert).data, status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recommended_job_click(request, job_id):
    job = get_object_or_404(_active_jobs(), id=job_id)
    AnalyticsService.track(name="recommended_job_viewed", user=request.user, target=job, metadata={"job_id": str(job.id)})
    return _success({"tracked": True})


@api_view(["POST"])
@permission_classes([AllowAny])
def recruiter_waitlist(request):
    """
    POST /api/v1/jobs/recruit/

    Save recruiter interest for the portal launch.
    """
    serializer = RecruiterWaitlistSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    _, created = RecruiterWaitlist.objects.get_or_create(
        email=data["email"],
        defaults=data,
    )

    if not created:
        return Response(
            {"detail": "You are already on the waitlist. We will contact you soon."},
            status=status.HTTP_200_OK,
        )

    logger.info("Recruiter waitlist: %s at %s", data["email"], data["company_name"])
    return Response(
        {"detail": "You are on the waitlist. We will reach out when the recruiter portal launches."},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def organization_jobs(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    if not PermissionService.can_manage_organization(request.user, organization) and not EntitlementService.can_post_job(
        request.user,
        organization=organization,
    ):
        raise PermissionError("You cannot manage jobs for this organization.")

    if request.method == "GET":
        jobs = JobListing.objects.filter(organization=organization).select_related("required_track")
        return Response(JobListingSerializer(jobs, many=True).data)

    if not EntitlementService.can_post_job(request.user, organization=organization):
        raise PermissionError("This organization cannot post jobs.")
    serializer = JobListingWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    job = serializer.save(
        organization=organization,
        posted_by=request.user,
        is_active=False,
    )
    AuditService.record(
        actor=request.user,
        action="job_created",
        target=job,
        organization=organization,
        metadata={"title": job.title},
    )
    AnalyticsService.job_created(user=request.user, organization=organization, job=job)
    return Response(JobListingSerializer(job).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def organization_job_update(request, organization_id, job_id):
    organization = get_object_or_404(Organization, id=organization_id)
    job = get_object_or_404(JobListing, id=job_id, organization=organization)
    if not PermissionService.can_manage_job(request.user, job):
        raise PermissionError("You cannot update this job.")
    serializer = JobListingWriteSerializer(job, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    job = serializer.save()
    return Response(JobListingSerializer(job).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def organization_job_publish(request, organization_id, job_id):
    organization = get_object_or_404(Organization, id=organization_id)
    job = get_object_or_404(JobListing, id=job_id, organization=organization)
    if not PermissionService.can_publish_job(request.user, job):
        raise PermissionError("You cannot publish this job.")
    if not EntitlementService.can_post_job(request.user, organization=organization):
        raise PermissionError("This organization cannot publish jobs.")
    job.is_active = True
    job.save(update_fields=["is_active", "updated_at"])
    AuditService.record(
        actor=request.user,
        action="job_published",
        target=job,
        organization=organization,
        metadata={"title": job.title},
    )
    AnalyticsService.track(
        name="job_published",
        user=request.user,
        organization=organization,
        target=job,
        metadata={"title": job.title},
    )
    return Response(JobListingSerializer(job).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def organization_job_archive(request, organization_id, job_id):
    organization = get_object_or_404(Organization, id=organization_id)
    job = get_object_or_404(JobListing, id=job_id, organization=organization)
    if not PermissionService.can_manage_job(request.user, job):
        raise PermissionError("You cannot archive this job.")
    job.is_active = False
    job.save(update_fields=["is_active", "updated_at"])
    AuditService.record(
        actor=request.user,
        action="job_archived",
        target=job,
        organization=organization,
        metadata={"title": job.title},
    )
    return Response(JobListingSerializer(job).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ApplicationSubmitRateThrottle])
def apply_to_job(request, job_id):
    job = get_object_or_404(JobListing, id=job_id, is_active=True)
    serializer = JobApplicationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data.copy()
    resume_id = data.pop("resume_id", None)
    data.pop("portfolio_id", None)
    answers = _validate_application_answers(job, data.pop("answers", []))
    selected_resume = None
    if resume_id:
        selected_resume = get_object_or_404(CareerResume, id=resume_id, user=request.user, is_archived=False)
    application, created = RecruitingService.create_application(
        actor=request.user,
        job=job,
        candidate=request.user,
        **data,
    )
    if selected_resume and application.selected_resume_id != selected_resume.id:
        application.selected_resume = selected_resume
        application.save(update_fields=["selected_resume", "updated_at"])
    _save_application_answers(application, answers)
    if selected_resume and created:
        ResumeAnalytics.objects.create(
            resume=selected_resume,
            actor=request.user,
            event_type=ResumeAnalytics.EventType.USED_FOR_APPLICATION,
            metadata={"application_id": str(application.id), "job_id": str(job.id)},
        )
        AnalyticsService.track(
            name="resume_used_for_application",
            user=request.user,
            organization=job.organization,
            target=selected_resume,
            metadata={"application_id": str(application.id), "job_id": str(job.id)},
        )
    if created:
        AnalyticsService.track(name="job_applied", user=request.user, organization=job.organization, target=application, metadata={"job_id": str(job.id)})
    return _success(
        JobApplicationSerializer(application).data,
        status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recruiter_dashboard(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    return _success(RecruitingService.dashboard_summary(request.user, organization))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pipeline_applications(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    applications = JobApplication.objects.filter(
        organization=organization,
        is_archived=False,
    ).select_related("job", "candidate", "assigned_recruiter", "hiring_manager")

    stage_filter = request.query_params.get("stage")
    job_id = request.query_params.get("job_id")
    assigned_to = request.query_params.get("assigned_to")
    search = request.query_params.get("search")
    sort = request.query_params.get("sort", "-created_at")

    if stage_filter:
        applications = applications.filter(stage=stage_filter)
    if job_id:
        applications = applications.filter(job_id=job_id)
    if assigned_to:
        applications = applications.filter(
            models.Q(assigned_recruiter_id=assigned_to) | models.Q(hiring_manager_id=assigned_to)
        )
    if search:
        applications = applications.filter(
            models.Q(candidate__full_name__icontains=search)
            | models.Q(candidate__email__icontains=search)
            | models.Q(job__title__icontains=search)
        )
    if sort.lstrip("-") in {"created_at", "updated_at", "stage"}:
        applications = applications.order_by(sort)

    page, meta = _paginate(request, applications)
    stats = {
        row["stage"]: row["count"]
        for row in applications.values("stage").annotate(count=models.Count("id"))
    }
    meta["pipeline_statistics"] = stats
    return _success(JobApplicationSerializer(page, many=True, context={"request": request, "organization": organization}).data, meta=meta)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def application_timeline(request, organization_id, application_id):
    organization = _get_recruiting_org(request.user, organization_id)
    application = get_object_or_404(JobApplication, id=application_id, organization=organization)
    if not PermissionService.can_view_application(request.user, application):
        raise PermissionError("You cannot view this application.")
    return _success(list(application.timeline.values("id", "event_type", "from_stage", "to_stage", "message", "metadata", "created_at")))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def application_detail(request, organization_id, application_id):
    organization = _get_recruiting_org(request.user, organization_id)
    application = get_object_or_404(
        JobApplication.objects.select_related("job", "candidate", "assigned_recruiter", "hiring_manager"),
        id=application_id,
        organization=organization,
    )
    if not PermissionService.can_view_application(request.user, application):
        raise PermissionError("You cannot view this application.")
    interviews = application.interviews.prefetch_related("feedback", "scorecards").all()
    audit_logs = AuditLog.objects.filter(
        organization_id=organization.id,
    ).filter(
        models.Q(target_type="JobApplication", target_id=str(application.id))
        | models.Q(target_type="Interview", target_id__in=[str(interview.id) for interview in interviews])
    )[:30]
    visibility = CandidateVisibilityService.evaluate(request.user, application.candidate, organization=organization)
    data = {
        "application": JobApplicationSerializer(application, context={"request": request, "organization": organization}).data,
        "candidate": {
            "id": str(application.candidate_id),
            "full_name": application.candidate.full_name,
            "email": application.candidate.email if visibility.can_contact else "",
            "avatar_url": application.candidate.avatar_url,
            "profile_headline": application.candidate.profile_headline,
            "profile_location": application.candidate.profile_location,
            "username": application.candidate.username,
            "is_verified": application.candidate.is_verified,
            "can_contact": visibility.can_contact,
            "resume_visible": visibility.can_view_resume,
            "portfolio_visible": visibility.can_view_portfolio,
        },
        "job": JobListingSerializer(application.job).data,
        "timeline": list(application.timeline.values("id", "event_type", "from_stage", "to_stage", "message", "metadata", "created_at")),
        "notes": ApplicationNoteSerializer(application.notes.select_related("author"), many=True).data,
        "attachments": ApplicationAttachmentSerializer(application.attachments.all(), many=True).data,
        "answers": JobApplicationAnswerSerializer(application.answers.select_related("question"), many=True).data,
        "activity": ApplicationActivitySerializer(application.activities.select_related("actor"), many=True).data,
        "interviews": InterviewDetailSerializer(interviews, many=True).data,
        "audit_history": list(audit_logs.values("id", "action", "target_type", "target_id", "metadata", "created_at")),
    }
    return _success(data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def organization_job_questions(request, organization_id, job_id):
    organization = _get_recruiting_org(request.user, organization_id)
    job = get_object_or_404(JobListing, id=job_id, organization=organization)
    if not PermissionService.can_manage_job(request.user, job):
        raise PermissionError("You cannot manage questions for this job.")
    if request.method == "GET":
        return _success(JobApplicationQuestionSerializer(job.application_questions.all(), many=True).data)
    serializer = JobApplicationQuestionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = JobApplicationQuestion.objects.create(job=job, **serializer.validated_data)
    return _success(JobApplicationQuestionSerializer(question).data, status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def organization_job_question_detail(request, organization_id, job_id, question_id):
    organization = _get_recruiting_org(request.user, organization_id)
    job = get_object_or_404(JobListing, id=job_id, organization=organization)
    if not PermissionService.can_manage_job(request.user, job):
        raise PermissionError("You cannot manage questions for this job.")
    question = get_object_or_404(JobApplicationQuestion, id=question_id, job=job)
    if request.method == "PATCH":
        serializer = JobApplicationQuestionSerializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return _success(JobApplicationQuestionSerializer(question).data)
    question.is_active = False
    question.save(update_fields=["is_active", "updated_at"])
    return _success(JobApplicationQuestionSerializer(question).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def application_stage_update(request, organization_id, application_id):
    organization = _get_recruiting_org(request.user, organization_id)
    application = get_object_or_404(JobApplication, id=application_id, organization=organization)
    serializer = StageTransitionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    application = RecruitingService.transition_application(
        actor=request.user,
        application=application,
        stage=serializer.validated_data["stage"],
        message=serializer.validated_data.get("message", ""),
    )
    return _success(JobApplicationSerializer(application).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def application_withdraw(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id, candidate=request.user)
    application = RecruitingService.withdraw_application(actor=request.user, application=application)
    return _success(JobApplicationSerializer(application).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_stage_update(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    serializer = BulkApplicationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    stage = serializer.validated_data.get("stage")
    if not stage:
        raise serializers.ValidationError({"stage": "This field is required."})
    updated = []
    for application in JobApplication.objects.filter(
        id__in=serializer.validated_data["application_ids"],
        organization=organization,
    ):
        updated.append(RecruitingService.transition_application(
            actor=request.user,
            application=application,
            stage=stage,
            message=serializer.validated_data.get("message", ""),
        ))
    return _success(JobApplicationSerializer(updated, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_archive(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    serializer = BulkApplicationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    archived = []
    for application in JobApplication.objects.filter(
        id__in=serializer.validated_data["application_ids"],
        organization=organization,
    ):
        archived.append(RecruitingService.archive_application(actor=request.user, application=application))
    return _success(JobApplicationSerializer(archived, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_reject(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    serializer = BulkApplicationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    rejected = []
    for application in JobApplication.objects.filter(
        id__in=serializer.validated_data["application_ids"],
        organization=organization,
    ):
        rejected.append(RecruitingService.transition_application(
            actor=request.user,
            application=application,
            stage=ApplicationStage.REJECTED,
            message=serializer.validated_data.get("message", ""),
        ))
    return _success(JobApplicationSerializer(rejected, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def application_assign(request, organization_id, application_id):
    organization = _get_recruiting_org(request.user, organization_id)
    application = get_object_or_404(JobApplication, id=application_id, organization=organization)
    RecruitingService.ensure_can_manage_application(request.user, application)
    serializer = ApplicationAssignmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    fields = []
    if "assigned_recruiter" in data:
        application.assigned_recruiter_id = data["assigned_recruiter"]
        fields.append("assigned_recruiter")
    if "hiring_manager" in data:
        application.hiring_manager_id = data["hiring_manager"]
        fields.append("hiring_manager")
    if fields:
        fields.append("updated_at")
        application.save(update_fields=fields)
    RecruitingService.create_timeline(application, request.user, "application_assigned", message="Application assignment updated.")
    RecruitingService.create_activity(application, request.user, "application_assigned")
    AuditService.record(actor=request.user, action="application_assigned", target=application, organization=organization)
    return _success(JobApplicationSerializer(application).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def application_notes(request, organization_id, application_id):
    organization = _get_recruiting_org(request.user, organization_id)
    application = get_object_or_404(JobApplication, id=application_id, organization=organization)
    RecruitingService.ensure_can_manage_application(request.user, application)
    if request.method == "GET":
        return _success(ApplicationNoteSerializer(application.notes.all(), many=True).data)
    serializer = ApplicationNoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    note = ApplicationNote.objects.create(
        application=application,
        author=request.user,
        body=serializer.validated_data["body"],
        is_internal=serializer.validated_data.get("is_internal", True),
    )
    RecruitingService.create_timeline(application, request.user, "application_note_added", message="Note added.")
    RecruitingService.create_activity(application, request.user, "application_note_added")
    return _success(ApplicationNoteSerializer(note).data, status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([RecruiterSearchRateThrottle])
def candidate_search(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    portfolios = Portfolio.objects.filter(
        user__is_active=True,
    ).exclude(visibility=VisibilityChoice.PRIVATE).select_related("user", "user__privacy_settings").prefetch_related("skills")
    portfolios = portfolios.filter(CandidateVisibilityService.visible_candidate_filter())

    q = request.query_params
    search = q.get("search")
    skills = [s.strip() for s in q.get("skills", "").split(",") if s.strip()]
    experience = q.get("experience")
    location = q.get("location")
    country = q.get("country")
    city = q.get("city")
    languages = [s.strip() for s in q.get("languages", "").split(",") if s.strip()]
    career_interests = q.get("career_interests")
    remote_preference = q.get("remote_preference")
    verification_status = q.get("verification_status")
    portfolio_available = q.get("portfolio_available")
    resume_available = q.get("resume_available")
    work_authorization = q.get("work_authorization")

    if search:
        portfolios = portfolios.filter(
            models.Q(user__full_name__icontains=search)
            | models.Q(user__email__icontains=search)
            | models.Q(headline__icontains=search)
            | models.Q(desired_role__icontains=search)
            | models.Q(bio__icontains=search)
        )
    if skills:
        portfolios = portfolios.filter(skills__name__in=skills).distinct()
    if experience:
        portfolios = portfolios.filter(experience_level=experience)
    if location:
        portfolios = portfolios.filter(location__icontains=location)
    if country:
        portfolios = portfolios.filter(preferred_work_country__iexact=country)
    if city:
        portfolios = portfolios.filter(location__icontains=city)
    if languages:
        portfolios = portfolios.filter(user__preferred_language__in=languages)
    if career_interests:
        portfolios = portfolios.filter(desired_role__icontains=career_interests)
    if remote_preference:
        portfolios = portfolios.filter(remote_preference=remote_preference)
    if verification_status == "verified":
        portfolios = portfolios.filter(user__is_verified=True)
    if portfolio_available == "true":
        portfolios = portfolios.filter(models.Q(headline__gt="") | models.Q(bio__gt=""))
    if resume_available == "true":
        portfolios = portfolios.filter(
            user__resume__isnull=False,
        ).filter(
            models.Q(user__privacy_settings__recruiter_resume_visibility=True)
            | models.Q(user__privacy_settings__isnull=True)
        )
    if work_authorization:
        portfolios = portfolios.filter(user__nationality__iexact=work_authorization)

    page, meta = _paginate(request, portfolios)
    AuditService.record(
        actor=request.user,
        action="candidate_search_performed",
        target=organization,
        organization=organization,
        request=request,
        metadata={
            "filters": sorted([key for key, value in q.items() if value]),
            "result_count": meta.get("count"),
        },
    )
    page_user_ids = [p.user_id for p in page]
    saved_ids = set(SavedCandidate.objects.filter(
        organization=organization,
        candidate_id__in=page_user_ids,
    ).values_list("candidate_id", flat=True))
    unlocked_ids = set(organization.candidate_profile_unlocks.filter(
        candidate_id__in=page_user_ids,
    ).values_list("candidate_id", flat=True))
    resume_ids = set(CareerResume.objects.filter(user_id__in=page_user_ids, is_archived=False).values_list("user_id", flat=True))
    data = []
    for portfolio in page:
        is_unlocked = portfolio.user_id in unlocked_ids
        visibility = CandidateVisibilityService.evaluate_search_result(
            request.user,
            portfolio.user,
            organization=organization,
            is_unlocked=is_unlocked,
        )
        data.append({
            "candidate_id": str(portfolio.user_id),
            "full_name": portfolio.user.full_name,
            "headline": portfolio.headline,
            "desired_role": portfolio.desired_role,
            "experience_level": portfolio.experience_level,
            "location": portfolio.location,
            "country": portfolio.preferred_work_country,
            "remote_preference": portfolio.remote_preference,
            "verified": portfolio.user.is_verified,
            "portfolio_available": visibility.can_view_portfolio,
            "resume_available": portfolio.user_id in resume_ids and visibility.can_view_resume,
            "skills": [skill.name for skill in list(portfolio.skills.all())[:20]],
            "is_saved": portfolio.user_id in saved_ids,
            "is_unlocked": is_unlocked,
            "can_contact": visibility.can_contact,
            "open_to_work": getattr(getattr(portfolio.user, "privacy_settings", None), "open_to_work", False),
        })
    return _success(data, meta=meta)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([CandidateUnlockRateThrottle])
def candidate_unlock(request, organization_id, candidate_id):
    organization = _get_recruiting_org(request.user, organization_id)
    candidate = get_object_or_404(User, id=candidate_id, is_active=True)
    if not CandidateVisibilityService.can_unlock_candidate(request.user, candidate, organization):
        logger.warning(
            "candidate_unlock_denied",
            extra={"actor_id": str(request.user.id), "candidate_id": str(candidate.id), "organization_id": str(organization.id)},
        )
        raise PermissionError("This candidate is not visible to recruiters.")
    entitlement = EntitlementService.get_recruiter_entitlement(organization)
    if not EntitlementService.can_search_candidates(request.user, organization=organization):
        raise PermissionError("This organization cannot search candidates.")
    if not entitlement or not entitlement.can_view_candidate_profiles:
        raise PermissionError("This organization cannot unlock candidate profiles.")
    unlock, created = CandidateProfileUnlock.objects.get_or_create(
        organization=organization,
        candidate=candidate,
        defaults={"unlocked_by": request.user},
    )
    if created:
        logger.info(
            "candidate_unlocked",
            extra={"actor_id": str(request.user.id), "candidate_id": str(candidate.id), "organization_id": str(organization.id)},
        )
        AuditService.record(
            actor=request.user,
            action="candidate_unlocked",
            target=unlock,
            organization=organization,
            metadata={"candidate_id": str(candidate.id)},
        )
        AnalyticsService.candidate_unlocked(
            user=request.user,
            organization=organization,
            candidate=candidate,
            metadata={"unlock_id": str(unlock.id)},
        )
    return _success({
        "candidate_id": str(candidate.id),
        "is_unlocked": True,
        "created": created,
    }, status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def saved_candidates(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    if request.method == "GET":
        saved = SavedCandidate.objects.filter(organization=organization).select_related("candidate", "talent_pool")
        return _success(SavedCandidateSerializer(saved, many=True, context={"request": request}).data)
    serializer = SavedCandidateCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    candidate = get_object_or_404(User, id=serializer.validated_data["candidate_id"], is_active=True)
    talent_pool = None
    if serializer.validated_data.get("talent_pool"):
        talent_pool = get_object_or_404(TalentPool, id=serializer.validated_data["talent_pool"], organization=organization)
    saved = RecruitingService.save_candidate(
        actor=request.user,
        organization=organization,
        candidate=candidate,
        labels=serializer.validated_data.get("labels", []),
        private_notes=serializer.validated_data.get("private_notes", ""),
        talent_pool=talent_pool,
    )
    return _success(SavedCandidateSerializer(saved, context={"request": request}).data, status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def saved_candidate_delete(request, organization_id, candidate_id):
    organization = _get_recruiting_org(request.user, organization_id)
    deleted, _ = SavedCandidate.objects.filter(organization=organization, candidate_id=candidate_id).delete()
    return _success({"deleted": deleted})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def talent_pools(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    if request.method == "GET":
        return _success(TalentPoolSerializer(organization.talent_pools.all(), many=True).data)
    serializer = TalentPoolSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    pool = TalentPool.objects.create(
        organization=organization,
        created_by=request.user,
        **serializer.validated_data,
    )
    return _success(TalentPoolSerializer(pool).data, status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def interviews(request, organization_id):
    organization = _get_recruiting_org(request.user, organization_id)
    if request.method == "GET":
        qs = Interview.objects.filter(organization=organization).select_related("application", "created_by")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        page, meta = _paginate(request, qs)
        return _success(InterviewSerializer(page, many=True).data, meta=meta)
    serializer = InterviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    application = get_object_or_404(JobApplication, id=serializer.validated_data["application_id"], organization=organization)
    data = serializer.validated_data.copy()
    participant_ids = data.pop("participant_ids", [])
    data.pop("application_id")
    interview = RecruitingService.schedule_interview(
        actor=request.user,
        application=application,
        interview_data=data,
        participant_ids=participant_ids,
    )
    return _success(InterviewSerializer(interview).data, status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def interview_update(request, organization_id, interview_id):
    organization = _get_recruiting_org(request.user, organization_id)
    interview = get_object_or_404(Interview, id=interview_id, organization=organization)
    if not PermissionService.can_manage_interview(request.user, interview):
        raise PermissionError("You cannot update this interview.")
    serializer = InterviewSerializer(interview, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    previous_status = interview.status
    interview = serializer.save()
    RecruitingService.create_timeline(
        interview.application,
        request.user,
        "interview_updated",
        message="Interview updated.",
        metadata={"interview_id": str(interview.id), "status": interview.status},
    )
    AuditService.record(actor=request.user, action="interview_updated", target=interview, organization=organization)
    AnalyticsService.track(name="interview_completed" if interview.status == InterviewStatus.COMPLETED else "interview_updated", user=request.user, organization=organization, target=interview)
    NotificationService.notify(
        recipient=interview.application.candidate,
        notification_type=NotificationType.INTERVIEW_UPDATED,
        title="Interview updated",
        body=f"Your interview for {interview.application.job.title} was updated.",
        action_url="/dashboard",
        payload={"application_id": str(interview.application_id), "interview_id": str(interview.id), "status": interview.status},
    )
    if interview.application.assigned_recruiter_id and interview.application.assigned_recruiter_id != request.user.id:
        NotificationService.notify(
            recipient=interview.application.assigned_recruiter,
            notification_type=NotificationType.INTERVIEW_UPDATED,
            title="Interview updated",
            body=f"Interview updated for {interview.application.candidate.full_name}.",
            action_url=f"/recruiter/applications/{interview.application_id}",
            payload={"application_id": str(interview.application_id), "interview_id": str(interview.id), "status": interview.status},
        )
    if previous_status != interview.status and interview.status == InterviewStatus.COMPLETED:
        RecruitingService.transition_application(
            actor=request.user,
            application=interview.application,
            stage=ApplicationStage.INTERVIEW_COMPLETED,
            message="Interview completed.",
        )
    return _success(InterviewSerializer(interview).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def interview_feedback(request, organization_id, interview_id):
    organization = _get_recruiting_org(request.user, organization_id)
    interview = get_object_or_404(Interview, id=interview_id, organization=organization)
    if not PermissionService.can_manage_interview(request.user, interview):
        raise PermissionError("You cannot add feedback.")
    serializer = InterviewFeedbackSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    feedback, _ = InterviewFeedback.objects.update_or_create(
        interview=interview,
        author=request.user,
        defaults=serializer.validated_data,
    )
    RecruitingService.create_timeline(interview.application, request.user, "interview_feedback_added", message="Interview feedback added.")
    return _success(InterviewFeedbackSerializer(feedback).data, status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def interview_scorecard(request, organization_id, interview_id):
    organization = _get_recruiting_org(request.user, organization_id)
    interview = get_object_or_404(Interview, id=interview_id, organization=organization)
    if not PermissionService.can_manage_interview(request.user, interview):
        raise PermissionError("You cannot add a scorecard.")
    serializer = InterviewScorecardSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    scorecard, _ = InterviewScorecard.objects.update_or_create(
        interview=interview,
        author=request.user,
        defaults=serializer.validated_data,
    )
    RecruitingService.create_timeline(interview.application, request.user, "interview_scorecard_added", message="Interview scorecard added.")
    return _success(InterviewScorecardSerializer(scorecard).data, status.HTTP_201_CREATED)
