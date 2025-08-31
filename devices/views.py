# devices/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Device
from .serializers import DeviceSerializer, DeviceCreateSerializer, ManufacturerSerializer
from accounts.models import User

class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for Device CRUD operations"""
    queryset = Device.objects.filter(status=True)
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeviceCreateSerializer
        return DeviceSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    device = serializer.save()
                    response_serializer = DeviceSerializer(device)
                    return Response({
                        'success': True,
                        'message': 'Device created successfully',
                        'data': response_serializer.data
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Failed to create device',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Devices retrieved successfully',
            'data': serializer.data,
            'count': queryset.count()
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Device retrieved successfully',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    device = serializer.save()
                    return Response({
                        'success': True,
                        'message': 'Device updated successfully',
                        'data': serializer.data
                    })
            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Failed to update device',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = False
        instance.save()
        return Response({
            'success': True,
            'message': 'Device deleted successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='manufacturers')
    def get_manufacturers(self, request):
        """Custom action to get all manufacturers for dropdown"""
        try:
            manufacturers = User.objects.filter(role__key__iexact='manufacturer', is_active=True)
            serializer = ManufacturerSerializer(manufacturers, many=True)
            return Response({
                'success': True,
                'message': 'Manufacturers retrieved successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to retrieve manufacturers',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='choices')
    def get_device_choices(self, request):
        """Custom action to get all dropdown choices for device form"""
        try:
            choices_data = {
                'unit_of_measure_choices': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Device.UNIT_OF_MEASURE_CHOICES
                ],
                'state_of_supply_choices': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in Device.STATE_OF_SUPPLY_CHOICES
                ]
            }
            return Response({
                'success': True,
                'message': 'Device choices retrieved successfully',
                'data': choices_data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to retrieve device choices',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UnitOfMeasurementViewSet(viewsets.ViewSet):
    """ViewSet for Unit of Measurement choices"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get all unit of measurement choices"""
        try:
            choices = [
                {'value': choice[0], 'label': choice[1]} 
                for choice in Device.UNIT_OF_MEASURE_CHOICES
            ]
            return Response({
                'success': True,
                'message': 'Unit of measurement choices retrieved successfully',
                'data': choices
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to retrieve unit of measurement choices',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)