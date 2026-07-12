import hashlib
import os
from datetime import timedelta

from django.conf import settings
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from apps.analytics.models import AnalyticsEvent
from apps.audit.models import AuditLog
from apps.careers.models import (
    ExperienceLevel as PortfolioExperienceLevel,
    Portfolio,
    PortfolioProject,
    PortfolioSkill,
    RemotePreference,
    Resume,
    SkillSource,
    VisibilityChoice,
)
from apps.jobs.models import (
    ApplicationActivity,
    ApplicationAttachment,
    ApplicationNote,
    ApplicationStage,
    ApplicationTimeline,
    ExperienceLevel,
    Interview,
    InterviewFeedback,
    InterviewParticipant,
    InterviewScorecard,
    InterviewStatus,
    InterviewType,
    JobApplication,
    JobListing,
    JobType,
    SavedCandidate,
    SalaryCurrency,
    TalentPool,
)
from apps.notifications.models import Notification, NotificationType
from apps.organizations.models import (
    CandidateProfileUnlock,
    MembershipStatus,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationStatus,
    OrganizationType,
)
from apps.users.models import User, UserRole


SOURCE = "recruiter_demo_seed"
DEMO_DOMAIN = "tcareer.demo"
DEFAULT_DEBUG_PASSWORD = "DemoPass123!"
COMPANY_SLUG = "technova-africa-demo"
UNIVERSITY_SLUG = "conakry-digital-university-demo"

DEMO_ACCOUNTS = {
    "company_admin": {
        "email": "company.admin@tcareer.demo",
        "full_name": "Amara Diallo",
        "role": UserRole.COMPANY_ADMIN,
        "username": "demo-company-admin",
        "headline": "Head of People at TechNova Africa",
    },
    "recruiter": {
        "email": "recruiter@tcareer.demo",
        "full_name": "Moussa Camara",
        "role": UserRole.RECRUITER,
        "username": "demo-recruiter",
        "headline": "Technical Recruiter for early career tech roles",
    },
    "recruiter2": {
        "email": "recruiter2@tcareer.demo",
        "full_name": "Fatou Bah",
        "role": UserRole.RECRUITER,
        "username": "demo-recruiter-2",
        "headline": "Recruiter focused on internships and support roles",
    },
    "student": {
        "email": "student@tcareer.demo",
        "full_name": "Aissatou Barry",
        "role": UserRole.STUDENT,
        "username": "demo-data-analyst-learner",
        "headline": "Data analyst learner with SQL and dashboard projects",
    },
    "student2": {
        "email": "student2@tcareer.demo",
        "full_name": "Ibrahim Sow",
        "role": UserRole.STUDENT,
        "username": "demo-python-backend-learner",
        "headline": "Python backend learner building Django APIs",
    },
    "student3": {
        "email": "student3@tcareer.demo",
        "full_name": "Mariama Keita",
        "role": UserRole.STUDENT,
        "username": "demo-ai-project-learner",
        "headline": "AI product learner with prompt and analytics projects",
    },
    "student4": {
        "email": "student4@tcareer.demo",
        "full_name": "Samuel Mensah",
        "role": UserRole.STUDENT,
        "username": "demo-teacher-to-tech",
        "headline": "English teacher transitioning into customer success in tech",
    },
    "student5": {
        "email": "student5@tcareer.demo",
        "full_name": "Grace Nwosu",
        "role": UserRole.STUDENT,
        "username": "demo-recent-grad-portfolio",
        "headline": "Recent graduate with portfolio projects and internship readiness",
    },
    "university_admin": {
        "email": "university.admin@tcareer.demo",
        "full_name": "Dr. Kadiatou Conte",
        "role": UserRole.UNIVERSITY_ADMIN,
        "username": "demo-university-admin",
        "headline": "University employability lead",
    },
}

