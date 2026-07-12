import logging

from django.db import transaction
from django.db import models
from django.db.models import Count
from django.utils import timezone

from apps.analytics.services import AnalyticsService
from apps.notifications.models import Notification, NotificationService, NotificationType
from apps.organizations.models import CandidateProfileUnlock, OrganizationRole
from common.audit import AuditService
from common.candidate_visibility import CandidateVisibilityService
from common.entitlements import EntitlementService
from common.exceptions import PermissionError
from common.permission_service import PermissionService

from .models import (
    ApplicationActivity,
    ApplicationStage,
    ApplicationTimeline,
    Interview,
    InterviewParticipant,
    InterviewStatus,
    JobAlert,
    JobApplication,
    JobListing,
    SavedCandidate,
    TalentPool,
)

logger = logging.getLogger("tcareer.jobs")


TERMINAL_APPLICATION_STAGES = {
    ApplicationStage.OFFER_ACCEPTED,
    ApplicationStage.OFFER_DECLINED,
    ApplicationStage.REJECTED,
    ApplicationStage.WITHDRAWN,
}


class RecruitingService:
    @staticmethod
    def ensure_can_recruit(user, organization):
        if not EntitlementService.can_search_candidates(user, organization=organization):
            raise PermissionError("You cannot access recruiting for this organization.")

    @staticmethod
    def ensure_can_manage_application(user, application):
        if not PermissionService.can_manage_application(user, application):
            raise PermissionError("You cannot manage this application.")

    @staticmethod
    def create_timeline(application, actor, event_type, message="", from_stage="", to_stage="", metadata=None):
        return ApplicationTimeline.objects.create(
            application=application,
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            event_type=event_type,
            message=message,
            from_stage=from_stage or "",
            to_stage=to_stage or "",
            metadata=metadata or {},
        )

    @staticmethod
    def create_activity(application, actor, activity_type, metadata=None):
        return ApplicationActivity.objects.create(
            application=application,
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            activity_type=activity_type,
            metadata=metadata or {},
        )

    @staticmethod
    def _notify_stage(application, previous_stage, new_stage):
        candidate = application.candidate
        job = application.job
        if new_stage == ApplicationStage.INTERVIEW_SCHEDULED:
            return
        notification_type = NotificationType.APPLICATION_STAGE_CHANGED
        title = "Application updated"
        body = f"Your application for {job.title} moved to {application.get_stage_display()}."
        if new_stage == ApplicationStage.OFFER_SENT:
            notification_type = NotificationType.OFFER_SENT
            title = "Offer sent"
            body = f"{job.company_name} sent an offer for {job.title}."
        elif new_stage == ApplicationStage.OFFER_ACCEPTED:
            notification_type = NotificationType.OFFER_ACCEPTED
            title = "Offer accepted"
            body = f"Offer accepted for {job.title}."
        elif new_stage == ApplicationStage.OFFER_DECLINED:
            notification_type = NotificationType.OFFER_DECLINED
            title = "Offer declined"
            body = f"Offer declined for {job.title}."
        NotificationService.notify(
            recipient=candidate,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url="/dashboard",
            payload={
                "application_id": str(application.id),
                "job_id": str(job.id),
                "from_stage": previous_stage,
                "to_stage": new_stage,
            },
        )

    @staticmethod
    @transaction.atomic
    def create_application(*, actor, job, candidate, cover_letter="", source="direct"):
        if not getattr(candidate, "is_authenticated", False):
            raise PermissionError("A candidate is required.")
        if actor.id != candidate.id and not PermissionService.can_manage_job(actor, job):
            raise PermissionError("You cannot create this application.")
        if not job.organization_id:
            raise PermissionError("This job is not connected to an organization.")

        application, created = JobApplication.objects.get_or_create(
            job=job,
            candidate=candidate,
            defaults={
                "organization": job.organization,
                "cover_letter": cover_letter,
                "source": source,
                "stage": ApplicationStage.APPLIED,
            },
        )
        if not created:
            return application, False

        JobListing.objects.filter(id=job.id).update(applications_count=models.F("applications_count") + 1)
        RecruitingService.create_timeline(
            application,
            actor,
            "application_created",
            to_stage=ApplicationStage.APPLIED,
            message="Application submitted.",
        )
        RecruitingService.create_activity(application, actor, "application_created")
        AuditService.record(
            actor=actor,
            action="application_created",
            target=application,
            organization=job.organization,
            metadata={"job_id": str(job.id), "candidate_id": str(candidate.id)},
        )
        AnalyticsService.track(
            name="application_created",
            user=actor,
            organization=job.organization,
            target=application,
            metadata={"job_id": str(job.id), "candidate_id": str(candidate.id)},
        )
        for membership in job.organization.memberships.filter(
            role__in=[OrganizationRole.RECRUITER, OrganizationRole.COMPANY_ADMIN],
            status="active",
        ).select_related("user"):
            NotificationService.notify(
                recipient=membership.user,
                notification_type=NotificationType.APPLICATION_RECEIVED,
                title="New application received",
                body=f"{candidate.full_name} applied for {job.title}.",
                action_url=f"/jobs/{job.id}",
                payload={"application_id": str(application.id), "job_id": str(job.id)},
            )
        return application, True

    @staticmethod
    @transaction.atomic
    def transition_application(*, actor, application, stage, message=""):
        if not (stage == ApplicationStage.WITHDRAWN and actor.id == application.candidate_id):
            RecruitingService.ensure_can_manage_application(actor, application)
        if application.stage in TERMINAL_APPLICATION_STAGES and stage != application.stage:
            raise PermissionError("Terminal applications cannot be moved.")
        previous_stage = application.stage
        if previous_stage == stage:
            return application
        application.stage = stage
        update_fields = ["stage", "updated_at"]
        if stage == ApplicationStage.WITHDRAWN:
            application.withdrawn_at = timezone.now()
            update_fields.append("withdrawn_at")
        application.save(update_fields=update_fields)
        RecruitingService.create_timeline(
            application,
            actor,
            "application_stage_changed",
            from_stage=previous_stage,
            to_stage=stage,
            message=message or f"Stage changed from {previous_stage} to {stage}.",
        )
        RecruitingService.create_activity(
            application,
            actor,
            "application_stage_changed",
            {"from_stage": previous_stage, "to_stage": stage},
        )
        AuditService.record(
            actor=actor,
            action="application_stage_changed",
            target=application,
            organization=application.organization,
            metadata={"from_stage": previous_stage, "to_stage": stage},
        )
        AnalyticsService.track(
            name="application_stage_changed",
            user=actor,
            organization=application.organization,
            target=application,
            metadata={"from_stage": previous_stage, "to_stage": stage},
        )
        offer_event_names = {
            ApplicationStage.OFFER_SENT: "offer_sent",
            ApplicationStage.OFFER_ACCEPTED: "offer_accepted",
            ApplicationStage.OFFER_DECLINED: "offer_declined",
        }
        if stage in offer_event_names:
            AnalyticsService.offer_event(
                offer_event_names[stage],
                user=actor,
                organization=application.organization,
                application=application,
                metadata={"from_stage": previous_stage, "to_stage": stage},
            )
        RecruitingService._notify_stage(application, previous_stage, stage)
        return application

    @staticmethod
    @transaction.atomic
    def withdraw_application(*, actor, application):
        if actor.id != application.candidate_id:
            raise PermissionError("Only the candidate can withdraw this application.")
        application = RecruitingService.transition_application(
            actor=actor,
            application=application,
            stage=ApplicationStage.WITHDRAWN,
            message="Candidate withdrew the application.",
        )
        AnalyticsService.track(
            name="application_withdrawn",
            user=actor,
            organization=application.organization,
            target=application,
            metadata={"job_id": str(application.job_id)},
        )
        return application

    @staticmethod
    @transaction.atomic
    def archive_application(*, actor, application):
        RecruitingService.ensure_can_manage_application(actor, application)
        application.is_archived = True
        application.deleted_at = timezone.now()
        application.save(update_fields=["is_archived", "deleted_at", "updated_at"])
        RecruitingService.create_timeline(application, actor, "application_archived", message="Application archived.")
        RecruitingService.create_activity(application, actor, "application_archived")
        AuditService.record(
            actor=actor,
            action="application_archived",
            target=application,
            organization=application.organization,
        )
        return application

    @staticmethod
    def dashboard_summary(actor, organization):
        RecruitingService.ensure_can_recruit(actor, organization)
        jobs = JobListing.objects.filter(organization=organization)
        applications = JobApplication.objects.filter(organization=organization, is_archived=False)
        stage_counts = {
            row["stage"]: row["count"]
            for row in applications.values("stage").annotate(count=Count("id"))
        }
        entitlement = EntitlementService.get_recruiter_entitlement(organization)
        active_seats = EntitlementService.active_recruiter_seats(organization)
        max_seats = EntitlementService.max_recruiter_seats(organization)
        return {
            "total_jobs": jobs.count(),
            "published_jobs": jobs.filter(is_active=True).count(),
            "draft_jobs": jobs.filter(is_active=False).count(),
            "archived_jobs": jobs.filter(is_active=False).count(),
            "applications_received": applications.count(),
            "applications_by_stage": stage_counts,
            "candidate_pipeline": stage_counts,
            "upcoming_interviews": Interview.objects.filter(
                organization=organization,
                status__in=[InterviewStatus.SCHEDULED, InterviewStatus.RESCHEDULED],
                scheduled_start__gte=timezone.now(),
            ).count(),
            "organization_recruiters": organization.memberships.filter(
                role=OrganizationRole.RECRUITER,
                status="active",
            ).count(),
            "remaining_recruiter_seats": max(max_seats - active_seats, 0),
            "seat_usage": {
                "active_recruiter_seats": active_seats,
                "max_recruiter_seats": max_seats,
            },
            "candidate_unlock_usage": {
                "used": CandidateProfileUnlock.objects.filter(organization=organization).count(),
                "limit": None,
            },
            "analytics_summary": {
                "jobs_created": jobs.count(),
                "applications_created": applications.count(),
                "entitled": bool(entitlement),
            },
            "recent_recruiter_activity": list(
                ApplicationActivity.objects.filter(application__organization=organization)
                .select_related("actor", "application")
                .values("id", "activity_type", "created_at", "actor__full_name", "application_id")[:20]
            ),
        }

    @staticmethod
    @transaction.atomic
    def save_candidate(*, actor, organization, candidate, labels=None, private_notes="", talent_pool=None):
        RecruitingService.ensure_can_recruit(actor, organization)
        if not CandidateVisibilityService.can_view_profile(actor, candidate, organization=organization):
            raise PermissionError("You cannot save this candidate.")
        saved, _ = SavedCandidate.objects.update_or_create(
            organization=organization,
            candidate=candidate,
            defaults={
                "saved_by": actor,
                "labels": labels or [],
                "private_notes": private_notes,
                "talent_pool": talent_pool,
            },
        )
        AuditService.record(
            actor=actor,
            action="candidate_saved",
            target=saved,
            organization=organization,
            metadata={"candidate_id": str(candidate.id)},
        )
        AnalyticsService.track(
            name="candidate_saved",
            user=actor,
            organization=organization,
            target=candidate,
            metadata={"saved_candidate_id": str(saved.id)},
        )
        return saved

    @staticmethod
    @transaction.atomic
    def schedule_interview(*, actor, application, interview_data, participant_ids=None):
        RecruitingService.ensure_can_manage_application(actor, application)
        interview = Interview.objects.create(
            application=application,
            organization=application.organization,
            created_by=actor,
            **interview_data,
        )
        participant_ids = set(participant_ids or [])
        participant_ids.add(str(application.candidate_id))
        participant_ids.add(str(actor.id))
        for user_id in participant_ids:
            InterviewParticipant.objects.get_or_create(
                interview=interview,
                user_id=user_id,
                defaults={"role": "candidate" if str(user_id) == str(application.candidate_id) else "interviewer"},
            )
        RecruitingService.transition_application(
            actor=actor,
            application=application,
            stage=ApplicationStage.INTERVIEW_SCHEDULED,
            message="Interview scheduled.",
        )
        RecruitingService.create_timeline(
            application,
            actor,
            "interview_scheduled",
            message="Interview scheduled.",
            metadata={"interview_id": str(interview.id)},
        )
        AuditService.record(
            actor=actor,
            action="interview_scheduled",
            target=interview,
            organization=application.organization,
            metadata={"application_id": str(application.id)},
        )
        AnalyticsService.track(
            name="interview_scheduled",
            user=actor,
            organization=application.organization,
            target=interview,
            metadata={"application_id": str(application.id)},
        )
        logger.info(
            "interview_scheduled",
            extra={
                "interview_id": str(interview.id),
                "application_id": str(application.id),
                "organization_id": str(application.organization_id),
                "actor_id": str(actor.id),
            },
        )
        NotificationService.notify(
            recipient=application.candidate,
            notification_type=NotificationType.INTERVIEW_SCHEDULED,
            title="Interview scheduled",
            body=f"Your interview for {application.job.title} has been scheduled.",
            action_url="/dashboard",
            payload={"application_id": str(application.id), "interview_id": str(interview.id)},
        )
        if application.assigned_recruiter_id and application.assigned_recruiter_id != actor.id:
            NotificationService.notify(
                recipient=application.assigned_recruiter,
                notification_type=NotificationType.INTERVIEW_SCHEDULED,
                title="Interview scheduled",
                body=f"Interview scheduled for {application.candidate.full_name} on {application.job.title}.",
                action_url=f"/recruiter/applications/{application.id}",
                payload={"application_id": str(application.id), "interview_id": str(interview.id)},
            )
        return interview


