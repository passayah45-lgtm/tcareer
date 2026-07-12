"""
Service layer for the careers domain.

All business logic lives here. Views are thin wrappers that call services.
This separation makes logic testable without HTTP context.
"""

import logging
import re
from collections import Counter
from io import BytesIO
from decimal import Decimal

from django.utils import timezone

from apps.ai_platform.models import AIFeature
from apps.ai_platform.services import AIService
from apps.analytics.services import AnalyticsService
from common.audit import AuditService
from .models import (
    CareerResume,
    Portfolio,
    PortfolioAIReview,
    PortfolioAIReviewType,
    PortfolioProject,
    PortfolioSkill,
    ResumeAIReview,
    ResumeAIReviewType,
    SkillSource,
)

logger = logging.getLogger(__name__)


SKILL_CATEGORIES = {
    "technical_skills": {
        "python", "django", "javascript", "typescript", "react", "next.js", "sql", "postgresql", "mysql",
        "excel", "power bi", "tableau", "html", "css", "node.js", "rest api", "graphql", "git", "docker",
    },
    "soft_skills": {"communication", "leadership", "teamwork", "problem solving", "collaboration", "mentoring"},
    "languages": {"english", "french", "spanish", "arabic", "hindi", "mandarin"},
    "tools": {"git", "jira", "figma", "excel", "power bi", "tableau", "notion", "slack"},
    "frameworks": {"django", "react", "next.js", "fastapi", "express", "tailwind"},
    "platforms": {"linux", "wordpress", "salesforce", "shopify"},
    "cloud_providers": {"aws", "azure", "google cloud", "gcp"},
    "databases": {"postgresql", "mysql", "sqlite", "mongodb", "redis"},
    "certificates": {"aws certified", "google data analytics", "pmp", "scrum master"},
}


def _clamp(value, low=0, high=100):
    return max(low, min(high, int(round(value))))


class PortfolioService:

    @staticmethod
    def get_or_create(user) -> Portfolio:
        """
        Get the user's portfolio, creating it if it does not exist.
        On creation, pre-fills fields from the User model so the student
        does not have to re-enter information they already provided.
        """
        portfolio, created = Portfolio.objects.get_or_create(
            user=user,
            defaults={
                "headline": user.profile_headline or "",
                "bio": user.profile_bio or "",
                "location": user.profile_location or "",
                "linkedin_url": user.linkedin_url or "",
                "github_url": user.github_url or "",
            },
        )
        if created:
            logger.info("Portfolio created for user %s", user.email)
        return portfolio

    @staticmethod
    def sync_skills_from_courses(portfolio: Portfolio) -> dict:
        """
        Auto-import skills from the student's completed course enrollments.
        Pulls the course category and any skills listed on completed tracks.
        Returns a dict with counts of added and skipped skills.
        """
        from apps.courses.models import Enrollment, EnrollmentStatus

        added = 0
        skipped = 0

        completed_enrollments = Enrollment.objects.filter(
            user=portfolio.user,
            status=EnrollmentStatus.COMPLETED,
        ).select_related("course")

        for enrollment in completed_enrollments:
            course = enrollment.course
            skill_name = course.title

            existing = PortfolioSkill.objects.filter(
                portfolio=portfolio, name__iexact=skill_name
            ).exists()

            if existing:
                skipped += 1
                continue

            position = PortfolioSkill.objects.filter(portfolio=portfolio).count()
            PortfolioSkill.objects.create(
                portfolio=portfolio,
                name=skill_name,
                category="Course",
                source=SkillSource.COURSE,
                source_id=course.id,
                position=position,
            )
            added += 1

        return {"added": added, "skipped": skipped}

    @staticmethod
    def sync_skills_from_tracks(portfolio: Portfolio) -> dict:
        """
        Auto-import skills from career tracks the student is enrolled in.
        Pulls from the track's skills_acquired JSON field.
        """
        from apps.tracks.models import UserTrackEnrollment

        added = 0
        skipped = 0

        track_enrollments = UserTrackEnrollment.objects.filter(
            user=portfolio.user
        ).select_related("track")

        for te in track_enrollments:
            skills = te.track.skills_acquired or []
            for skill_name in skills:
                if not skill_name:
                    continue

                existing = PortfolioSkill.objects.filter(
                    portfolio=portfolio, name__iexact=skill_name
                ).exists()

                if existing:
                    skipped += 1
                    continue

                position = PortfolioSkill.objects.filter(portfolio=portfolio).count()
                PortfolioSkill.objects.create(
                    portfolio=portfolio,
                    name=skill_name,
                    category="Track Skill",
                    source=SkillSource.TRACK,
                    source_id=te.track.id,
                    position=position,
                )
                added += 1

        return {"added": added, "skipped": skipped}

    @staticmethod
    def increment_profile_views(portfolio: Portfolio) -> None:
        """Increment profile view count atomically."""
        Portfolio.objects.filter(pk=portfolio.pk).update(
            profile_views=portfolio.profile_views + 1
        )