JOBS = [
    {
        "key": "data_analyst",
        "title": "Junior Data Analyst",
        "job_type": JobType.FULL_TIME,
        "experience_level": ExperienceLevel.ENTRY,
        "is_active": True,
        "city": "Conakry",
        "location": "Conakry, Guinea",
        "salary_min": 9000,
        "salary_max": 14000,
        "required_skills": ["SQL", "Python", "Excel", "Dashboards"],
        "preferred_skills": ["Pandas", "Power BI"],
        "description": "Join TechNova Africa's data team to clean datasets, write SQL, and build weekly hiring and operations dashboards.",
    },
    {
        "key": "django_backend",
        "title": "Backend Django Developer",
        "job_type": JobType.FULL_TIME,
        "experience_level": ExperienceLevel.ENTRY,
        "is_active": True,
        "city": "Remote",
        "location": "Remote - West Africa",
        "salary_min": 18000,
        "salary_max": 26000,
        "required_skills": ["Python", "Django", "REST APIs", "PostgreSQL"],
        "preferred_skills": ["Docker", "Celery"],
        "description": "Build secure Django REST APIs for learning, hiring, and marketplace workflows.",
    },
    {
        "key": "ai_product_intern",
        "title": "AI Product Intern",
        "job_type": JobType.INTERNSHIP,
        "experience_level": ExperienceLevel.STUDENT,
        "is_active": True,
        "city": "Conakry",
        "location": "Hybrid - Conakry",
        "salary_min": 2500,
        "salary_max": 4500,
        "required_skills": ["AI Tools", "Research", "Product Thinking", "Analytics"],
        "preferred_skills": ["Prompt Engineering", "Figma"],
        "description": "Support discovery, prototype AI career tools, and measure learner outcomes.",
    },
    {
        "key": "career_success",
        "title": "Career Success Associate",
        "job_type": JobType.PART_TIME,
        "experience_level": ExperienceLevel.ENTRY,
        "is_active": False,
        "city": "Remote",
        "location": "Remote",
        "salary_min": 7000,
        "salary_max": 10000,
        "required_skills": ["Communication", "Coaching", "English", "CRM"],
        "preferred_skills": ["Teaching", "Community"],
        "description": "Coach learners, review portfolios, and coordinate interview preparation.",
    },
]

CANDIDATE_PROFILES = {
    "student": {
        "desired_role": "Junior Data Analyst",
        "experience_level": PortfolioExperienceLevel.ENTRY,
        "remote_preference": RemotePreference.HYBRID,
        "skills": ["SQL", "Python", "Pandas", "Excel", "Power BI"],
        "projects": ["Market Basket Dashboard", "Learner Progress SQL Analysis"],
    },
    "student2": {
        "desired_role": "Backend Django Developer",
        "experience_level": PortfolioExperienceLevel.ENTRY,
        "remote_preference": RemotePreference.REMOTE,
        "skills": ["Python", "Django", "DRF", "PostgreSQL", "Docker"],
        "projects": ["Job Board API", "Course Progress Service"],
    },
    "student3": {
        "desired_role": "AI Product Intern",
        "experience_level": PortfolioExperienceLevel.STUDENT,
        "remote_preference": RemotePreference.FLEXIBLE,
        "skills": ["AI Tools", "Prompt Engineering", "Analytics", "Figma"],
        "projects": ["AI Tutor Prompt Tests", "Career Matching Prototype"],
    },
    "student4": {
        "desired_role": "Career Success Associate",
        "experience_level": PortfolioExperienceLevel.ENTRY,
        "remote_preference": RemotePreference.REMOTE,
        "skills": ["English", "Teaching", "Communication", "Learner Coaching"],
        "projects": ["Tech English Lesson Plan", "Portfolio Review Checklist"],
    },
    "student5": {
        "desired_role": "Junior Data Analyst",
        "experience_level": PortfolioExperienceLevel.STUDENT,
        "remote_preference": RemotePreference.FLEXIBLE,
        "skills": ["SQL", "Python", "Presentation", "Research"],
        "projects": ["Graduate Skills Survey", "Public Portfolio Case Study"],
    },
}

APPLICATION_PLAN = [
    ("student", "data_analyst", ApplicationStage.APPLIED),
    ("student2", "django_backend", ApplicationStage.UNDER_REVIEW),
    ("student3", "ai_product_intern", ApplicationStage.SHORTLISTED),
    ("student4", "career_success", ApplicationStage.ASSESSMENT),
    ("student5", "data_analyst", ApplicationStage.INTERVIEW_SCHEDULED),
    ("student", "django_backend", ApplicationStage.INTERVIEW_COMPLETED),
    ("student2", "data_analyst", ApplicationStage.OFFER_SENT),
    ("student3", "django_backend", ApplicationStage.REJECTED),
]


