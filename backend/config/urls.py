from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from common import health as health_views
from common import platform_management as platform_management_views
from common import platform_operations as platform_operations_views


def health_check(request):
    return JsonResponse({"status": "ok", "service": "tcareer-api"})


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),

    path("api/v1/health/", health_views.health, name="api-health"),
    path("api/v1/health/ready/", health_views.ready, name="api-health-ready"),
    path("api/v1/health/live/", health_views.live, name="api-health-live"),
    path("api/v1/health/ops/", health_views.ops, name="api-health-ops"),
    path("api/v1/platform/management/dashboard/", platform_management_views.platform_management_dashboard, name="platform-management-dashboard"),
    path("api/v1/platform/operations/", platform_operations_views.platform_operations, name="platform-operations"),
    path("api/v1/platform/audit/", platform_operations_views.platform_audit_search, name="platform-audit-search"),
    path("api/v1/platform/verification/", platform_operations_views.platform_verification_queue, name="platform-verification-queue"),
    path("api/v1/platform/verification/<uuid:request_id>/", platform_operations_views.platform_verification_detail, name="platform-verification-detail"),
    path(
        "api/v1/platform/verification/<uuid:request_id>/<str:action>/",
        platform_operations_views.platform_verification_action,
        name="platform-verification-action",
    ),
    path(
        "api/v1/platform/operations/<str:resource>/<uuid:object_id>/<str:action>/",
        platform_operations_views.platform_operation_action,
        name="platform-operation-action",
    ),

    path("api/v1/auth/", include("apps.users.urls", namespace="users")),
    path("api/v1/courses/", include("apps.courses.urls", namespace="courses")),
    path("api/v1/assessments/", include("apps.assessments.urls", namespace="assessments")),
    path("api/v1/careers/", include("apps.careers.urls", namespace="careers")),
    path("api/v1/certificates/", include("apps.certificates.urls", namespace="certificates")),
    path("api/v1/ai/", include("apps.ai_platform.urls", namespace="ai_platform")),
    path("api/v1/ai/", include("apps.ai_tutor.urls", namespace="ai_tutor")),
    path("api/v1/jobs/", include("apps.jobs.urls", namespace="jobs")),
    path("api/v1/payments/", include("apps.payments.urls", namespace="payments")),
    path("api/v1/tracks/", include("apps.tracks.urls", namespace="tracks")),
    path("api/v1/community/", include("apps.community.urls", namespace="community")),
    path("api/v1/notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("api/v1/search/", include("apps.search.urls", namespace="search")),
    path("api/v1/geo/", include("apps.geo.urls", namespace="geo")),
    path("api/v1/profiles/", include("apps.profiles.urls", namespace="profiles")),
    path("api/v1/verification/", include("apps.verification.urls", namespace="verification")),
    path("api/v1/organizations/", include("apps.organizations.urls", namespace="organizations")),

    path("social/", include("social_django.urls", namespace="social")),

    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