class ResumeService:

    @staticmethod
    def get_or_create(user):
        """
        Get the user's resume, creating it with defaults if it does not exist.
        """
        from .models import Resume
        resume, created = Resume.objects.get_or_create(
            user=user,
            defaults={
                "title": f"{user.get_full_name()} - Resume",
                "summary": "",
                "education": [],
                "experience": [],
            },
        )
        if created:
            logger.info("Resume created for user %s", user.email)
        return resume

    @staticmethod
    def generate_pdf(resume) -> str:
        """
        Generate a PDF from the resume and upload it to S3.
        Returns the S3 URL of the generated PDF.

        Falls back gracefully if WeasyPrint or S3 is not available.
        """
        import base64
        from django.template.loader import render_to_string
        from apps.certificates.models import Certificate
        from apps.courses.models import Enrollment, EnrollmentStatus

        try:
            from weasyprint import HTML
        except ImportError:
            logger.warning("WeasyPrint not available. Resume PDF not generated.")
            return ""

        certificates = Certificate.objects.filter(
            user=resume.user, is_revoked=False
        ).select_related("course").order_by("-issued_at")

        try:
            portfolio = resume.user.portfolio
            skills = list(portfolio.skills.values_list("name", flat=True))
        except Exception:
            skills = []

        context = {
            "resume": resume,
            "user": resume.user,
            "certificates": certificates,
            "skills": skills,
        }

        html_content = render_to_string("resume/resume.html", context)

        try:
            buf = BytesIO()
            HTML(string=html_content).write_pdf(buf)
            buf.seek(0)

            from common.storage import upload_to_s3
            s3_key = f"resumes/{resume.user.id}/resume.pdf"
            pdf_url = upload_to_s3(buf, s3_key, content_type="application/pdf")

            resume.pdf_url = pdf_url
            resume.last_generated_at = timezone.now()
            resume.save(update_fields=["pdf_url", "last_generated_at"])

            logger.info("Resume PDF generated for user %s: %s", resume.user.email, pdf_url)
            return pdf_url

        except Exception as exc:
            logger.error("Resume PDF generation failed for %s: %s", resume.user.email, exc)
            return ""


class ResumeIntelligenceService:
    PROMPT_VERSION = "resume-intelligence-v1"

    @staticmethod
    def resume_text(resume: CareerResume) -> str:
        education = "\n".join(
            f"{item.get('degree', '')} {item.get('field', '')} at {item.get('institution', '')} {item.get('description', '')}"
            for item in (resume.education or [])
        )
        experience = "\n".join(
            f"{item.get('title', '')} at {item.get('company', '')}: {item.get('description', '')}"
            for item in (resume.experience or [])
        )
        skills = ", ".join(resume.skills or [])
        return (
            f"Title: {resume.title}\nTarget role: {resume.target_role}\nSummary: {resume.summary}\n"
            f"Skills: {skills}\nExperience:\n{experience}\nEducation:\n{education}"
        ).strip()

    @staticmethod
    def job_text(job) -> str:
        if job is None:
            return ""
        return (
            f"Job: {job.title} at {job.company_name}\n"
            f"Description: {job.description}\n"
            f"Requirements: {', '.join(job.requirements or [])}\n"
            f"Required skills: {', '.join(job.required_skills or [])}\n"
            f"Preferred skills: {', '.join(job.preferred_skills or [])}\n"
            f"Experience level: {job.experience_level}"
        ).strip()

    @staticmethod
    def _words(text: str) -> set[str]:
        return {word.lower() for word in re.findall(r"[a-zA-Z][a-zA-Z0-9.+#-]{1,}", text or "")}

    @staticmethod
    def extract_skills_from_text(text: str, *, known_skills=None) -> dict:
        lowered = f" {text.lower()} "
        extracted = {category: [] for category in SKILL_CATEGORIES}
        catalog = {skill.lower(): skill for skill in (known_skills or []) if skill}
        for category, terms in SKILL_CATEGORIES.items():
            matches = sorted({term for term in terms if f" {term.lower()} " in lowered or term.lower() in lowered})
            extracted[category] = matches
        extracted["catalog_matches"] = sorted({label for key, label in catalog.items() if key in lowered})
        return extracted

    @staticmethod
    def normalize_skills(resume: CareerResume, extracted: dict) -> dict:
        catalog_names = list(PortfolioSkill.objects.values_list("name", flat=True).distinct())
        catalog_lookup = {name.lower(): name for name in catalog_names}
        all_skills = {str(skill).strip().lower(): str(skill).strip() for skill in (resume.skills or []) if str(skill).strip()}
        for values in extracted.values():
            if isinstance(values, list):
                for value in values:
                    all_skills[str(value).strip().lower()] = str(value).strip()
        normalized = sorted(catalog_lookup.get(key, value) for key, value in all_skills.items())
        return {
            "normalized": normalized,
            "catalog_matches": sorted({catalog_lookup[key] for key in all_skills if key in catalog_lookup}),
            "uncataloged": sorted(value for key, value in all_skills.items() if key not in catalog_lookup),
        }


