# devices/views.py
import pandas as pd
import io
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from .models import Device, BOMEntry, Enclosure, WireHarness, Battery, SOSButton, Sticker
from .serializers import (
    DeviceSerializer, 
    DeviceCreateSerializer, 
    ManufacturerSerializer, 
    BOMEntrySerializer,
    EnclosureSerializer,
    WireHarnessSerializer,
    BatterySerializer,
    SOSButtonSerializer,
    StickerSerializer
)
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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    device = serializer.save(created_by=self.request.user)
                    response_serializer = DeviceSerializer(device)
                    return Response({
                        'success': True,
                        'message': 'Device created successfully. Please proceed to BOM Entry.',
                        'data': response_serializer.data
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'success': False, 'message': 'Failed to create device', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'message': 'Devices retrieved successfully', 'data': serializer.data, 'count': queryset.count()})
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'message': 'Device retrieved successfully', 'data': serializer.data})
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    device = serializer.save()
                    return Response({'success': True, 'message': 'Device updated successfully', 'data': serializer.data})
            except Exception as e:
                return Response({'success': False, 'message': 'Failed to update device', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = False
        instance.save()
        return Response({'success': True, 'message': 'Device deleted successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='manufacturers')
    def get_manufacturers(self, request):
        try:
            manufacturers = User.objects.filter(role__key__iexact='manufacturer', is_active=True)
            serializer = ManufacturerSerializer(manufacturers, many=True)
            return Response({'success': True, 'message': 'Manufacturers retrieved successfully', 'data': serializer.data})
        except Exception as e:
            return Response({'success': False, 'message': 'Failed to retrieve manufacturers', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='choices')
    def get_device_choices(self, request):
        try:
            choices_data = {
                'unit_of_measure_choices': [{'value': c[0], 'label': c[1]} for c in Device.UNIT_OF_MEASURE_CHOICES],
                'state_of_supply_choices': [{'value': c[0], 'label': c[1]} for c in Device.STATE_OF_SUPPLY_CHOICES],
                'pin_type_choices': [{'value': c[0], 'label': c[1]} for c in WireHarness.PIN_TYPE_CHOICES],
            }
            return Response({'success': True, 'message': 'Device choices retrieved successfully', 'data': choices_data})
        except Exception as e:
            return Response({'success': False, 'message': 'Failed to retrieve device choices', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='add-bom')
    def add_bom(self, request, pk=None):
        try:
            device = self.get_object()
            upload_type = request.data.get('bom_upload_type')
            quantity = request.data.get('quantity')

            if quantity is not None:
                try:
                    device.quantity = int(quantity)
                    device.save()
                except (ValueError, TypeError):
                    return Response({'success': False, 'message': 'Invalid quantity provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
            BOMEntry.objects.filter(device=device).delete()
            bom_entries_to_create = []

            if upload_type == 'Individual entry':
                manual_entries = request.data.get('manual_entries', [])
                if not isinstance(manual_entries, list):
                     return Response({'success': False, 'message': "'manual_entries' must be a list."}, status=status.HTTP_400_BAD_REQUEST)
                for entry in manual_entries:
                    bom_entries_to_create.append(BOMEntry(device=device, **entry))

            elif upload_type == 'Bulk upload':
                bom_file = request.FILES.get('bom_file')
                if not bom_file:
                    return Response({'success': False, 'message': 'BOM file is required for bulk upload.'}, status=status.HTTP_400_BAD_REQUEST)
                df = pd.read_excel(bom_file)
                df.columns = [c.strip().upper().replace(' ', '_').lower() for c in df.columns]
                for index, row in df.iterrows():
                    bom_entries_to_create.append(BOMEntry(device=device, **row.to_dict()))
            else:
                return Response({'success': False, 'message': 'Invalid BOM Upload Type.'}, status=status.HTTP_400_BAD_REQUEST)

            if bom_entries_to_create:
                BOMEntry.objects.bulk_create(bom_entries_to_create)
            
            device.refresh_from_db()
            serializer = self.get_serializer(device)
            return Response({'success': True, 'message': 'BOM entries saved successfully.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'success': False, 'message': f'Error processing request: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='download-sample-bom')
    def download_sample_bom(self, request):
        headers = ['IDENTIFICATION MARK', 'COMPONENTS REQUIRED', 'Designator', 'SHIP QTY', 'FP CROSS CHECKED']
        df = pd.DataFrame(columns=headers)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='BOM_Sample')
        output.seek(0)
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="bom_sample.xlsx"'
        return response

    @action(detail=True, methods=['post'], url_path='add-enclosure')
    def add_enclosure(self, request, pk=None):
        try:
            device = self.get_object()
        except Device.DoesNotExist:
             return Response({'success': False, 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = EnclosureSerializer(data=request.data)
        if serializer.is_valid():
            enclosure, created = Enclosure.objects.update_or_create(device=device, defaults=serializer.validated_data)
            device.refresh_from_db()
            device_serializer = self.get_serializer(device)
            message = 'Enclosure created successfully.' if created else 'Enclosure updated successfully.'
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response({'success': True, 'message': message, 'data': device_serializer.data}, status=status_code)
        else:
            return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='add-wire-harness')
    def add_wire_harness(self, request, pk=None):
        try:
            device = self.get_object()
        except Device.DoesNotExist:
             return Response({'success': False, 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WireHarnessSerializer(data=request.data)
        if serializer.is_valid():
            harness, created = WireHarness.objects.update_or_create(device=device, defaults=serializer.validated_data)
            device.refresh_from_db()
            device_serializer = self.get_serializer(device)
            message = 'Wire Harness created successfully.' if created else 'Wire Harness updated successfully.'
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response({'success': True, 'message': message, 'data': device_serializer.data}, status=status_code)
        else:
            return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='add-battery')
    def add_battery(self, request, pk=None):
        try:
            device = self.get_object()
        except Device.DoesNotExist:
             return Response({'success': False, 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BatterySerializer(data=request.data)
        if serializer.is_valid():
            battery, created = Battery.objects.update_or_create(device=device, defaults=serializer.validated_data)
            device.refresh_from_db()
            device_serializer = self.get_serializer(device)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            message = 'Battery created successfully.' if created else 'Battery updated successfully.'
            return Response({'success': True, 'message': message, 'data': device_serializer.data}, status=status_code)
        else:
            return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='add-sos-button')
    def add_sos_button(self, request, pk=None):
        try:
            device = self.get_object()
        except Device.DoesNotExist:
             return Response({'success': False, 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SOSButtonSerializer(data=request.data)
        if serializer.is_valid():
            sos_button, created = SOSButton.objects.update_or_create(device=device, defaults=serializer.validated_data)
            device.refresh_from_db()
            device_serializer = self.get_serializer(device)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            message = 'SOS Button created successfully.' if created else 'SOS Button updated successfully.'
            return Response({'success': True, 'message': message, 'data': device_serializer.data}, status=status_code)
        else:
            return Response({'success': False, 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
   
    @action(detail=True, methods=['post'], url_path='add-sticker')
    def add_sticker(self, request, pk=None):
        """
        Action to add or update a sticker for a specific device.
        Handles multipart/form-data for the image upload.
        """
        try:
            device = self.get_object()
        except Device.DoesNotExist:
             return Response({'success': False, 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StickerSerializer(data=request.data)
        if serializer.is_valid():
            sticker, created = Sticker.objects.update_or_create(
                device=device,
                defaults=serializer.validated_data
            )
            
            device.refresh_from_db()
            device_serializer = self.get_serializer(device)
            
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            message = 'Sticker created successfully.' if created else 'Sticker updated successfully.'
            
            return Response({
                'success': True, 
                'message': message, 
                'data': device_serializer.data
            }, status=status_code)
        else:
            return Response({
                'success': False, 
                'message': 'Validation failed', 
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

