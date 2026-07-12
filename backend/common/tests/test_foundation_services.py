import pytest
from django.utils import timezone
from types import SimpleNamespace

from apps.analytics.models import AnalyticsEvent
from apps.analytics.services import AnalyticsService
from apps.audit.models import AuditLog
from apps.careers.models import Portfolio, Resume, VisibilityChoice
from apps.courses.models import Course, CourseStatus, Enrollment, EnrollmentStatus, Lesson
from apps.organizations.models import (
    CandidateProfileUnlock,
    Organization,
    OrganizationMembership,
    OrganizationRecruiterEntitlement,
    OrganizationRole,
    OrganizationType,
)
from apps.organizations.services import OrganizationService
from apps.payments.models import Subscription, SubscriptionPlan, SubscriptionStatus
from apps.users.tests.factories import AdminFactory, InstructorFactory, RecruiterFactory, UserFactory
from common.audit import AuditService
from common.entitlements import EntitlementService
from common.privacy import PrivacyService
from common.permission_service import PermissionService


@pytest.mark.django_db
def test_permission_service_covers_org_assets_and_private_user_assets():
    admin = AdminFactory()
    owner = UserFactory()
    stranger = UserFactory()
    organization = Organization.objects.create(name="Org", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=owner,
        role=OrganizationRole.COMPANY_ADMIN,
    )
    portfolio = Portfolio.objects.create(user=owner, visibility=VisibilityChoice.PRIVATE)
    resume = Resume.objects.create(user=owner)

    assert PermissionService.can_manage_organization(owner, organization)
    assert PermissionService.can_view_organization(owner, organization)
    assert PermissionService.can_manage_portfolio(owner, portfolio)
    assert PermissionService.can_manage_resume(owner, resume)
    assert PermissionService.can_manage_portfolio(admin, portfolio)
    assert not PermissionService.can_manage_resume(stranger, resume)


@pytest.mark.django_db
def test_permission_service_allows_job_management_for_recruiter_membership():
    recruiter = RecruiterFactory()
    organization = Organization.objects.create(name="Hiring Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )

    job = SimpleNamespace(posted_by_id=None, organization=organization)

    assert PermissionService.can_manage_job(recruiter, job)


@pytest.mark.django_db
def test_entitlement_service_provider_neutral_checks():
    user = UserFactory()
    instructor = InstructorFactory()
    recruiter = RecruiterFactory()
    organization = Organization.objects.create(name="Hiring Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    course = Course.objects.create(
        instructor=instructor,
        title="Paid Course",
        slug="paid-course",
        status=CourseStatus.PUBLISHED,
        price=99,
    )
    lesson = Lesson.objects.create(course=course, title="Intro")

    assert not EntitlementService.can_access_course(user, course)
    Enrollment.objects.create(user=user, course=course, status=EnrollmentStatus.ACTIVE)
    assert EntitlementService.can_access_course(user, course)
    assert EntitlementService.can_use_ai_tutor(user, course)
    assert EntitlementService.can_post_job(recruiter, organization=organization)
    assert EntitlementService.can_search_candidates(recruiter, organization=organization)
    assert EntitlementService.can_view_candidate_profile(recruiter, user, organization=organization)
    assert lesson.course == course


@pytest.mark.django_db
def test_recruiter_seat_entitlement_limits_invites():
    admin = AdminFactory()
    company_admin = UserFactory()
    existing_recruiter = RecruiterFactory()
    new_recruiter = UserFactory(email="new-recruiter@example.com")
    organization = Organization.objects.create(name="Seat Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=company_admin,
        role=OrganizationRole.COMPANY_ADMIN,
    )

    assert not EntitlementService.can_invite_recruiter(company_admin, organization)

    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )
    assert EntitlementService.can_invite_recruiter(company_admin, organization)

    OrganizationService.add_member(
        actor=admin,
        organization=organization,
        user=existing_recruiter,
        role=OrganizationRole.RECRUITER,
    )
    assert EntitlementService.active_recruiter_seats(organization) == 1
    assert not EntitlementService.can_invite_recruiter(company_admin, organization)

    with pytest.raises(Exception):
        OrganizationService.invite_member(
            actor=company_admin,
            organization=organization,
            email=new_recruiter.email,
            role=OrganizationRole.RECRUITER,
        )


@pytest.mark.django_db
def test_candidate_profile_requires_visible_or_unlocked_profile():
    recruiter = RecruiterFactory()
    candidate = UserFactory(is_public_profile=False)
    organization = Organization.objects.create(name="Candidate Co", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(
        organization=organization,
        user=recruiter,
        role=OrganizationRole.RECRUITER,
    )
    OrganizationRecruiterEntitlement.objects.create(
        organization=organization,
        max_recruiter_seats=1,
        can_post_jobs=True,
        can_search_candidates=True,
        can_view_candidate_profiles=True,
    )

    assert not EntitlementService.can_view_candidate_profile(recruiter, candidate, organization=organization)

    privacy = PrivacyService.get_settings(candidate)
    privacy.public_profile = True
    privacy.save()
    assert EntitlementService.can_view_candidate_profile(recruiter, candidate, organization=organization)

    privacy.public_profile = False
    privacy.save()
    CandidateProfileUnlock.objects.create(
        organization=organization,
        candidate=candidate,
        unlocked_by=recruiter,
    )
    assert EntitlementService.can_view_candidate_profile(recruiter, candidate, organization=organization)


@pytest.mark.django_db
def test_subscription_unlocks_resume_and_portfolio_analysis():
    user = UserFactory()
    Subscription.objects.create(
        user=user,
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        plan=SubscriptionPlan.PRO,
        status=SubscriptionStatus.ACTIVE,
        current_period_end=timezone.now() + timezone.timedelta(days=10),
    )

    assert EntitlementService.can_use_resume_analysis(user)
    assert EntitlementService.can_use_portfolio_analysis(user)


@pytest.mark.django_db
def test_audit_log_is_append_only():
    user = UserFactory()
    log = AuditService.record(actor=user, action="admin_security_action", target=user)

    log.action = "tampered"
    with pytest.raises(ValueError):
        log.save()
    with pytest.raises(ValueError):
        log.delete()


@pytest.mark.django_db
def test_analytics_service_tracks_event():
    user = UserFactory()
    event = AnalyticsService.track(name="course_started", user=user, target=user, metadata={"source": "test"})

    assert isinstance(event, AnalyticsEvent)
    assert event.name == "course_started"
    assert event.user == user
    assert AnalyticsEvent.objects.filter(name="course_started").exists()
    assert AuditLog.objects.count() == 0