class PortfolioIntelligenceService:
    PROMPT_VERSION = "portfolio-intelligence-v1"

    @staticmethod
    def portfolio_text(portfolio: Portfolio) -> str:
        skills = ", ".join(portfolio.skills.values_list("name", flat=True))
        projects = "\n".join(
            f"{project.title}: {project.description} | Tech: {', '.join(project.tech_stack or [])} | GitHub: {project.github_url} | Demo: {project.project_url}"
            for project in portfolio.projects.all()
        )
        return (
            f"Headline: {portfolio.headline}\nBio: {portfolio.bio}\nDesired role: {portfolio.desired_role}\n"
            f"Experience level: {portfolio.experience_level}\nSkills: {skills}\nProjects:\n{projects}"
        ).strip()

    @staticmethod
    def project_text(project: PortfolioProject) -> str:
        return (
            f"Project: {project.title}\nDescription: {project.description}\nTech: {', '.join(project.tech_stack or [])}\n"
            f"GitHub: {project.github_url}\nLive demo: {project.project_url}\nVideo: {project.demo_video_url}\n"
            f"Featured: {project.is_featured}"
        ).strip()

    @staticmethod
    def _project_quality(project: PortfolioProject) -> dict:
        tech_count = len(project.tech_stack or [])
        has_github = bool(project.github_url)
        has_demo = bool(project.project_url)
        has_media = project.media.count() > 0
        description_len = len(project.description or "")
        return {
            "architecture": _clamp(45 + tech_count * 7 + int(has_github) * 12),
            "technology_choices": _clamp(50 + tech_count * 8),
            "code_organization": 75 if has_github else 45,
            "innovation": _clamp(45 + int(project.is_featured) * 15 + tech_count * 3),
            "complexity": _clamp(40 + tech_count * 8 + int(description_len > 160) * 10),
            "business_relevance": _clamp(45 + int(description_len > 120) * 20 + int(has_demo) * 10),
            "scalability": _clamp(45 + int("docker" in [t.lower() for t in (project.tech_stack or [])]) * 15 + tech_count * 3),
            "testing": 55 if has_github else 35,
            "deployment_readiness": _clamp(45 + int(has_demo) * 25 + int(has_github) * 10),
            "documentation": _clamp(45 + int(description_len > 100) * 25 + int(has_github) * 10),
            "portfolio_presentation": _clamp(50 + int(has_media) * 20 + int(project.is_featured) * 10),
        }

    @staticmethod
    def _github_report(project: PortfolioProject | None, portfolio: Portfolio) -> dict:
        github_urls = []
        if project and project.github_url:
            github_urls.append(project.github_url)
        github_urls.extend(p.github_url for p in portfolio.projects.all() if p.github_url)
        if portfolio.github_url:
            github_urls.append(portfolio.github_url)
        unique_urls = list(dict.fromkeys(url for url in github_urls if url))
        if not unique_urls:
            return {
                "available": False,
                "github_quality_score": 0,
                "message": "No GitHub repository or profile URL is available.",
                "recommendations": ["Add a GitHub repository link for at least one featured project."],
                "missing_repository_standards": ["README", "license", "tests", "CI/CD"],
            }
        score = _clamp(45 + len(unique_urls) * 8 + sum("github.com" in url.lower() for url in unique_urls) * 8)
        return {
            "available": True,
            "repositories": unique_urls,
            "repository_structure": "not_fetched",
            "readme_quality": "unknown_without_provider_fetch",
            "commit_activity": "unknown_without_provider_fetch",
            "project_maturity": "estimated_from_links",
            "languages": [],
            "frameworks": [],
            "testing_presence": "unknown",
            "ci_cd_presence": "unknown",
            "license": "unknown",
            "github_quality_score": score,
            "recommendations": ["Add clear README setup steps, screenshots, tests, license, and deployment instructions."],
            "missing_repository_standards": ["Verified README quality", "Test evidence", "CI/CD evidence", "License evidence"],
        }

    @staticmethod
    def _portfolio_scores(portfolio: Portfolio, github_report: dict) -> dict:
        projects = list(portfolio.projects.all())
        project_scores = [sum(PortfolioIntelligenceService._project_quality(project).values()) / 11 for project in projects]
        skills = list(portfolio.skills.values_list("name", flat=True))
        tech_stack = {tech for project in projects for tech in (project.tech_stack or [])}
        return {
            "overall_portfolio": _clamp(45 + len(projects) * 8 + len(skills) * 2 + int(bool(portfolio.bio)) * 8),
            "project_quality": _clamp(sum(project_scores) / len(project_scores)) if project_scores else 25,
            "project_diversity": _clamp(35 + len(tech_stack) * 6 + len(projects) * 5),
            "technical_depth": _clamp(40 + len(tech_stack) * 5 + github_report.get("github_quality_score", 0) * 0.2),
            "business_impact": _clamp(45 + sum(1 for p in projects if len(p.description or "") > 120) * 12),
            "problem_solving": _clamp(45 + sum(1 for p in projects if p.description) * 10),
            "code_quality": github_report.get("github_quality_score", 0) or 45,
            "documentation_quality": _clamp(45 + sum(1 for p in projects if len(p.description or "") > 100) * 12),
            "design_quality": _clamp(45 + sum(1 for p in projects if p.media.exists() or p.thumbnail_url) * 12),
            "presentation_quality": _clamp(45 + int(bool(portfolio.headline)) * 10 + int(bool(portfolio.bio)) * 10 + len(projects) * 5),
            "completeness": _clamp(35 + int(bool(portfolio.headline)) * 10 + int(bool(portfolio.bio)) * 10 + len(skills) * 3 + len(projects) * 8),
            "professionalism": _clamp(55 + int(bool(portfolio.linkedin_url)) * 8 + int(bool(portfolio.github_url)) * 8 + int(bool(portfolio.website_url)) * 8),
            "storytelling": _clamp(45 + int(len(portfolio.bio or "") > 120) * 25 + sum(1 for p in projects if len(p.description or "") > 100) * 5),
            "consistency": _clamp(55 + int(bool(portfolio.desired_role)) * 10 + int(bool(skills)) * 10),
        }

    @staticmethod
    def _extract_skills(portfolio: Portfolio) -> dict:
        text = PortfolioIntelligenceService.portfolio_text(portfolio)
        extracted = ResumeIntelligenceService.extract_skills_from_text(
            text,
            known_skills=list(PortfolioSkill.objects.values_list("name", flat=True).distinct()),
        )
        project_tech = sorted({tech for project in portfolio.projects.all() for tech in (project.tech_stack or []) if tech})
        portfolio_skills = list(portfolio.skills.values_list("name", flat=True))
        normalized = sorted(set(project_tech + portfolio_skills + extracted.get("catalog_matches", [])))
        extracted["normalized"] = normalized
        extracted["project_technologies"] = project_tech
        extracted["duplicate_skills"] = sorted([skill for skill, count in Counter([s.lower() for s in portfolio_skills]).items() if count > 1])
        extracted["emerging_skills"] = [skill for skill in normalized if skill.lower() in {"ai", "machine learning", "next.js", "cloud", "docker"}]
        return extracted

    @staticmethod
    def _match_job(portfolio: Portfolio, job) -> dict:
        if job is None:
            return {}
        extracted = PortfolioIntelligenceService._extract_skills(portfolio)
        portfolio_skill_set = {skill.lower() for skill in extracted.get("normalized", [])}
        required = [str(skill).strip() for skill in (job.required_skills or []) if str(skill).strip()]
        preferred = [str(skill).strip() for skill in (job.preferred_skills or []) if str(skill).strip()]
        matched = [skill for skill in required + preferred if skill.lower() in portfolio_skill_set]
        missing = [skill for skill in required if skill.lower() not in portfolio_skill_set]
        project_text = " ".join(project.title + " " + project.description + " " + " ".join(project.tech_stack or []) for project in portfolio.projects.all()).lower()
        relevant_projects = [project.title for project in portfolio.projects.all() if any(skill.lower() in project_text for skill in required + preferred)]
        denominator = max(len(required) + len(preferred) * 0.5, 1)
        score = _clamp((len([s for s in required if s.lower() in portfolio_skill_set]) + len([s for s in preferred if s.lower() in portfolio_skill_set]) * 0.5) / denominator * 100)
        return {
            "job_id": str(job.id),
            "job_title": job.title,
            "portfolio_match_score": score,
            "project_relevance": relevant_projects[:8],
            "skill_overlap": matched,
            "missing_skills": missing,
            "experience_relevance": "strong" if portfolio.desired_role and portfolio.desired_role.lower() in job.title.lower() else "developing",
            "technology_overlap": matched,
            "confidence": _clamp(62 + len(required) * 3),
            "why_it_matches": f"Portfolio overlaps with {len(matched)} listed job technologies or skills.",
            "why_it_does_not": f"Missing required skills: {', '.join(missing) if missing else 'none detected'}.",
            "recommended_portfolio_improvements": [f"Add a project demonstrating {skill}." for skill in missing[:5]],
            "projects_to_build_next": [f"Build a {job.title} case study using {', '.join(missing[:3]) or 'the job stack'}."],
        }

    @staticmethod
    def _call_ai(user, *, input_text, feature=AIFeature.PORTFOLIO_REVIEW, metadata=None):
        return AIService.generate_text(user=user, feature=feature, input_text=input_text, metadata=metadata or {})

    @staticmethod
    def _model_name(ai_result) -> str:
        request = ai_result.get("request") if ai_result else None
        model = getattr(request, "model_configuration", None)
        return getattr(model, "model_name", "") if model else ""

    @staticmethod
    def create_review(*, user, portfolio: Portfolio, review_type: str, project=None, job=None) -> PortfolioAIReview:
        portfolio_text = PortfolioIntelligenceService.portfolio_text(portfolio)
        project_text = PortfolioIntelligenceService.project_text(project) if project else ""
        job_text = ResumeIntelligenceService.job_text(job)
        feature = AIFeature.JOB_MATCHING if review_type == PortfolioAIReviewType.JOB_MATCH else AIFeature.PORTFOLIO_REVIEW
        if review_type == PortfolioAIReviewType.SKILL_EXTRACTION:
            feature = AIFeature.SKILL_GAP_ANALYSIS
        prompt = (
            "Return concise structured portfolio intelligence. Do not expose private reasoning.\n"
            f"Review type: {review_type}\nPortfolio:\n{portfolio_text}\nProject:\n{project_text}\nJob:\n{job_text}"
        )
        ai_result = PortfolioIntelligenceService._call_ai(
            user,
            feature=feature,
            input_text=prompt,
            metadata={"portfolio_id": str(portfolio.id), "project_id": str(project.id) if project else "", "job_id": str(job.id) if job else "", "review_type": review_type},
        )
        github_report = PortfolioIntelligenceService._github_report(project, portfolio)
        skills = PortfolioIntelligenceService._extract_skills(portfolio)
        scores = PortfolioIntelligenceService._portfolio_scores(portfolio, github_report)
        if project:
            project_scores = PortfolioIntelligenceService._project_quality(project)
            project_score = _clamp(sum(project_scores.values()) / len(project_scores))
        else:
            project_scores = {}
            project_score = scores["project_quality"]
        job_match = PortfolioIntelligenceService._match_job(portfolio, job)
        overall = scores["overall_portfolio"]
        if review_type == PortfolioAIReviewType.PROJECT_REVIEW:
            overall = project_score
        elif review_type == PortfolioAIReviewType.GITHUB_REVIEW:
            overall = github_report["github_quality_score"]
        elif review_type == PortfolioAIReviewType.JOB_MATCH:
            overall = job_match.get("portfolio_match_score", 0)
        strengths = [label.replace("_", " ").title() for label, score in scores.items() if score >= 75][:8]
        weaknesses = [label.replace("_", " ").title() for label, score in scores.items() if score < 60][:8]
        if not strengths:
            strengths = ["Portfolio has a usable foundation"]
        suggestions = [f"Improve {label.replace('_', ' ')} with clearer evidence and stronger project detail." for label, score in scores.items() if score < 65]
        if not github_report["available"]:
            suggestions.append("Add GitHub repository links for stronger technical credibility.")
        if not suggestions:
            suggestions.append("Add quantified business impact to featured projects.")
        report = {
            "summary": f"Portfolio scores {overall}/100 with {len(strengths)} strengths and {len(weaknesses)} improvement areas.",
            "portfolio_scores": scores,
            "project_scores": project_scores,
            "github": github_report,
            "skills": skills,
            "job_match": job_match,
            "project_count": portfolio.projects.count(),
            "technology_diversity": len(set(skills.get("project_technologies", []))),
            "ai_summary": ai_result.get("text", ""),
            "recommended_technologies": sorted(set(job_match.get("missing_skills", []) + github_report.get("missing_repository_standards", [])[:2]))[:8],
            "recommended_next_project": job_match.get("projects_to_build_next", ["Build one polished case study with demo, GitHub, README, tests, and measurable impact."])[0],
        }
        usage = ai_result.get("usage", {})
        review = PortfolioAIReview.objects.create(
            portfolio=portfolio,
            user=user,
            review_type=review_type,
            project=project,
            job=job,
            ai_request=ai_result.get("request"),
            ai_response=ai_result.get("response"),
            prompt_version=PortfolioIntelligenceService.PROMPT_VERSION,
            model_name=PortfolioIntelligenceService._model_name(ai_result),
            estimated_cost=Decimal(str(usage.get("estimated_cost", "0") or "0")),
            overall_score=overall,
            project_score=project_score,
            github_score=github_report["github_quality_score"],
            match_score=job_match.get("portfolio_match_score", 0),
            confidence=job_match.get("confidence", 72) if job_match else 72,
            extracted_skills=skills,
            missing_skills=job_match.get("missing_skills", []),
            technology_stack=skills.get("project_technologies", []),
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions[:10],
            action_items=[{"priority": "high" if index < 2 else "medium", "action": item} for index, item in enumerate(suggestions[:8])],
            report=report,
            summary=report["summary"],
        )
        AnalyticsService.track(name=f"portfolio_ai_{review_type}", user=user, target=portfolio, metadata={"review_id": str(review.id)})
        AuditService.record(actor=user, action=f"portfolio_ai_{review_type}", target=portfolio, metadata={"review_id": str(review.id)})
        return review

    @staticmethod
    def analytics(user, portfolio: Portfolio | None = None) -> dict:
        reviews = PortfolioAIReview.objects.filter(user=user)
        if portfolio:
            reviews = reviews.filter(portfolio=portfolio)
        scores = list(reviews.values_list("overall_score", flat=True))
        strength_counter = Counter()
        weakness_counter = Counter()
        for review in reviews:
            strength_counter.update(review.strengths or [])
            weakness_counter.update(review.weaknesses or [])
        return {
            "average_score": _clamp(sum(scores) / len(scores)) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "review_count": len(scores),
            "top_strengths": [{"label": label, "count": count} for label, count in strength_counter.most_common(8)],
            "top_weaknesses": [{"label": label, "count": count} for label, count in weakness_counter.most_common(8)],
            "score_history": [{"score": r.overall_score, "review_type": r.review_type, "created_at": r.created_at} for r in reviews.order_by("created_at")[:50]],
            "project_quality_trend": [{"score": r.project_score, "created_at": r.created_at} for r in reviews.exclude(project_score=0).order_by("created_at")[:50]],
            "skill_growth": [{"count": len(r.extracted_skills.get("normalized", [])), "created_at": r.created_at} for r in reviews.order_by("created_at")[:50]],
            "technology_diversity": [{"count": len(r.technology_stack or []), "created_at": r.created_at} for r in reviews.order_by("created_at")[:50]],
            "job_match_trend": [{"score": r.match_score, "created_at": r.created_at} for r in reviews.exclude(match_score=0).order_by("created_at")[:50]],
        }

    @staticmethod
    def _section_scores(resume: CareerResume, extracted: dict) -> dict:
        text = ResumeIntelligenceService.resume_text(resume)
        word_count = len(text.split())
        skill_count = len(set(resume.skills or []))
        experience_count = len(resume.experience or [])
        education_count = len(resume.education or [])
        action_verbs = len(re.findall(r"\b(built|created|led|improved|reduced|increased|delivered|designed|launched|managed|analyzed)\b", text.lower()))
        achievement_markers = len(re.findall(r"(\d+%|\$\d+|\b\d+\s*(users|students|projects|hours|days|weeks|months)\b)", text.lower()))
        return {
            "ats_friendliness": _clamp(55 + skill_count * 4 + experience_count * 5 + int(bool(resume.target_role)) * 8),
            "grammar": 82 if len(re.findall(r"\s{2,}", text)) < 3 else 70,
            "professional_tone": 80 if len(resume.summary or "") >= 40 else 62,
            "formatting": _clamp(65 + int(bool(resume.summary)) * 8 + experience_count * 4 + education_count * 4),
            "keyword_coverage": _clamp(45 + len(extracted.get("normalized", [])) * 5),
            "action_verbs": _clamp(45 + action_verbs * 10),
            "achievements": _clamp(40 + achievement_markers * 12),
            "education": 85 if education_count else 35,
            "experience": _clamp(40 + experience_count * 16),
            "skills": _clamp(35 + skill_count * 8),
            "projects": 65 if "project" in text.lower() else 45,
            "certifications": 70 if "cert" in text.lower() or "certificate" in text.lower() else 45,
            "length": 82 if 220 <= word_count <= 900 else (65 if word_count else 25),
        }

    @staticmethod
    def _strengths_and_weaknesses(resume: CareerResume, section_scores: dict) -> tuple[list[str], list[str]]:
        strengths = []
        weaknesses = []
        if resume.summary and len(resume.summary) >= 80:
            strengths.append("Clear professional summary")
        if len(resume.skills or []) >= 5:
            strengths.append("Solid skills section")
        if len(resume.experience or []) >= 2:
            strengths.append("Multiple experience entries")
        for label, score in section_scores.items():
            if score >= 80:
                strengths.append(label.replace("_", " ").title())
            if score < 60:
                weaknesses.append(label.replace("_", " ").title())
        if not strengths:
            strengths.append("Resume has a usable foundation")
        return list(dict.fromkeys(strengths))[:8], list(dict.fromkeys(weaknesses))[:8]

    @staticmethod
    def _suggestions(section_scores: dict, missing_skills=None) -> list[str]:
        suggestions = []
        for label, score in section_scores.items():
            if score < 65:
                suggestions.append(f"Improve {label.replace('_', ' ')} with more specific, measurable evidence.")
        if missing_skills:
            suggestions.append(f"Add evidence for missing role keywords: {', '.join(missing_skills[:6])}.")
        if not suggestions:
            suggestions.append("Tailor the top summary and skills to each job before applying.")
        return suggestions[:10]

    @staticmethod
    def _action_items(suggestions: list[str]) -> list[dict]:
        priorities = ["high", "high", "medium", "medium", "low"]
        return [
            {"priority": priorities[index] if index < len(priorities) else "low", "action": suggestion}
            for index, suggestion in enumerate(suggestions[:8])
        ]

    @staticmethod
    def _call_ai(user, *, feature, input_text, metadata):
        return AIService.generate_text(user=user, feature=feature, input_text=input_text, metadata=metadata)

    @staticmethod
    def _cost(ai_result) -> Decimal:
        usage = ai_result.get("usage", {}) if ai_result else {}
        return Decimal(str(usage.get("estimated_cost", "0") or "0"))

    @staticmethod
    def _model_name(ai_result) -> str:
        request = ai_result.get("request") if ai_result else None
        model = getattr(request, "model_configuration", None)
        return getattr(model, "model_name", "") if model else ""

    @staticmethod
    def create_review(*, user, resume: CareerResume, review_type: str, job=None, comparison_resume=None) -> ResumeAIReview:
        resume_text = ResumeIntelligenceService.resume_text(resume)
        comparison_text = ResumeIntelligenceService.resume_text(comparison_resume) if comparison_resume else ""
        job_text = ResumeIntelligenceService.job_text(job)
        feature = AIFeature.JOB_MATCHING if review_type == ResumeAIReviewType.JOB_MATCH else AIFeature.RESUME_REVIEW
        if review_type == ResumeAIReviewType.SKILL_EXTRACTION:
            feature = AIFeature.SKILL_GAP_ANALYSIS
        prompt = (
            "Return concise structured resume intelligence. Do not expose private reasoning.\n"
            f"Review type: {review_type}\nResume:\n{resume_text}\n"
            f"Job context:\n{job_text}\nComparison resume:\n{comparison_text}"
        )
        ai_result = ResumeIntelligenceService._call_ai(
            user,
            feature=feature,
            input_text=prompt,
            metadata={"resume_id": str(resume.id), "review_type": review_type, "job_id": str(job.id) if job else ""},
        )
        catalog_skills = list(PortfolioSkill.objects.values_list("name", flat=True).distinct())
        extracted = ResumeIntelligenceService.extract_skills_from_text(resume_text, known_skills=catalog_skills)
        normalized = ResumeIntelligenceService.normalize_skills(resume, extracted)
        extracted["normalized"] = normalized["normalized"]
        section_scores = ResumeIntelligenceService._section_scores(resume, extracted)
        overall_score = _clamp(sum(section_scores.values()) / max(len(section_scores), 1))
        missing_skills = []
        match_report = {}
        if job:
            resume_skill_set = {skill.lower() for skill in normalized["normalized"]}
            required = [str(skill).strip() for skill in (job.required_skills or []) if str(skill).strip()]
            preferred = [str(skill).strip() for skill in (job.preferred_skills or []) if str(skill).strip()]
            missing_skills = [skill for skill in required if skill.lower() not in resume_skill_set]
            matched = [skill for skill in required + preferred if skill.lower() in resume_skill_set]
            denominator = max(len(required) + len(preferred) * 0.5, 1)
            match_score = _clamp((len([s for s in required if s.lower() in resume_skill_set]) + len([s for s in preferred if s.lower() in resume_skill_set]) * 0.5) / denominator * 100)
            match_report = {
                "job_id": str(job.id),
                "job_title": job.title,
                "matched_skills": matched,
                "missing_skills": missing_skills,
                "keyword_overlap": sorted(ResumeIntelligenceService._words(resume_text) & ResumeIntelligenceService._words(job_text))[:30],
                "experience_fit": "strong" if resume.target_role and resume.target_role.lower() in job.title.lower() else "developing",
                "education_fit": "present" if resume.education else "not_evidenced",
                "confidence": _clamp(60 + len(required) * 3),
                "explanation": f"Matches {len(matched)} job skills and is missing {len(missing_skills)} required skills.",
            }
        else:
            match_score = 0
        if review_type == ResumeAIReviewType.ATS:
            overall_score = section_scores["ats_friendliness"]
        strengths, weaknesses = ResumeIntelligenceService._strengths_and_weaknesses(resume, section_scores)
        suggestions = ResumeIntelligenceService._suggestions(section_scores, missing_skills)
        report = {
            "summary": f"{resume.title} scores {overall_score}/100 with {len(strengths)} strengths and {len(weaknesses)} improvement areas.",
            "section_scores": section_scores,
            "missing_sections": [name for name, present in {"summary": resume.summary, "education": resume.education, "experience": resume.experience, "skills": resume.skills}.items() if not present],
            "weak_sections": [name for name, score in section_scores.items() if score < 60],
            "skill_extraction": extracted,
            "skill_normalization": normalized,
            "ats": {
                "compatibility_score": section_scores["ats_friendliness"],
                "missing_keywords": missing_skills,
                "formatting_issues": [] if section_scores["formatting"] >= 70 else ["Add clear section headings and concise bullet points."],
                "duplicate_content": [],
                "weak_summaries": [] if section_scores["professional_tone"] >= 70 else ["Strengthen the summary with target role and impact."],
                "weak_bullets": [] if section_scores["achievements"] >= 60 else ["Add metrics and outcomes to experience bullets."],
                "unreadable_sections": [],
            },
            "job_match": match_report,
            "ai_summary": ai_result.get("text", ""),
        }
        if comparison_resume:
            old_skills = {str(skill).lower(): str(skill) for skill in (comparison_resume.skills or [])}
            new_skills = {str(skill).lower(): str(skill) for skill in (resume.skills or [])}
            report["comparison"] = {
                "comparison_resume_id": str(comparison_resume.id),
                "added_skills": sorted(new_skills[key] for key in new_skills.keys() - old_skills.keys()),
                "removed_skills": sorted(old_skills[key] for key in old_skills.keys() - new_skills.keys()),
                "ats_improvement": section_scores["ats_friendliness"],
                "score_change": overall_score,
                "improved_wording": len(resume.summary or "") > len(comparison_resume.summary or ""),
            }
        review = ResumeAIReview.objects.create(
            resume=resume,
            user=user,
            review_type=review_type,
            job=job,
            comparison_resume=comparison_resume,
            ai_request=ai_result.get("request"),
            ai_response=ai_result.get("response"),
            prompt_version=ResumeIntelligenceService.PROMPT_VERSION,
            model_name=ResumeIntelligenceService._model_name(ai_result),
            estimated_cost=ResumeIntelligenceService._cost(ai_result),
            overall_score=overall_score,
            ats_score=section_scores["ats_friendliness"],
            match_score=match_score,
            confidence=match_report.get("confidence", 72) if match_report else 72,
            extracted_skills=extracted,
            missing_skills=missing_skills,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            action_items=ResumeIntelligenceService._action_items(suggestions),
            report=report,
            summary=report["summary"],
        )
        AnalyticsService.track(name=f"resume_ai_{review_type}", user=user, target=resume, metadata={"review_id": str(review.id)})
        AuditService.record(actor=user, action=f"resume_ai_{review_type}", target=resume, metadata={"review_id": str(review.id)})
        return review

    @staticmethod
    def analytics(user, resume: CareerResume | None = None) -> dict:
        reviews = ResumeAIReview.objects.filter(user=user)
        if resume:
            reviews = reviews.filter(resume=resume)
        scores = list(reviews.values_list("overall_score", flat=True))
        best = max(scores) if scores else 0
        average = _clamp(sum(scores) / len(scores)) if scores else 0
        weakness_counter = Counter()
        strength_counter = Counter()
        for review in reviews:
            weakness_counter.update(review.weaknesses or [])
            strength_counter.update(review.strengths or [])
        return {
            "average_score": average,
            "best_score": best,
            "review_count": len(scores),
            "top_weaknesses": [{"label": label, "count": count} for label, count in weakness_counter.most_common(8)],
            "top_strengths": [{"label": label, "count": count} for label, count in strength_counter.most_common(8)],
            "score_history": [
                {"score": review.overall_score, "review_type": review.review_type, "created_at": review.created_at}
                for review in reviews.order_by("created_at")[:50]
            ],
            "ats_trend": [
                {"score": review.ats_score, "created_at": review.created_at}
                for review in reviews.exclude(ats_score=0).order_by("created_at")[:50]
            ],
            "job_match_trend": [
                {"score": review.match_score, "created_at": review.created_at}
                for review in reviews.exclude(match_score=0).order_by("created_at")[:50]
            ],
            "skill_growth": [
                {"count": len(review.extracted_skills.get("normalized", [])), "created_at": review.created_at}
                for review in reviews.order_by("created_at")[:50]
            ],
        }


