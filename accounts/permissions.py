# accounts/permissions.py
from rest_framework import permissions

class HasCapability(permissions.BasePermission):
    """
    Checks view.required_capabilities OR view.required_all_capabilities.
    If none defined, this permission allows through (other permissions may still apply).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_any = getattr(view, 'required_capabilities', None)
        required_all = getattr(view, 'required_all_capabilities', None)

        if not required_any and not required_all:
            return True

        if required_all:
            return all(request.user.has_capability(code) for code in required_all)

        return any(request.user.has_capability(code) for code in required_any)
