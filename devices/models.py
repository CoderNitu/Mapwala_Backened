# devices/models.py
from django.db import models
from accounts.models import User

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
    
    # New field for BOM quantity
    quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Total quantity for this device BOM")
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_devices',
        null=True,
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

# ---- BOM entries MODEL ----
class BOMEntry(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='bom_entries')
    identification_mark = models.CharField(max_length=255, blank=True, null=True)
    components_required = models.CharField(max_length=255, blank=True, null=True)
    designator = models.CharField(max_length=255, blank=True, null=True)
    ship_qty = models.PositiveIntegerField(default=0)
    fp_cross_checked = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_bom_entries'
        ordering = ['created_at']
        verbose_name = "BOM Entry"
        verbose_name_plural = "BOM Entries"

    def __str__(self):
        return f"{self.device.model} - {self.components_required or 'N/A'}"
    

# --- ENCLOSURE MODEL---

class Enclosure(models.Model):
    """Stores enclosure details for a specific device."""
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='enclosure')
    make = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role__key__iexact': 'manufacturer'},
        related_name='enclosures',
        help_text="Manufacturer of the enclosure"
    )
    part_no = models.CharField(max_length=100)
    length = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    breadth = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    height = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_enclosures'
        ordering = ['-created_at']

    def __str__(self):
        return f"Enclosure for {self.device.model} - Part No: {self.part_no}"
    

# --- WIRE HARNESS MODEL ---

class WireHarness(models.Model):
    """Stores wire harness details for a specific device."""
    # UPDATED: The database key (first element) now matches the display label
    PIN_TYPE_CHOICES = [
        ('1 Pin', '1 Pin'),
        ('2 Pin', '2 Pin'),
        ('3 Pin', '3 Pin'),
        ('4 Pin', '4 Pin'),
        ('5 Pin', '5 Pin'),
        ('6 Pin', '6 Pin'),
        ('7 Pin', '7 Pin'),
        ('8 Pin', '8 Pin'),
        ('9 Pin', '9 Pin'),
        ('10 Pin', '10 Pin'),
    ]

    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='wire_harness')
    make = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role__key__iexact': 'manufacturer'},
        related_name='wire_harnesses',
        help_text="Manufacturer of the wire harness"
    )
    part_no = models.CharField(max_length=100)
    no_of_wires = models.PositiveIntegerField()
    color = models.CharField(max_length=50)
    length = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    no_of_connectors = models.PositiveIntegerField()
    pin_type = models.CharField(max_length=10, choices=PIN_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_wire_harnesses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Wire Harness for {self.device.model} - Part No: {self.part_no}"
    

# --- BATTERY MODEL ---

class Battery(models.Model):
    """Stores battery details for a specific device."""
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='battery')
    make = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role__key__iexact': 'manufacturer'},
        related_name='batteries',
        help_text="Manufacturer of the battery"
    )
    part_no = models.CharField(max_length=100)
    capacity = models.CharField(max_length=50, help_text="e.g., 850 mAH, 2000 mAh")
    length = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    breadth = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    height = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_batteries'
        ordering = ['-created_at']
        verbose_name_plural = "Batteries" # Fix for Django admin pluralization

    def __str__(self):
        return f"Battery for {self.device.model} - Part No: {self.part_no}"
    

# --- SOSBUTTON MODEL ---

class SOSButton(models.Model):
    """Stores SOS Button details for a specific device."""
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='sos_button')
    make = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role__key__iexact': 'manufacturer'},
        related_name='sos_buttons',
        help_text="Manufacturer of the SOS Button"
    )
    part_no = models.CharField(max_length=100)
    total_length = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total length at the set (in mm)")
    quantity_per_set = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_sos_buttons'
        ordering = ['-created_at']

    def __str__(self):
        return f"SOS Button for {self.device.model} - Part No: {self.part_no}"
    

# --- STICKER MODEL ---

def get_sticker_upload_path(instance, filename):
    return f'devices/stickers/device_{instance.device.id}/{filename}'

class Sticker(models.Model):
    """Stores sticker details for a specific device."""
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='sticker')
    name = models.CharField(max_length=255)
    make = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role__key__iexact': 'manufacturer'},
        related_name='stickers',
        help_text="Manufacturer of the sticker"
    )
    part_no = models.CharField(max_length=100)
    length = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    breadth = models.DecimalField(max_digits=10, decimal_places=2, help_text="in mm")
    quantity = models.PositiveIntegerField()
    sticker_image = models.ImageField(upload_to=get_sticker_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_stickers'
        ordering = ['-created_at']

    def __str__(self):
        return f"Sticker for {self.device.model} - {self.name}"
    