def _portfolio_ai_create_review(*, user, portfolio: Portfolio, review_type: str, project=None, job=None) -> PortfolioAIReview:
    portfolio_text = PortfolioIntelligenceService.portfolio_text(portfolio)
    project_text = PortfolioIntelligenceService.project_text(project) if project else ""
    job_text = ResumeIntelligenceService.job_text(job)
    feature = AIFeature.JOB_MATCHING if review_type == PortfolioAIReviewType.JOB_MATCH else AIFeature.PORTFOLIO_REVIEW
    if review_type == PortfolioAIReviewType.SKILL_EXTRACTION:
        feature = AIFeature.SKILL_GAP_ANALYSIS
    prompt = (
        "Return concise structured portfolio intelligence. Do not expose private reasoning.\n"
        f"Review type: {review_type}\nPortfolio:\n{portfolio_text}\nProject:\n{project_text}\nJob:\n{job_text}"
    )
    ai_result = AIService.generate_text(
        user=user,
        feature=feature,
        input_text=prompt,
        metadata={"portfolio_id": str(portfolio.id), "project_id": str(project.id) if project else "", "job_id": str(job.id) if job else "", "review_type": review_type},
    )
    github_report = PortfolioIntelligenceService._github_report(project, portfolio)
    skills = PortfolioIntelligenceService._extract_skills(portfolio)
    scores = PortfolioIntelligenceService._portfolio_scores(portfolio, github_report)
    if project:
        project_scores = PortfolioIntelligenceService._project_quality(project)
        project_score = _clamp(sum(project_scores.values()) / len(project_scores))
    else:
        project_scores = {}
        project_score = scores["project_quality"]
    job_match = PortfolioIntelligenceService._match_job(portfolio, job)
    overall = scores["overall_portfolio"]
    if review_type == PortfolioAIReviewType.PROJECT_REVIEW:
        overall = project_score
    elif review_type == PortfolioAIReviewType.GITHUB_REVIEW:
        overall = github_report["github_quality_score"]
    elif review_type == PortfolioAIReviewType.JOB_MATCH:
        overall = job_match.get("portfolio_match_score", 0)
    strengths = [label.replace("_", " ").title() for label, score in scores.items() if score >= 75][:8] or ["Portfolio has a usable foundation"]
    weaknesses = [label.replace("_", " ").title() for label, score in scores.items() if score < 60][:8]
    suggestions = [f"Improve {label.replace('_', ' ')} with clearer evidence and stronger project detail." for label, score in scores.items() if score < 65]
    if not github_report["available"]:
        suggestions.append("Add GitHub repository links for stronger technical credibility.")
    if not suggestions:
        suggestions.append("Add quantified business impact to featured projects.")
    report = {
        "summary": f"Portfolio scores {overall}/100 with {len(strengths)} strengths and {len(weaknesses)} improvement areas.",
        "portfolio_scores": scores,
        "project_scores": project_scores,
        "github": github_report,
        "skills": skills,
        "job_match": job_match,
        "project_count": portfolio.projects.count(),
        "technology_diversity": len(set(skills.get("project_technologies", []))),
        "ai_summary": ai_result.get("text", ""),
        "recommended_technologies": sorted(set(job_match.get("missing_skills", []) + github_report.get("missing_repository_standards", [])[:2]))[:8],
        "recommended_next_project": job_match.get("projects_to_build_next", ["Build one polished case study with demo, GitHub, README, tests, and measurable impact."])[0],
    }
    usage = ai_result.get("usage", {})
    review = PortfolioAIReview.objects.create(
        portfolio=portfolio,
        user=user,
        review_type=review_type,
        project=project,
        job=job,
        ai_request=ai_result.get("request"),
        ai_response=ai_result.get("response"),
        prompt_version=PortfolioIntelligenceService.PROMPT_VERSION,
        model_name=PortfolioIntelligenceService._model_name(ai_result),
        estimated_cost=Decimal(str(usage.get("estimated_cost", "0") or "0")),
        overall_score=overall,
        project_score=project_score,
        github_score=github_report["github_quality_score"],
        match_score=job_match.get("portfolio_match_score", 0),
        confidence=job_match.get("confidence", 72) if job_match else 72,
        extracted_skills=skills,
        missing_skills=job_match.get("missing_skills", []),
        technology_stack=skills.get("project_technologies", []),
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=suggestions[:10],
        action_items=[{"priority": "high" if index < 2 else "medium", "action": item} for index, item in enumerate(suggestions[:8])],
        report=report,
        summary=report["summary"],
    )
    AnalyticsService.track(name=f"portfolio_ai_{review_type}", user=user, target=portfolio, metadata={"review_id": str(review.id)})
    AuditService.record(actor=user, action=f"portfolio_ai_{review_type}", target=portfolio, metadata={"review_id": str(review.id)})
    return review


