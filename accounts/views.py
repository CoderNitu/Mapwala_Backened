# accounts/views.py
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, State
from .permissions import HasCapability
from .serializers import UserCreateSerializer, UserSerializer, CustomTokenObtainPairSerializer, AdminUserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('role', 'reports_to', 'state')
    lookup_field = 'id'
    permission_classes = [IsAuthenticated, HasCapability]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateSerializer
        return UserSerializer

    def get_list_serializer_class(self):
        """
        Return appropriate serializer for list view based on requesting user's role
        """
        if self.request.user.is_authenticated and self.request.user.role and self.request.user.role.key.lower() == 'admin':
            return AdminUserSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        self.required_capabilities = ['user.list']
        
        # Get queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Paginate if needed
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Use UserSerializer for all - it will automatically handle admin vs non-admin users
            serializer = UserSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        # Non-paginated response
        serializer = UserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        target = self.get_object()
        if request.user.has_capability('user.view') or request.user.pk == target.pk or request.user.is_manager_of(target):
            # Use UserSerializer - it will automatically handle admin vs non-admin users
            serializer = UserSerializer(target, context={'request': request})
            return Response(serializer.data)
        return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    def create(self, request, *args, **kwargs):
        caller = request.user
        data = request.data.copy()

        # 🔹 Admin-only restriction for admin role
        if data.get('role') in ['admin', 'Admin']:
            if not (caller.is_superuser or (caller.role and caller.role.key.lower() == 'admin')):
                return Response(
                    {'detail': 'Only Admins can create admin users'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Handle reports_to: can be ID or phone_number
        reports_to_value = data.get('reports_to')
        if reports_to_value:
            try:
                if str(reports_to_value).isdigit():
                    manager = User.objects.get(pk=int(reports_to_value))
                else:
                    manager = User.objects.get(phone_number=reports_to_value)
                data['reports_to'] = manager.pk
            except User.DoesNotExist:
                return Response({'detail': 'Manager not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return response using UserSerializer - it will handle the appropriate format
        output_serializer = UserSerializer(serializer.instance, context={'request': request})
        
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        caller = request.user
        target = self.get_object()
        data = request.data.copy()

        # 🔹 Admin-only restriction for admin role
        if data.get('role') in ['admin', 'Admin']:
            if not (caller.is_superuser or (caller.role and caller.role.key.lower() == 'admin')):
                return Response(
                    {'detail': 'Only Admins can assign admin role'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Handle reports_to: ID or phone_number
        reports_to_value = data.get('reports_to')
        if reports_to_value:
            try:
                if reports_to_value.isdigit() and len(reports_to_value) >= 6:
                    manager = User.objects.get(pk=reports_to_value)
                else:
                    manager = User.objects.get(phone_number=reports_to_value)
                data['reports_to'] = manager.pk
            except User.DoesNotExist:
                return Response({'detail': 'Manager not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserCreateSerializer(target, data=data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return response using UserSerializer - it will handle the appropriate format
        output_serializer = UserSerializer(serializer.instance, context={'request': request})
        
        return Response(output_serializer.data)

    def destroy(self, request, *args, **kwargs):
        caller = request.user
        if not (caller.is_superuser or (caller.role and caller.role.key.lower() == 'admin')):
            return Response(
                {'detail': 'Only Admins can delete users'},
                status=status.HTTP_403_FORBIDDEN
            )

        target = self.get_object()
        if not (caller.has_capability('user.delete') or caller.is_manager_of(target) or caller.is_superuser):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='change_manager')
    def change_manager(self, request, id=None):
      target = self.get_object()
      caller = request.user

      if not (caller.is_superuser or (caller.role and caller.role.key.lower() == 'admin')):
        return Response(
            {'detail': 'Only Admins can change managers'},
            status=status.HTTP_403_FORBIDDEN
        )

      new_manager_value = request.data.get('reports_to')

    # Case: removing manager
      if new_manager_value is None or new_manager_value == "":
        target.reports_to = None
        target.save()
        return Response(UserSerializer(target, context={'request': request}).data)

      try:
        # Normalize to string for checking
        new_manager_str = str(new_manager_value)

        # If numeric and length < 6 treat as ID, otherwise phone_number
        if new_manager_str.isdigit() and len(new_manager_str) < 6:
            new_manager = User.objects.get(pk=int(new_manager_str))
        else:
            new_manager = User.objects.get(phone_number=new_manager_str)

      except User.DoesNotExist:
        return Response({'detail': 'Manager not found'}, status=status.HTTP_400_BAD_REQUEST)

    # Prevent cycles/self-reporting
      if new_manager.pk == target.pk or target.is_manager_of(new_manager):
        return Response(
            {'detail': 'Invalid manager (would create cycle or self-reporting).'},
            status=status.HTTP_400_BAD_REQUEST
        )

      target.reports_to = new_manager
      target.save()

      return Response(UserSerializer(target, context={'request': request}).data)

