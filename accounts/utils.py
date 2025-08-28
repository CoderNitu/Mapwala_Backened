# accounts/utils.py
from functools import wraps
from rest_framework.exceptions import PermissionDenied

def require_capabilities(*capabilities, require_all=False):
    def decorator(func):
        @wraps(func)
        def inner(self, request, *args, **kwargs):
            user = request.user
            if not user or not user.is_authenticated:
                raise PermissionDenied("Authentication required")
            if require_all:
                ok = all(user.has_capability(c) for c in capabilities)
            else:
                ok = any(user.has_capability(c) for c in capabilities)
            if not ok:
                raise PermissionDenied("Insufficient capabilities")
            return func(self, request, *args, **kwargs)
        return inner
    return decorator