class JobAlertService:
    @staticmethod
    def _normalise_list(value):
        if not value:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _matches(job, filters):
        search = (filters.get("search") or filters.get("q") or "").strip().lower()
        if search:
            haystack = " ".join([job.title, job.company_name, job.description, job.city, job.location]).lower()
            if search not in haystack:
                return False

        skills = JobAlertService._normalise_list(filters.get("skills"))
        if skills:
            job_skills = {skill.lower() for skill in [*job.required_skills, *job.preferred_skills]}
            if not any(skill.lower() in job_skills for skill in skills):
                return False

        country = (filters.get("country") or filters.get("country_code") or "").strip().upper()
        if country and job.country_code.upper() != country:
            return False

        city = (filters.get("city") or "").strip().lower()
        if city and city not in job.city.lower() and city not in job.location.lower():
            return False

        job_type = (filters.get("job_type") or "").strip()
        if job_type and job.job_type != job_type:
            return False

        experience = (filters.get("experience") or filters.get("experience_level") or "").strip()
        if experience and job.experience_level != experience:
            return False

        remote = filters.get("remote")
        if remote is None:
            remote = filters.get("is_remote")
        if remote is True or str(remote).lower() in {"true", "1", "yes", "remote"}:
            if not job.is_remote:
                return False

        return True

    @staticmethod
    def _already_notified(alert, job):
        notifications = Notification.objects.filter(
            recipient=alert.user,
            notification_type=NotificationType.NEW_JOB_MATCH,
        ).only("payload")
        return any(
            item.payload.get("source") == "job_alert"
            and item.payload.get("alert_id") == str(alert.id)
            and item.payload.get("job_id") == str(job.id)
            for item in notifications
        )

    @staticmethod
    def matching_jobs(alert, limit=10):
        jobs = JobListing.objects.filter(is_active=True).select_related("organization").order_by("-created_at")[:200]
        matches = [job for job in jobs if JobAlertService._matches(job, alert.filters or {})]
        return matches[:limit]

    @staticmethod
    def run_alert(alert, limit=10, dry_run=False):
        created = []
        if not alert.is_active:
            return created
        for job in JobAlertService.matching_jobs(alert, limit=limit):
            if JobAlertService._already_notified(alert, job):
                continue
            if dry_run:
                created.append(job)
                continue
            NotificationService.notify(
                recipient=alert.user,
                notification_type=NotificationType.NEW_JOB_MATCH,
                title="New job match",
                body=f"{job.title} at {job.company_name} matches your alert: {alert.name}.",
                action_url=f"/jobs/{job.id}",
                payload={
                    "source": "job_alert",
                    "alert_id": str(alert.id),
                    "job_id": str(job.id),
                    "email_ready": True,
                    "email_subject": f"New T-Career job match: {job.title}",
                },
            )
            AnalyticsService.track(
                name="job_alert_matched",
                user=alert.user,
                organization=job.organization,
                target=job,
                metadata={"alert_id": str(alert.id), "job_id": str(job.id)},
            )
            created.append(job)
        if dry_run:
            return created
        alert.last_run_at = timezone.now()
        alert.last_matched_count = len(created)
        alert.total_matched_count = models.F("total_matched_count") + len(created)
        alert.save(update_fields=["last_run_at", "last_matched_count", "total_matched_count", "updated_at"])
        alert.refresh_from_db(fields=["total_matched_count"])
        logger.info(
            "job_alert_processed",
            extra={"alert_id": str(alert.id), "user_id": str(alert.user_id), "matches_created": len(created), "dry_run": dry_run},
        )
        return created

    @staticmethod
    def run_active_alerts(limit_per_alert=10, dry_run=False, limit=None):
        summary = {"alerts_checked": 0, "matches_created": 0, "email_payloads_created": 0}
        alerts = JobAlert.objects.filter(is_active=True).select_related("user")
        for alert in alerts:
            if limit is not None and summary["matches_created"] >= limit:
                break
            summary["alerts_checked"] += 1
            remaining = limit - summary["matches_created"] if limit is not None else limit_per_alert
            created = JobAlertService.run_alert(
                alert,
                limit=min(limit_per_alert, remaining),
                dry_run=dry_run,
            )
            summary["matches_created"] += len(created)
            if not dry_run:
                summary["email_payloads_created"] += len(created)
        summary["dry_run"] = dry_run
        return summary