def _portfolio_ai_analytics(user, portfolio: Portfolio | None = None) -> dict:
    reviews = PortfolioAIReview.objects.filter(user=user)
    if portfolio:
        reviews = reviews.filter(portfolio=portfolio)
    scores = list(reviews.values_list("overall_score", flat=True))
    strength_counter = Counter()
    weakness_counter = Counter()
    for review in reviews:
        strength_counter.update(review.strengths or [])
        weakness_counter.update(review.weaknesses or [])
    return {
        "average_score": _clamp(sum(scores) / len(scores)) if scores else 0,
        "best_score": max(scores) if scores else 0,
        "review_count": len(scores),
        "top_strengths": [{"label": label, "count": count} for label, count in strength_counter.most_common(8)],
        "top_weaknesses": [{"label": label, "count": count} for label, count in weakness_counter.most_common(8)],
        "score_history": [{"score": r.overall_score, "review_type": r.review_type, "created_at": r.created_at} for r in reviews.order_by("created_at")[:50]],
        "project_quality_trend": [{"score": r.project_score, "created_at": r.created_at} for r in reviews.exclude(project_score=0).order_by("created_at")[:50]],
        "skill_growth": [{"count": len(r.extracted_skills.get("normalized", [])), "created_at": r.created_at} for r in reviews.order_by("created_at")[:50]],
        "technology_diversity": [{"count": len(r.technology_stack or []), "created_at": r.created_at} for r in reviews.order_by("created_at")[:50]],
        "job_match_trend": [{"score": r.match_score, "created_at": r.created_at} for r in reviews.exclude(match_score=0).order_by("created_at")[:50]],
    }


for _name in [
    "_section_scores",
    "_strengths_and_weaknesses",
    "_suggestions",
    "_action_items",
    "_call_ai",
    "_cost",
    "_model_name",
    "create_review",
    "analytics",
]:
    setattr(ResumeIntelligenceService, _name, staticmethod(getattr(PortfolioIntelligenceService, _name)))

PortfolioIntelligenceService.create_portfolio_review = staticmethod(_portfolio_ai_create_review)
PortfolioIntelligenceService.portfolio_analytics = staticmethod(_portfolio_ai_analytics)
