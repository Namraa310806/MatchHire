from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user and user.is_authenticated and user.role == user.Roles.CANDIDATE
        )


class IsRecruiter(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user and user.is_authenticated and user.role == user.Roles.RECRUITER
        )


class IsVerifiedUser(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_verified)


class IsProfileOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        return bool(
            user and user.is_authenticated and getattr(obj, "user", None) == user
        )


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class CandidateAndVerified(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.role == user.Roles.CANDIDATE
            and user.is_verified
        )


class RecruiterAndVerified(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.role == user.Roles.RECRUITER
            and user.is_verified
        )
