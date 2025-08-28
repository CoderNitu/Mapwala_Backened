# accounts/views.py
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import HasCapability
from .serializers import UserCreateSerializer, UserSerializer, CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('role', 'reports_to')
    lookup_field = 'id'
    permission_classes = [IsAuthenticated, HasCapability]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        self.required_capabilities = ['user.list']
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # 🔹 Admin-only restriction
        if not (request.user.is_superuser or (request.user.role and request.user.role.key.lower() == 'admin')):
            return Response(
                {'detail': 'Only Admins can create users'},
                status=status.HTTP_403_FORBIDDEN
            )

        self.required_capabilities = ['user.create']
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output_serializer = UserSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        target = self.get_object()
        if request.user.has_capability('user.view') or request.user.pk == target.pk or request.user.is_manager_of(target):
            return super().retrieve(request, *args, **kwargs)
        return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        # 🔹 Admin-only restriction
        if not (request.user.is_superuser or (request.user.role and request.user.role.key.lower() == 'admin')):
            return Response(
                {'detail': 'Only Admins can update users'},
                status=status.HTTP_403_FORBIDDEN
            )

        target = self.get_object()
        serializer = UserCreateSerializer(target, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output_serializer = UserSerializer(serializer.instance, context={'request': request})
        return Response(output_serializer.data)

    def destroy(self, request, *args, **kwargs):
        # 🔹 Admin-only restriction
        if not (request.user.is_superuser or (request.user.role and request.user.role.key.lower() == 'admin')):
            return Response(
                {'detail': 'Only Admins can delete users'},
                status=status.HTTP_403_FORBIDDEN
            )

        target = self.get_object()
        if not (request.user.has_capability('user.delete') or request.user.is_manager_of(target) or request.user.is_superuser):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='change_manager')
    def change_manager(self, request, id=None):
        target = self.get_object()
        caller = request.user

        # 🔹 Admin-only restriction
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == 'admin')):
            return Response(
                {'detail': 'Only Admins can change managers'},
                status=status.HTTP_403_FORBIDDEN
            )

        new_manager_id = request.data.get('reports_to')

        if new_manager_id is None:
            target.reports_to = None
            target.save()
            return Response(UserSerializer(target).data)

        try:
            new_manager = User.objects.get(pk=new_manager_id)
        except User.DoesNotExist:
            return Response({'detail': 'Manager not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent self-reporting & cycles
        if new_manager.pk == target.pk or target.is_manager_of(new_manager):
            return Response(
                {'detail': 'Invalid manager (would create cycle or self-reporting).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        target.reports_to = new_manager
        target.save()
        return Response(UserSerializer(target).data)
