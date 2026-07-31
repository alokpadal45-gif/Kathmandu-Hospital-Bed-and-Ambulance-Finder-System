# This is the actual emergency request workflow - a citizen submits a
# request, a hospital accepts it and assigns one of their ambulances, then
# it goes out and comes back. Kept as one model with a status field rather
# than splitting into separate tables per stage since the whole point is
# tracking ONE request through its lifecycle, not the individual stages
# as separate objects.
#
# status flow:
#   PENDING -> ACCEPTED -> DISPATCHED -> COMPLETED
#   (can be CANCELLED any time before COMPLETED)

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.hospitals.models import Ambulance, AmbulanceStatus, Hospital


class RequestStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    DISPATCHED = 'dispatched', 'Dispatched'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class AmbulanceRequest(models.Model):
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ambulance_requests',
    )

    # hospital isn't required at request time - citizen just says where they
    # need pickup, and any hospital with an available ambulance can accept
    # it. once accepted, hospital gets filled in.
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='ambulance_requests',
    )
    assigned_ambulance = models.ForeignKey(
        Ambulance, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests',
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='accepted_requests',
        help_text='Hospital staff member who accepted this request.',
    )

    # who/where - patient info doesn't have to match the logged in citizen
    # since someone might be requesting on behalf of a family member
    patient_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=15)
    pickup_address = models.CharField(max_length=255)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    emergency_description = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)

    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ambulances_request'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Request #{self.pk} - {self.patient_name} ({self.get_status_display()})'

    # --- status transitions ---
    # putting these on the model instead of the view so the same rules
    # apply everywhere this gets called from (staff dashboard, api, admin)

    def accept(self, hospital, ambulance, staff_user):
        if self.status != RequestStatus.PENDING:
            raise ValidationError('Only pending requests can be accepted.')
        if ambulance.status != AmbulanceStatus.AVAILABLE:
            raise ValidationError('That ambulance is not available.')
        if ambulance.hospital_id != hospital.id:
            raise ValidationError('That ambulance does not belong to this hospital.')

        self.hospital = hospital
        self.assigned_ambulance = ambulance
        self.accepted_by = staff_user
        self.status = RequestStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

        ambulance.status = AmbulanceStatus.DISPATCHED
        ambulance.save()

    def mark_dispatched(self):
        if self.status != RequestStatus.ACCEPTED:
            raise ValidationError('Only accepted requests can be marked dispatched.')
        self.status = RequestStatus.DISPATCHED
        self.dispatched_at = timezone.now()
        self.save()

    def mark_completed(self):
        if self.status not in (RequestStatus.ACCEPTED, RequestStatus.DISPATCHED):
            raise ValidationError('Only accepted or dispatched requests can be completed.')
        self.status = RequestStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()

        # ambulance is back and free again
        if self.assigned_ambulance:
            self.assigned_ambulance.status = AmbulanceStatus.AVAILABLE
            self.assigned_ambulance.save()

    def cancel(self):
        if self.status == RequestStatus.COMPLETED:
            raise ValidationError('Completed requests cannot be cancelled.')

        # free up the ambulance if one was already assigned
        if self.assigned_ambulance and self.status in (RequestStatus.ACCEPTED, RequestStatus.DISPATCHED):
            self.assigned_ambulance.status = AmbulanceStatus.AVAILABLE
            self.assigned_ambulance.save()

        self.status = RequestStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.save()