def demo_password():
    password = os.environ.get("TCAREER_DEMO_PASSWORD")
    if password:
        return password
    if settings.DEBUG:
        return DEFAULT_DEBUG_PASSWORD
    raise CommandError("Set TCAREER_DEMO_PASSWORD before creating demo users outside DEBUG.")


def ensure_demo_commands_allowed():
    if settings.DEBUG:
        return
    if os.environ.get("ALLOW_RECRUITER_DEMO_COMMANDS") == "True":
        return
    raise CommandError("Recruiter demo commands are blocked outside DEBUG unless ALLOW_RECRUITER_DEMO_COMMANDS=True.")


def source_metadata(**extra):
    return {"source": SOURCE, **extra}


def raw_delete_audit_demo_records():
    qs = AuditLog.objects.filter(metadata__source=SOURCE)
    return qs._raw_delete(qs.db)


def reset_recruiter_demo_data():
    demo_emails = [account["email"] for account in DEMO_ACCOUNTS.values()]
    demo_orgs = Organization.objects.filter(slug__in=[COMPANY_SLUG, UNIVERSITY_SLUG])
    demo_org_ids = list(demo_orgs.values_list("id", flat=True))
    demo_users = User.objects.filter(email__in=demo_emails)
    demo_user_ids = list(demo_users.values_list("id", flat=True))

    raw_delete_audit_demo_records()
    AnalyticsEvent.objects.filter(metadata__source=SOURCE).delete()
    Notification.objects.filter(payload__source=SOURCE).delete()

    ApplicationAttachment.objects.filter(application__organization_id__in=demo_org_ids).delete()
    InterviewScorecard.objects.filter(interview__organization_id__in=demo_org_ids).delete()
    InterviewFeedback.objects.filter(interview__organization_id__in=demo_org_ids).delete()
    InterviewParticipant.objects.filter(interview__organization_id__in=demo_org_ids).delete()
    Interview.objects.filter(organization_id__in=demo_org_ids).delete()
    ApplicationNote.objects.filter(application__organization_id__in=demo_org_ids).delete()
    ApplicationActivity.objects.filter(application__organization_id__in=demo_org_ids).delete()
    ApplicationTimeline.objects.filter(application__organization_id__in=demo_org_ids).delete()
    JobApplication.objects.filter(organization_id__in=demo_org_ids).delete()
    SavedCandidate.objects.filter(organization_id__in=demo_org_ids).delete()
    TalentPool.objects.filter(organization_id__in=demo_org_ids).delete()
    CandidateProfileUnlock.objects.filter(organization_id__in=demo_org_ids).delete()
    OrganizationRecruiterEntitlement.objects.filter(organization_id__in=demo_org_ids).delete()
    OrganizationInvitation.objects.filter(organization_id__in=demo_org_ids).delete()
    OrganizationMembership.objects.filter(organization_id__in=demo_org_ids).delete()
    JobListing.objects.filter(organization_id__in=demo_org_ids).delete()
    demo_orgs.delete()

    Resume.objects.filter(user_id__in=demo_user_ids).delete()
    PortfolioProject.objects.filter(portfolio__user_id__in=demo_user_ids).delete()
    PortfolioSkill.objects.filter(portfolio__user_id__in=demo_user_ids).delete()
    Portfolio.objects.filter(user_id__in=demo_user_ids).delete()
    demo_users.delete()


