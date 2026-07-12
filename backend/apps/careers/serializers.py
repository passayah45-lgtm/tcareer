"""
Serializers for the careers domain.

Serializer strategy:
- Read serializers are optimized for public display (minimal data, no sensitive fields)
- Write serializers validate all input strictly
- The public portfolio serializer assembles data from multiple models
- The recruiter view extends the public view with contact and match signals
"""

import uuid
from rest_framework import serializers
from apps.certificates.models import Certificate
from apps.courses.models import Enrollment, EnrollmentStatus
from common.uploads import UploadValidationService
from .models import (
    CareerResume,
    Portfolio,
    PortfolioSkill,
    PortfolioProject,
    PortfolioProjectMedia,
    PortfolioAIReview,
    Resume,
    ResumeAnalytics,
    ResumeAIReview,
    ResumeFile,
    ResumeVersion,
    VisibilityChoice,
)


# ── Portfolio ─────────────────────────────────────────────────────────────────

class PortfolioSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioSkill
        fields = ["id", "name", "category", "source", "position", "created_at"]
        read_only_fields = ["id", "source", "created_at"]


class PortfolioSkillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioSkill
        fields = ["name", "category", "position"]

    def validate_name(self, value):
        return value.strip()

    def validate(self, attrs):
        portfolio = self.context["portfolio"]
        name = attrs.get("name", "").strip()
        if PortfolioSkill.objects.filter(portfolio=portfolio, name__iexact=name).exists():
            raise serializers.ValidationError(
                {"name": "You already have this skill on your portfolio."}
            )
        return attrs


class PortfolioProjectSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioProject
        fields = [
            "id", "title", "description", "tech_stack",
            "project_url", "github_url", "demo_video_url",
            "thumbnail_url", "gallery_urls",
            "is_featured", "position", "start_date", "end_date",
            "created_at", "updated_at", "media",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_media(self, obj):
        media = obj.media.all()
        request = self.context.get("request")
        if not request or request.user != obj.portfolio.user:
            media = media.exclude(visibility=VisibilityChoice.PRIVATE)
        return PortfolioProjectMediaSerializer(media, many=True).data

    def validate_tech_stack(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("tech_stack must be a list.")
        if len(value) > 20:
            raise serializers.ValidationError("Maximum 20 technologies allowed.")
        return [str(t).strip() for t in value if str(t).strip()]

    def validate_gallery_urls(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("gallery_urls must be a list.")
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 gallery images allowed.")
        return value

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )
        return attrs


class PortfolioProjectMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioProjectMedia
        fields = [
            "id", "project", "media_type", "url", "file_name", "content_type", "file_size",
            "title", "description", "visibility", "position", "is_featured", "created_at",
        ]
        read_only_fields = ["id", "project", "created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get("url") and instance.file:
            data["url"] = instance.file.url
        return data

    def validate(self, attrs):
        file_name = attrs.get("file_name")
        content_type = attrs.get("content_type")
        file_size = attrs.get("file_size")
        if file_name or content_type or file_size:
            UploadValidationService.validate_metadata(
                file_name=file_name or "",
                content_type=content_type or "",
                file_size=file_size or 0,
                allowed_extensions={".png", ".jpg", ".jpeg", ".webp"},
                allowed_mime_types={"image/png", "image/jpeg", "image/webp"},
                max_size_bytes=8 * 1024 * 1024,
            )
        return attrs


class PortfolioSerializer(serializers.ModelSerializer):
    """Used for the owner's own portfolio view and update."""
    skills = PortfolioSkillSerializer(many=True, read_only=True)
    projects = PortfolioProjectSerializer(many=True, read_only=True)
    public_url = serializers.ReadOnlyField()
    username = serializers.CharField(source="user.username", read_only=True)
    avatar_url = serializers.CharField(source="user.avatar_url", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "id", "username", "full_name", "avatar_url",
            "headline", "bio", "location", "desired_role", "experience_level",
            "linkedin_url", "github_url", "website_url",
            "visibility", "profile_views", "public_url",
            "skills", "projects",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "username", "full_name", "avatar_url",
            "profile_views", "public_url", "created_at", "updated_at",
        ]


class PortfolioUpdateSerializer(serializers.ModelSerializer):
    """Used for PATCH requests to update portfolio fields."""
    class Meta:
        model = Portfolio
        fields = [
            "headline", "bio", "location", "desired_role", "experience_level",
            "linkedin_url", "github_url", "website_url", "visibility",
        ]

    def validate_visibility(self, value):
        if value not in [v[0] for v in VisibilityChoice.choices]:
            raise serializers.ValidationError("Invalid visibility value.")
        return value


# ── Public portfolio (no auth required) ───────────────────────────────────────

class PublicCertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)

    class Meta:
        model = Certificate
        fields = ["cert_number", "course_title", "course_slug", "issued_at", "verify_url"]


class PublicCompletedCourseSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="course.title", read_only=True)
    slug = serializers.CharField(source="course.slug", read_only=True)
    thumbnail_url = serializers.CharField(source="course.thumbnail_url", read_only=True)
    level = serializers.CharField(source="course.level", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["title", "slug", "thumbnail_url", "level", "completed_at"]


class PublicPortfolioSerializer(serializers.ModelSerializer):
    """
    Public-facing portfolio response.
    Assembles data from Portfolio, Certificate, and Enrollment models.
    Only returned when portfolio visibility is public or unlisted.
    """
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    avatar_url = serializers.CharField(source="user.avatar_url", read_only=True)
    skills = PortfolioSkillSerializer(many=True, read_only=True)
    projects = PortfolioProjectSerializer(many=True, read_only=True)
    certificates = serializers.SerializerMethodField()
    completed_courses = serializers.SerializerMethodField()
    career_tracks = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    open_to_work = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField(source="user.is_verified", read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "username", "full_name", "avatar_url",
            "headline", "bio", "location", "desired_role", "experience_level",
            "linkedin_url", "github_url", "website_url", "preferred_work_country",
            "relocation_willingness", "remote_preference", "availability",
            "open_to_work", "is_verified", "education", "experience",
            "skills", "projects",
            "certificates", "completed_courses", "career_tracks",
        ]

    def get_certificates(self, obj):
        certs = Certificate.objects.filter(
            user=obj.user, is_revoked=False
        ).select_related("course").order_by("-issued_at")
        return PublicCertificateSerializer(certs, many=True).data

    def get_completed_courses(self, obj):
        enrollments = Enrollment.objects.filter(
            user=obj.user, status=EnrollmentStatus.COMPLETED
        ).select_related("course").order_by("-completed_at")
        return PublicCompletedCourseSerializer(enrollments, many=True).data

    def get_career_tracks(self, obj):
        from apps.tracks.serializers import UserTrackEnrollmentSerializer
        from apps.tracks.models import UserTrackEnrollment
        track_enrollments = UserTrackEnrollment.objects.filter(
            user=obj.user
        ).select_related("track").order_by("-created_at")
        return UserTrackEnrollmentSerializer(track_enrollments, many=True).data

    def get_education(self, obj):
        resume = CareerResume.objects.filter(user=obj.user, is_default=True, is_archived=False).first()
        return resume.education if resume else []

    def get_experience(self, obj):
        resume = CareerResume.objects.filter(user=obj.user, is_default=True, is_archived=False).first()
        return resume.experience if resume else []

    def get_availability(self, obj):
        return {
            "remote_preference": obj.remote_preference,
            "relocation_willingness": obj.relocation_willingness,
            "preferred_work_country": obj.preferred_work_country,
        }

    def get_open_to_work(self, obj):
        return obj.visibility == VisibilityChoice.PUBLIC


class RecruiterPortfolioSerializer(PublicPortfolioSerializer):
    """
    Extended portfolio view for authenticated recruiters.
    Adds contact signals and match-readiness indicators.
    Does not expose private contact details - only what the student made public.
    """
    certificate_count = serializers.SerializerMethodField()
    completed_course_count = serializers.SerializerMethodField()
    skill_count = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()
    profile_completeness = serializers.SerializerMethodField()

    class Meta(PublicPortfolioSerializer.Meta):
        fields = PublicPortfolioSerializer.Meta.fields + [
            "certificate_count", "completed_course_count",
            "skill_count", "project_count", "profile_completeness",
        ]

    def get_certificate_count(self, obj):
        return Certificate.objects.filter(user=obj.user, is_revoked=False).count()

    def get_completed_course_count(self, obj):
        return Enrollment.objects.filter(
            user=obj.user, status=EnrollmentStatus.COMPLETED
        ).count()

    def get_skill_count(self, obj):
        return obj.skills.count()

    def get_project_count(self, obj):
        return obj.projects.count()

    def get_profile_completeness(self, obj):
        """
        Returns a completeness score from 0-100.
        Used by recruiters to assess how complete a profile is.
        Weights are intentionally biased toward verifiable achievements.
        """
        score = 0
        if obj.headline:
            score += 10
        if obj.bio and len(obj.bio) > 50:
            score += 10
        if obj.location:
            score += 5
        if obj.desired_role:
            score += 10
        if obj.linkedin_url:
            score += 5
        if obj.github_url:
            score += 5
        if obj.skills.count() >= 3:
            score += 15
        if obj.projects.count() >= 1:
            score += 15
        if Certificate.objects.filter(user=obj.user, is_revoked=False).count() >= 1:
            score += 15
        if Enrollment.objects.filter(
            user=obj.user, status=EnrollmentStatus.COMPLETED
        ).count() >= 1:
            score += 10
        return min(score, 100)


# ── Resume ─────────────────────────────────────────────────────────────────────

class EducationItemSerializer(serializers.Serializer):
    """Validates a single education entry in the resume."""
    id = serializers.UUIDField(default=uuid.uuid4)
    institution = serializers.CharField(max_length=200)
    degree = serializers.CharField(max_length=200, allow_blank=True, default="")
    field = serializers.CharField(max_length=200, allow_blank=True, default="")
    start_year = serializers.IntegerField(min_value=1950, max_value=2100)
    end_year = serializers.IntegerField(min_value=1950, max_value=2100, allow_null=True, required=False)
    grade = serializers.CharField(max_length=100, allow_blank=True, default="")
    description = serializers.CharField(allow_blank=True, default="")

    def validate(self, attrs):
        start = attrs.get("start_year")
        end = attrs.get("end_year")
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_year": "End year cannot be before start year."}
            )
        return attrs

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)


