from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """Allows access only to users with the student role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )


class IsInstructor(BasePermission):
    """Allows access only to users with the instructor role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "instructor"
        )


class IsRecruiter(BasePermission):
    """Allows access only to users with the recruiter role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "recruiter"
        )


class IsAdmin(BasePermission):
    """Allows access only to platform administrators."""

    def has_permission(self, request, view):
        from common.permission_service import PermissionService

        return PermissionService.is_platform_admin(request.user)


class IsOwner(BasePermission):
    """
    Object-level permission: only the owner of an object can access it.
    The object must have a `user` attribute pointing to the owning user.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsInstructorOrReadOnly(BasePermission):
    """
    Read-only for everyone authenticated.
    Write operations require the instructor role.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.role == "instructor"
