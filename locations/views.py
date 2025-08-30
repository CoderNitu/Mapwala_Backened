from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import District
from .serializers import DistrictSerializer
from accounts.models import State
from accounts.permissions import HasCapability  # optional (see note)
from accounts.serializers import StateSerializer

# For simplicity, reuse your existing HasCapability permission if you prefer.
# If HasCapability lives in accounts.permissions, import that instead.
from accounts.permissions import HasCapability


class DistrictViewSet(viewsets.ModelViewSet):
    """
    CRUD for Districts.
    Only authenticated users; create/update/delete restricted to admins (enforced in methods below).
    """

    queryset = District.objects.select_related("state").all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated, HasCapability]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code", "state__name"]
    ordering_fields = ["name", "code", "state__name"]

    def perform_create(self, serializer):
        # Only superuser or role=admin allowed to create
        caller = self.request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == "admin")):
            return Response({"detail": "Only Admins can create districts"}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def create(self, request, *args, **kwargs):
        # supervisor wrapper: check permission and return friendly message if not allowed
        caller = request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == "admin")):
            return Response({"detail": "Only Admins can create districts"}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        caller = request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == "admin")):
            return Response({"detail": "Only Admins can update districts"}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        caller = request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == "admin")):
            return Response({"detail": "Only Admins can delete districts"}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class StateViewSet(viewsets.ModelViewSet):
    """
    Minimal controller for States (read + admin create/update/delete).
    We reuse the State model in accounts; this ViewSet provides admin-friendly CRUD and list + search.
    """

    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated, HasCapability]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]

    def create(self, request, *args, **kwargs):
        caller = request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == "admin")):
            return Response({"detail": "Only Admins can create states"}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        caller = request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == "admin")):
            return Response({"detail": "Only Admins can update states"}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        caller = request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == "admin")):
            return Response({"detail": "Only Admins can delete states"}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

