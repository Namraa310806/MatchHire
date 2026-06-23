from rest_framework.permissions import BasePermission

from apps.users.permissions import IsRecruiter


class IsJobOwner(BasePermission):
    """Permission to check if user is the owner of the job"""
    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and obj.recruiter == user)