class ExperienceItemSerializer(serializers.Serializer):
    """Validates a single experience entry in the resume."""
    id = serializers.UUIDField(default=uuid.uuid4)
    company = serializers.CharField(max_length=200)
    title = serializers.CharField(max_length=200)
    location = serializers.CharField(max_length=200, allow_blank=True, default="")
    start_date = serializers.CharField(max_length=7, help_text="Format: YYYY-MM")
    end_date = serializers.CharField(max_length=7, allow_blank=True, default="")
    is_current = serializers.BooleanField(default=False)
    description = serializers.CharField(allow_blank=True, default="")

    def validate_start_date(self, value):
        import re
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise serializers.ValidationError("start_date must be in YYYY-MM format.")
        return value

    def validate_end_date(self, value):
        import re
        if value and not re.match(r"^\d{4}-\d{2}$", value):
            raise serializers.ValidationError("end_date must be in YYYY-MM format.")
        return value

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)


class ResumeSerializer(serializers.ModelSerializer):
    """Full resume serializer with nested section data."""
    certificates = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            "id", "title", "summary", "target_role",
            "education", "experience",
            "certificates", "skills",
            "pdf_url", "last_generated_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "pdf_url", "last_generated_at", "created_at", "updated_at"]

    def get_certificates(self, obj):
        certs = Certificate.objects.filter(
            user=obj.user, is_revoked=False
        ).select_related("course").order_by("-issued_at")
        return PublicCertificateSerializer(certs, many=True).data

    def get_skills(self, obj):
        try:
            portfolio = obj.user.portfolio
            return PortfolioSkillSerializer(
                portfolio.skills.all(), many=True
            ).data
        except Portfolio.DoesNotExist:
            return []


class ResumeUpdateSerializer(serializers.ModelSerializer):
    """Validates resume updates including JSONB section arrays."""
    education = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        max_length=10,
    )
    experience = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        max_length=15,
    )

    class Meta:
        model = Resume
        fields = ["title", "summary", "target_role", "education", "experience"]

    def validate_education(self, value):
        serializer = EducationItemSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return [
            {**item, "id": str(item["id"])}
            for item in serializer.validated_data
        ]

    def validate_experience(self, value):
        serializer = ExperienceItemSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return [
            {**item, "id": str(item["id"])}
            for item in serializer.validated_data
        ]


class ResumeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeFile
        fields = ["id", "resume", "file_url", "file_name", "content_type", "file_size", "is_private", "created_at"]
        read_only_fields = ["id", "resume", "created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get("file_url") and instance.file:
            data["file_url"] = instance.file.url
        return data

    def validate(self, attrs):
        file_name = attrs.get("file_name")
        content_type = attrs.get("content_type")
        file_size = attrs.get("file_size")
        if file_name or content_type or file_size:
            UploadValidationService.validate_metadata(
                file_name=file_name or "",
                content_type=content_type or "",
                file_size=file_size or 0,
                allowed_extensions={".pdf", ".doc", ".docx"},
                allowed_mime_types={
                    "application/pdf",
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                },
                max_size_bytes=5 * 1024 * 1024,
            )
        attrs["is_private"] = True
        return attrs


class ResumeAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAnalytics
        fields = ["id", "event_type", "metadata", "created_at"]


class ResumeVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeVersion
        fields = ["id", "version_number", "snapshot", "change_summary", "created_at"]


class CareerResumeSerializer(serializers.ModelSerializer):
    files = ResumeFileSerializer(many=True, read_only=True)
    versions = ResumeVersionSerializer(many=True, read_only=True)
    analytics = ResumeAnalyticsSerializer(many=True, read_only=True)
    ai_reviews = serializers.SerializerMethodField()
    analytics_summary = serializers.SerializerMethodField()

    class Meta:
        model = CareerResume
        fields = [
            "id", "title", "summary", "target_role", "education", "experience", "skills",
            "is_default", "is_archived", "files", "versions", "analytics", "ai_reviews", "analytics_summary",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_ai_reviews(self, obj):
        return ResumeAIReviewSerializer(obj.ai_reviews.all()[:5], many=True).data

    def get_analytics_summary(self, obj):
        return {
            "views": obj.analytics.filter(event_type=ResumeAnalytics.EventType.VIEWED_BY_RECRUITER).count(),
            "downloads": obj.analytics.filter(event_type=ResumeAnalytics.EventType.DOWNLOADED).count(),
            "applications": obj.analytics.filter(event_type=ResumeAnalytics.EventType.USED_FOR_APPLICATION).count(),
        }


class CareerResumeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerResume
        fields = ["title", "summary", "target_role", "education", "experience", "skills", "is_default"]

    def validate_experience(self, value):
        serializer = ExperienceItemSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return [
            {**item, "id": str(item["id"])}
            for item in serializer.validated_data
        ]


class ResumeAIReviewSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    comparison_resume_title = serializers.CharField(source="comparison_resume.title", read_only=True)

    class Meta:
        model = ResumeAIReview
        fields = [
            "id",
            "resume",
            "review_type",
            "job",
            "job_title",
            "comparison_resume",
            "comparison_resume_title",
            "prompt_version",
            "model_name",
            "estimated_cost",
            "overall_score",
            "ats_score",
            "match_score",
            "confidence",
            "extracted_skills",
            "missing_skills",
            "strengths",
            "weaknesses",
            "suggestions",
            "action_items",
            "report",
            "summary",
            "created_at",
        ]
        read_only_fields = fields


class ResumeAIRecruiterSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAIReview
        fields = [
            "id",
            "review_type",
            "overall_score",
            "ats_score",
            "match_score",
            "confidence",
            "extracted_skills",
            "missing_skills",
            "strengths",
            "weaknesses",
            "summary",
            "created_at",
        ]
        read_only_fields = fields


class ResumeAIJobMatchRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()


class ResumeAIComparisonRequestSerializer(serializers.Serializer):
    comparison_resume_id = serializers.UUIDField()


class PortfolioAIReviewSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = PortfolioAIReview
        fields = [
            "id",
            "portfolio",
            "review_type",
            "project",
            "project_title",
            "job",
            "job_title",
            "prompt_version",
            "model_name",
            "estimated_cost",
            "overall_score",
            "project_score",
            "github_score",
            "match_score",
            "confidence",
            "extracted_skills",
            "missing_skills",
            "technology_stack",
            "strengths",
            "weaknesses",
            "suggestions",
            "action_items",
            "report",
            "summary",
            "created_at",
        ]
        read_only_fields = fields


class PortfolioAIRecruiterSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioAIReview
        fields = [
            "id",
            "review_type",
            "overall_score",
            "project_score",
            "github_score",
            "match_score",
            "confidence",
            "technology_stack",
            "strengths",
            "weaknesses",
            "summary",
            "created_at",
        ]
        read_only_fields = fields


class PortfolioAIProjectRequestSerializer(serializers.Serializer):
    project_id = serializers.UUIDField()


class PortfolioAIJobMatchRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
