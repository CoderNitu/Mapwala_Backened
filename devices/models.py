# devices/models.py
from django.db import models
from accounts.models import User, Role

class Device(models.Model):
    UNIT_OF_MEASURE_CHOICES = [
        ('PCS', 'Pieces (PCS)'),
        ('KG', 'Kilograms (KG)'),
        ('G', 'Grams (G)'),
        ('M', 'Meters (M)'),
        ('CM', 'Centimeters (CM)'),
        ('L', 'Liters (L)'),
        ('ML', 'Milliliters (ML)'),
    ]
    
    STATE_OF_SUPPLY_CHOICES = [
        ('RAW_MATERIAL', 'Raw Material'),
        ('WORK_IN_PROGRESS', 'Work in Progress'),
        ('FINISHED_GOODS', 'Finished Goods'),
        ('SEMI_FINISHED', 'Semi-Finished'),
        ('CONSUMABLE', 'Consumable'),
    ]
    
    # Device Information fields
    make_id = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role__key__iexact': 'manufacturer'},
        related_name='devices',
        help_text="Manufacturer of the device"
    )
    model = models.CharField(max_length=255)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(
        max_length=10, 
        choices=UNIT_OF_MEASURE_CHOICES
    )
    version = models.CharField(max_length=100, blank=True, null=True)
    variant = models.CharField(max_length=100, blank=True, null=True)
    state_of_supply = models.CharField(
        max_length=20, 
        choices=STATE_OF_SUPPLY_CHOICES
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_devices',
        null=True,  # Temporarily allow null
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'devices'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.manufacturer_name} - {self.model}"
    
    @property
    def manufacturer_name(self):
        """Return the manufacturer's username or first_name + last_name"""
        if self.make_id.first_name and self.make_id.last_name:
            return f"{self.make_id.first_name} {self.make_id.last_name}"
        return self.make_id.username