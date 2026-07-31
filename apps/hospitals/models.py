from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class HospitalType(models.TextChoices):
    GOVERNMENT = 'government', 'Government'
    PRIVATE = 'private', 'Private'
    COMMUNITY = 'community', 'Community'


class Hospital(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    hospital_type = models.CharField(max_length=20, choices=HospitalType.choices, default=HospitalType.GOVERNMENT)

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, default='Kathmandu', db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True)

    total_beds = models.PositiveIntegerField(default=0)
    available_beds = models.PositiveIntegerField(default=0)
    total_icu_beds = models.PositiveIntegerField(default=0)
    available_icu_beds = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to='hospital_images/', blank=True, null=True)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitals_hospital'
        ordering = ['name']
        indexes = [
            models.Index(fields=['city', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}
        if self.available_beds > self.total_beds:
            errors['available_beds'] = 'Available beds cannot exceed total beds.'
        if self.available_icu_beds > self.total_icu_beds:
            errors['available_icu_beds'] = 'Available ICU beds cannot exceed total ICU beds.'
        if errors:
            raise ValidationError(errors)

    @property
    def available_ambulance_count(self):
        return self.ambulances.filter(status=AmbulanceStatus.AVAILABLE).count()

    @property
    def total_ambulance_count(self):
        return self.ambulances.count()

    @property
    def bed_occupancy_percentage(self):
        if self.total_beds == 0:
            return 0
        occupied = self.total_beds - self.available_beds
        return round((occupied / self.total_beds) * 100, 1)

    @property
    def bed_status(self):
        if self.total_beds == 0 or self.available_beds == 0:
            return 'critical'
        if self.available_beds / self.total_beds <= 0.2:
            return 'limited'
        return 'available'

    @property
    def icu_status(self):
        if self.total_icu_beds == 0 or self.available_icu_beds == 0:
            return 'critical'
        if self.available_icu_beds / self.total_icu_beds <= 0.2:
            return 'limited'
        return 'available'

    @property
    def overall_status(self):
        statuses = {self.bed_status, self.icu_status}
        if 'critical' in statuses:
            return 'critical'
        if 'limited' in statuses:
            return 'limited'
        return 'available'

    @property
    def avatar_color(self):
        palette = ['#0F3D5C', '#1F9D63', '#C0392B', '#8E44AD', '#B9781A', '#16748C']
        return palette[sum(ord(c) for c in self.name) % len(palette)]


class AmbulanceStatus(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    DISPATCHED = 'dispatched', 'Dispatched'
    UNDER_MAINTENANCE = 'under_maintenance', 'Under Maintenance'


class Ambulance(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='ambulances')
    vehicle_number = models.CharField(max_length=20, unique=True, help_text='e.g. Ba 1 Kha 1234')
    driver_name = models.CharField(max_length=150, blank=True)
    driver_phone = models.CharField(max_length=15, blank=True)
    status = models.CharField(max_length=20, choices=AmbulanceStatus.choices, default=AmbulanceStatus.AVAILABLE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitals_ambulance'
        ordering = ['hospital', 'vehicle_number']

    def __str__(self):
        return f'{self.vehicle_number} ({self.hospital.name})'


class HospitalStaffProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff_members')
    position = models.CharField(max_length=100, blank=True, help_text='e.g. Bed Manager, Duty Officer')

    class Meta:
        db_table = 'hospitals_staff_profile'

    def __str__(self):
        return f'{self.user.username} @ {self.hospital.name}'