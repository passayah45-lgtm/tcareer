from django.urls import path
from . import views

app_name = "verification"

urlpatterns = [
    # User-facing endpoints
    path("upload/", views.upload_document, name="upload_document"),
    path("submit/", views.submit_verification, name="submit_verification"),
    path("my-status/", views.my_verification_status, name="my_verification_status"),

    # Staff queue and review
    path("staff/queue/", views.staff_verification_queue, name="staff_queue"),
    path("staff/queue/<uuid:request_id>/", views.staff_verification_detail, name="staff_detail"),
    path("staff/queue/<uuid:request_id>/assign/", views.staff_assign, name="staff_assign"),
    path("staff/queue/<uuid:request_id>/approve/", views.staff_approve, name="staff_approve"),
    path("staff/queue/<uuid:request_id>/reject/", views.staff_reject, name="staff_reject"),
    path("staff/queue/<uuid:request_id>/more-info/", views.staff_more_info, name="staff_more_info"),

    # Staff subject actions (not tied to a specific request)
    path("staff/subjects/<str:subject_type>/<uuid:subject_id>/suspend/", views.staff_suspend, name="staff_suspend"),
    path("staff/subjects/<str:subject_type>/<uuid:subject_id>/reinstate/", views.staff_reinstate, name="staff_reinstate"),

    # Staff document access
    path("staff/documents/<uuid:document_id>/signed-url/", views.staff_signed_document_url, name="staff_signed_url"),

    # Staff audit log
    path("staff/audit-log/", views.staff_audit_log, name="staff_audit_log"),
]
