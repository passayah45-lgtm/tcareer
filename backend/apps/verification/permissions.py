from rest_framework.permissions import BasePermission
from apps.profiles.models import VerificationStatus


class IsVerificationStaff(BasePermission):
    # Grants access only to users in the verification_staff group or Django staff.
    # Used for all staff-only verification endpoints.

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        return request.user.groups.filter(name="verification_staff").exists()


class IsProfileOwner(BasePermission):
    # Used on document upload endpoints.
    # The view must set self.get_owner_user() or pass owner in context.
    # Checked at the object level by has_object_permission.

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class CanSubmitVerification(BasePermission):
    # Prevents suspended subjects from submitting new verification requests.
    # The view resolves the subject and calls this check.

    message = "Your account is suspended. Contact support to reinstate verification access."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def is_subject_suspended(self, subject) -> bool:
        return (
            hasattr(subject, "verification_status")
            and subject.verification_status == VerificationStatus.SUSPENDED
        )