class RecruiterDemoSeeder:
    def __init__(self, stdout=None):
        self.stdout = stdout
        self.password = demo_password()
        self.users = {}
        self.jobs = {}

    @transaction.atomic
    def seed(self):
        ensure_demo_commands_allowed()
        self._create_users()
        company, university = self._create_organizations()
        self._create_memberships(company, university)
        self._create_entitlement(company)
        self._create_invitation(company)
        self._create_candidate_assets()
        self._create_jobs(company)
        self._create_applications(company)
        self._create_saved_candidates(company)
        self._create_notifications(company)
        self._create_org_events(company, university)
        return {
            "users": len(self.users),
            "organizations": 2,
            "jobs": len(self.jobs),
            "applications": JobApplication.objects.filter(organization=company).count(),
        }

    def _create_users(self):
        for key, data in DEMO_ACCOUNTS.items():
            user, _ = User.objects.update_or_create(
                email=data["email"],
                defaults={
                    "full_name": data["full_name"],
                    "role": data["role"],
                    "username": data["username"],
                    "profile_headline": data["headline"],
                    "profile_location": "Conakry, Guinea",
                    "current_country": "GN",
                    "nationality": "GN",
                    "preferred_language": "en",
                    "locale": "en-GN",
                    "timezone": "Africa/Conakry",
                    "is_active": True,
                    "is_verified": True,
                    "is_email_verified": True,
                    "is_public_profile": data["role"] == UserRole.STUDENT,
                },
            )
            user.set_password(self.password)
            user.save(update_fields=["password", "updated_at"])
            self.users[key] = user

    def _create_organizations(self):
        company, _ = Organization.objects.update_or_create(
            slug=COMPANY_SLUG,
            defaults={
                "name": "TechNova Africa",
                "organization_type": OrganizationType.COMPANY,
                "status": OrganizationStatus.ACTIVE,
                "website_url": "https://technova.example.com",
                "country_code": "GN",
                "created_by": self.users["company_admin"],
                "verified_by": self.users["company_admin"],
                "verified_at": timezone.now(),
            },
        )
        university, _ = Organization.objects.update_or_create(
            slug=UNIVERSITY_SLUG,
            defaults={
                "name": "Conakry Digital University",
                "organization_type": OrganizationType.UNIVERSITY,
                "status": OrganizationStatus.ACTIVE,
                "website_url": "https://university.example.com",
                "country_code": "GN",
                "created_by": self.users["university_admin"],
                "verified_by": self.users["university_admin"],
                "verified_at": timezone.now(),
            },
        )
        return company, university

    def _create_memberships(self, company, university):
        memberships = [
            (company, "company_admin", OrganizationRole.COMPANY_ADMIN),
            (company, "recruiter", OrganizationRole.RECRUITER),
            (company, "recruiter2", OrganizationRole.RECRUITER),
            (university, "university_admin", OrganizationRole.UNIVERSITY_ADMIN),
            (university, "student", OrganizationRole.STUDENT),
            (university, "student2", OrganizationRole.STUDENT),
            (university, "student3", OrganizationRole.STUDENT),
            (university, "student4", OrganizationRole.STUDENT),
            (university, "student5", OrganizationRole.STUDENT),
        ]
        for organization, user_key, role in memberships:
            OrganizationMembership.objects.update_or_create(
                organization=organization,
                user=self.users[user_key],
                role=role,
                defaults={"status": MembershipStatus.ACTIVE, "invited_by": self.users.get("company_admin")},
            )

    def _create_entitlement(self, company):
        OrganizationRecruiterEntitlement.objects.update_or_create(
            organization=company,
            defaults={
                "max_recruiter_seats": 4,
                "can_post_jobs": True,
                "can_search_candidates": True,
                "can_view_candidate_profiles": True,
                "starts_at": timezone.now() - timedelta(days=30),
                "ends_at": timezone.now() + timedelta(days=60),
                "updated_by": self.users["company_admin"],
            },
        )

    def _create_invitation(self, company):
        token_hash = hashlib.sha256(f"{SOURCE}:pending-recruiter".encode("utf-8")).hexdigest()
        OrganizationInvitation.objects.update_or_create(
            token_hash=token_hash,
            defaults={
                "organization": company,
                "email": "pending.recruiter@tcareer.demo",
                "role": OrganizationRole.RECRUITER,
                "invited_by": self.users["company_admin"],
                "expires_at": timezone.now() + timedelta(days=7),
                "accepted_by": None,
                "accepted_at": None,
                "revoked_at": None,
            },
        )

    def _create_candidate_assets(self):
        for key, profile_data in CANDIDATE_PROFILES.items():
            user = self.users[key]
            portfolio, _ = Portfolio.objects.update_or_create(
                user=user,
                defaults={
                    "headline": user.profile_headline,
                    "bio": f"{user.full_name} is part of the recruiter demo scenario and has a public profile ready for candidate discovery.",
                    "location": "Conakry, Guinea",
                    "desired_role": profile_data["desired_role"],
                    "experience_level": profile_data["experience_level"],
                    "visibility": VisibilityChoice.PUBLIC,
                    "preferred_work_country": "GN",
                    "relocation_willingness": "regional",
                    "remote_preference": profile_data["remote_preference"],
                    "linkedin_url": "https://linkedin.example.com/demo",
                    "github_url": "https://github.example.com/demo",
                    "website_url": f"https://portfolio.example.com/{user.username}",
                },
            )
            for position, skill in enumerate(profile_data["skills"], start=1):
                PortfolioSkill.objects.update_or_create(
                    portfolio=portfolio,
                    name=skill,
                    defaults={"category": "Demo Skill", "source": SkillSource.MANUAL, "position": position},
                )
            for position, title in enumerate(profile_data["projects"], start=1):
                PortfolioProject.objects.update_or_create(
                    portfolio=portfolio,
                    title=title,
                    defaults={
                        "description": f"Demo project showing {profile_data['desired_role'].lower()} readiness.",
                        "tech_stack": profile_data["skills"][:4],
                        "project_url": f"https://projects.example.com/{user.username}/{position}",
                        "github_url": "https://github.example.com/demo/project",
                        "thumbnail_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71",
                        "is_featured": position == 1,
                        "position": position,
                    },
                )
            Resume.objects.update_or_create(
                user=user,
                defaults={
                    "title": f"{user.full_name} - {profile_data['desired_role']} Resume",
                    "summary": user.profile_headline,
                    "target_role": profile_data["desired_role"],
                    "education": [{"school": "T-Career Academy", "program": "Career Track", "year": "2026"}],
                    "experience": [{"company": "Demo Project Lab", "role": profile_data["desired_role"], "duration": "6 months"}],
                    "pdf_url": f"https://files.example.com/demo/resumes/{user.username}.pdf",
                    "last_generated_at": timezone.now(),
                },
            )

    def _create_jobs(self, company):
        for index, data in enumerate(JOBS, start=1):
            job, _ = JobListing.objects.update_or_create(
                organization=company,
                title=data["title"],
                defaults={
                    "company_name": company.name,
                    "description": data["description"],
                    "requirements": data["required_skills"],
                    "job_type": data["job_type"],
                    "experience_level": data["experience_level"],
                    "location": data["location"],
                    "country_code": "GN",
                    "city": data["city"],
                    "is_remote": "Remote" in data["location"],
                    "remote_regions": ["West Africa", "Remote"] if "Remote" in data["location"] else ["Guinea"],
                    "salary_min": data["salary_min"],
                    "salary_max": data["salary_max"],
                    "salary_currency": SalaryCurrency.USD,
                    "salary_visible": True,
                    "apply_url": "",
                    "required_skills": data["required_skills"],
                    "preferred_skills": data["preferred_skills"],
                    "languages_required": ["en", "fr"],
                    "is_active": data["is_active"],
                    "views_count": 80 - (index * 9),
                    "posted_by": self.users["company_admin"] if index % 2 else self.users["recruiter"],
                },
            )
            self.jobs[data["key"]] = job
            self._upsert_audit("job_created", job, company, self.users["company_admin"])
            if job.is_active:
                self._upsert_audit("job_published", job, company, self.users["company_admin"])
                self._upsert_analytics("job_published", self.users["company_admin"], company, job)

    def _create_applications(self, company):
        now = timezone.now()
        for index, (candidate_key, job_key, stage) in enumerate(APPLICATION_PLAN, start=1):
            candidate = self.users[candidate_key]
            job = self.jobs[job_key]
            application, _ = JobApplication.objects.update_or_create(
                job=job,
                candidate=candidate,
                defaults={
                    "organization": company,
                    "stage": stage,
                    "cover_letter": f"I am excited to apply for {job.title} through the T-Career demo marketplace.",
                    "source": SOURCE,
                    "assigned_recruiter": self.users["recruiter"] if index % 2 else self.users["recruiter2"],
                    "hiring_manager": self.users["company_admin"],
                    "is_archived": False,
                },
            )
            created_at = now - timedelta(days=10 - index)
            JobApplication.objects.filter(id=application.id).update(created_at=created_at, updated_at=created_at)
            self._application_history(application, stage, index)
            self._upsert_analytics("application_created", candidate, company, application, occurred_at=created_at)
            self._upsert_audit("application_created", application, company, candidate)
            if stage in {ApplicationStage.INTERVIEW_SCHEDULED, ApplicationStage.INTERVIEW_COMPLETED, ApplicationStage.OFFER_SENT}:
                self._create_interview(application, index)
            if stage == ApplicationStage.OFFER_SENT:
                self._upsert_analytics("offer_sent", self.users["recruiter"], company, application)

    def _application_history(self, application, stage, index):
        stage_sequence = [ApplicationStage.APPLIED]
        if stage != ApplicationStage.APPLIED:
            stage_sequence.append(ApplicationStage.UNDER_REVIEW)
        if stage in {
            ApplicationStage.SHORTLISTED,
            ApplicationStage.ASSESSMENT,
            ApplicationStage.INTERVIEW_SCHEDULED,
            ApplicationStage.INTERVIEW_COMPLETED,
            ApplicationStage.OFFER_SENT,
            ApplicationStage.REJECTED,
        }:
            stage_sequence.append(ApplicationStage.SHORTLISTED)
        if stage in {ApplicationStage.ASSESSMENT, ApplicationStage.INTERVIEW_SCHEDULED, ApplicationStage.INTERVIEW_COMPLETED, ApplicationStage.OFFER_SENT}:
            stage_sequence.append(ApplicationStage.ASSESSMENT)
        if stage in {ApplicationStage.INTERVIEW_SCHEDULED, ApplicationStage.INTERVIEW_COMPLETED, ApplicationStage.OFFER_SENT}:
            stage_sequence.append(ApplicationStage.INTERVIEW_SCHEDULED)
        if stage in {ApplicationStage.INTERVIEW_COMPLETED, ApplicationStage.OFFER_SENT}:
            stage_sequence.append(ApplicationStage.INTERVIEW_COMPLETED)
        if stage in {ApplicationStage.OFFER_SENT, ApplicationStage.REJECTED} and stage not in stage_sequence:
            stage_sequence.append(stage)

        previous = ""
        for position, current in enumerate(stage_sequence, start=1):
            ApplicationTimeline.objects.update_or_create(
                application=application,
                event_type=f"demo_stage_{position}",
                defaults={
                    "actor": self.users["recruiter"],
                    "from_stage": previous,
                    "to_stage": current,
                    "message": f"Demo application moved to {current.replace('_', ' ')}.",
                    "metadata": source_metadata(stage=current),
                },
            )
            previous = current
        ApplicationActivity.objects.update_or_create(
            application=application,
            activity_type="application_stage_changed",
            defaults={
                "actor": self.users["recruiter"],
                "metadata": source_metadata(stage=stage, demo_index=index),
            },
        )
        ApplicationNote.objects.update_or_create(
            application=application,
            author=self.users["recruiter"],
            defaults={
                "body": f"Demo note: {application.candidate.full_name} is a strong fit for {application.job.title}.",
                "is_internal": True,
            },
        )
        ApplicationAttachment.objects.update_or_create(
            application=application,
            file_name=f"{application.candidate.username}-resume.pdf",
            defaults={
                "uploaded_by": application.candidate,
                "file_url": f"https://files.example.com/demo/applications/{application.id}.pdf",
                "content_type": "application/pdf",
                "is_private": False,
            },
        )

    def _create_interview(self, application, index):
        scheduled_start = timezone.now() + timedelta(days=index)
        if application.stage in {ApplicationStage.INTERVIEW_COMPLETED, ApplicationStage.OFFER_SENT}:
            scheduled_start = timezone.now() - timedelta(days=index)
        interview, _ = Interview.objects.update_or_create(
            application=application,
            defaults={
                "organization": application.organization,
                "interview_type": InterviewType.ONLINE,
                "status": InterviewStatus.COMPLETED if application.stage in {ApplicationStage.INTERVIEW_COMPLETED, ApplicationStage.OFFER_SENT} else InterviewStatus.SCHEDULED,
                "scheduled_start": scheduled_start,
                "scheduled_end": scheduled_start + timedelta(minutes=45),
                "timezone": "Africa/Conakry",
                "meeting_link": "https://meet.example.com/tcareer-demo",
                "created_by": self.users["recruiter"],
            },
        )
        for participant, role in [(application.candidate, "candidate"), (self.users["recruiter"], "interviewer")]:
            InterviewParticipant.objects.update_or_create(interview=interview, user=participant, defaults={"role": role})
        if interview.status == InterviewStatus.COMPLETED:
            InterviewFeedback.objects.update_or_create(
                interview=interview,
                author=self.users["recruiter"],
                defaults={"rating": 4, "recommendation": "advance", "feedback": "Clear communication and strong practical examples."},
            )
            InterviewScorecard.objects.update_or_create(
                interview=interview,
                author=self.users["recruiter"],
                defaults={"criteria": {"technical": 4, "communication": 5, "learning_agility": 4}, "total_score": 13, "recommendation": "advance"},
            )
            self._upsert_analytics("interview_completed", self.users["recruiter"], application.organization, interview)
        self._upsert_analytics("interview_scheduled", self.users["recruiter"], application.organization, interview)
        self._upsert_audit("interview_scheduled", interview, application.organization, self.users["recruiter"])

    def _create_saved_candidates(self, company):
        pool, _ = TalentPool.objects.update_or_create(
            organization=company,
            name="Demo shortlist",
            defaults={"description": "Candidates prepared for the live recruiter demo.", "created_by": self.users["recruiter"]},
        )
        for key in ["student", "student2", "student3"]:
            saved, _ = SavedCandidate.objects.update_or_create(
                organization=company,
                candidate=self.users[key],
                defaults={
                    "saved_by": self.users["recruiter"],
                    "talent_pool": pool,
                    "labels": ["demo", CANDIDATE_PROFILES[key]["desired_role"]],
                    "private_notes": "Demo saved candidate with recruiter notes.",
                },
            )
            self._upsert_analytics("candidate_saved", self.users["recruiter"], company, self.users[key], {"saved_candidate_id": str(saved.id)})
            CandidateProfileUnlock.objects.update_or_create(
                organization=company,
                candidate=self.users[key],
                defaults={"unlocked_by": self.users["recruiter"]},
            )
            self._upsert_analytics("candidate_unlocked", self.users["recruiter"], company, self.users[key])

    def _create_notifications(self, company):
        for application in JobApplication.objects.filter(organization=company).select_related("candidate", "job"):
            Notification.objects.update_or_create(
                recipient=application.candidate,
                notification_type=NotificationType.APPLICATION_STAGE_CHANGED,
                title=f"Demo update: {application.job.title}",
                defaults={
                    "body": f"Your demo application is currently in {application.get_stage_display()}.",
                    "action_url": "/dashboard",
                    "payload": source_metadata(application_id=str(application.id), job_id=str(application.job_id)),
                },
            )
        Notification.objects.update_or_create(
            recipient=self.users["recruiter"],
            notification_type=NotificationType.RECRUITER_INVITED,
            title="Demo recruiter workspace ready",
            defaults={
                "body": f"{company.name} is ready for the recruiter demo.",
                "action_url": "/recruiter/dashboard",
                "payload": source_metadata(organization_id=str(company.id)),
            },
        )

    def _create_org_events(self, company, university):
        self._upsert_audit("organization_created", company, company, self.users["company_admin"])
        self._upsert_audit("entitlement_changed", company.recruiter_entitlement, company, self.users["company_admin"])
        self._upsert_audit("organization_created", university, university, self.users["university_admin"])
        self._upsert_analytics("organization_member_added", self.users["recruiter"], company, company)
        self._upsert_analytics("recruiter_viewed_candidate", self.users["recruiter"], company, self.users["student"])

    def _upsert_analytics(self, name, user, organization, target, metadata=None, occurred_at=None):
        event, _ = AnalyticsEvent.objects.update_or_create(
            name=name,
            organization_id=organization.id,
            target_type=target.__class__.__name__,
            target_id=str(target.id),
            defaults={"user": user, "metadata": source_metadata(**(metadata or {}))},
        )
        if occurred_at:
            AnalyticsEvent.objects.filter(id=event.id).update(occurred_at=occurred_at)
        return event

    def _upsert_audit(self, action, target, organization, actor):
        return AuditLog.objects.get_or_create(
            action=action,
            target_type=target.__class__.__name__,
            target_id=str(target.id),
            organization_id=organization.id,
            defaults={"actor": actor, "metadata": source_metadata()},
        )[0]
