from django.utils import timezone
from .models import TrustScoreLog, TrustChangeReason, TrustSubjectType


SCORE_RULES = {
    TrustChangeReason.EMAIL_VERIFIED: 10,
    TrustChangeReason.PROFILE_COMPLETE: 10,
    TrustChangeReason.IDENTITY_SUBMITTED: 10,
    TrustChangeReason.IDENTITY_VERIFIED: 30,
    TrustChangeReason.TEACHING_DEMO_SUBMITTED: 10,
    TrustChangeReason.TEACHING_DEMO_APPROVED: 20,
    TrustChangeReason.FIRST_COURSE_PUBLISHED: 10,
    TrustChangeReason.RATING_ABOVE_4: 10,
    TrustChangeReason.COMPANY_VERIFIED: 30,
    TrustChangeReason.COMPANY_EMAIL_VERIFIED: 10,
    TrustChangeReason.REGISTRATION_SUBMITTED: 10,
    TrustChangeReason.WEBSITE_VERIFIED: 10,
    TrustChangeReason.ENTERPRISE_LEVEL: 20,
    TrustChangeReason.FIRST_JOB_POSTED: 5,
    TrustChangeReason.FIRST_CERTIFICATE: 10,
    TrustChangeReason.PORTFOLIO_COMPLETE: 10,
    TrustChangeReason.RESUME_CREATED: 5,
    TrustChangeReason.COMPLAINT_RECEIVED: -20,
    TrustChangeReason.SUSPICIOUS_ACTIVITY: -30,
}

SCORE_MAX = 100
SCORE_MIN = 0
SUSPENDED_SCORE_CAP = 20


def _get_profile(subject_type: str, subject_id):
    if subject_type == TrustSubjectType.INSTRUCTOR:
        from apps.profiles.models import InstructorProfile
        return InstructorProfile.objects.get(id=subject_id)
    if subject_type == TrustSubjectType.RECRUITER:
        from apps.profiles.models import RecruiterProfile
        return RecruiterProfile.objects.get(id=subject_id)
    if subject_type == TrustSubjectType.ORGANIZATION:
        from apps.profiles.models import Organization
        return Organization.objects.get(id=subject_id)
    if subject_type == TrustSubjectType.LEARNER:
        from apps.profiles.models import LearnerProfile
        return LearnerProfile.objects.get(id=subject_id)
    raise ValueError(f"Unknown subject_type: {subject_type}")


def apply_trust_event(
    subject_type: str,
    subject_id,
    change_reason: str,
    actor=None,
    notes: str = "",
    override_value: int = None,
):
    profile = _get_profile(subject_type, subject_id)
    previous_score = profile.trust_score

    change_value = override_value if override_value is not None else SCORE_RULES.get(change_reason, 0)

    is_suspension_event = change_reason == TrustChangeReason.SUSPENDED
    is_already_suspended = (
        hasattr(profile, "verification_status")
        and profile.verification_status == "suspended"
    )

    # Skip zero-value non-suspension events
    if change_value == 0 and not is_suspension_event and not is_already_suspended:
        return previous_score

    raw_new_score = previous_score + change_value

    if is_suspension_event or is_already_suspended:
        new_score = max(SCORE_MIN, min(raw_new_score, SUSPENDED_SCORE_CAP))
    else:
        new_score = max(SCORE_MIN, min(SCORE_MAX, raw_new_score))

    profile.trust_score = new_score
    profile.trust_score_updated_at = timezone.now()
    profile.trust_score_reason_summary = _build_reason_summary(change_reason, change_value)
    profile.save(update_fields=["trust_score", "trust_score_updated_at", "trust_score_reason_summary"])

    TrustScoreLog.objects.create(
        subject_type=subject_type,
        subject_id=subject_id,
        previous_score=previous_score,
        new_score=new_score,
        change_value=change_value,
        change_reason=change_reason,
        calculated_by="staff" if actor else "system",
        actor=actor,
        notes=notes,
    )

    return new_score


def recalculate_full_score(subject_type: str, subject_id):
    logs = TrustScoreLog.objects.filter(
        subject_type=subject_type,
        subject_id=subject_id,
    ).order_by("performed_at")

    score = 0
    for log in logs:
        score = max(SCORE_MIN, min(SCORE_MAX, score + log.change_value))

    profile = _get_profile(subject_type, subject_id)
    profile.trust_score = score
    profile.trust_score_updated_at = timezone.now()
    profile.trust_score_reason_summary = "Recalculated from log history."
    profile.save(update_fields=["trust_score", "trust_score_updated_at", "trust_score_reason_summary"])

    return score


def _build_reason_summary(change_reason: str, change_value: int) -> str:
    sign = "+" if change_value >= 0 else ""
    label = TrustChangeReason(change_reason).label
    return f"Last change: {sign}{change_value} ({label})"