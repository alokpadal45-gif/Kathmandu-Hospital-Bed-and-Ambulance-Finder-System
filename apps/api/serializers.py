from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.ambulances.models import AmbulanceRequest
from apps.hospitals.models import Ambulance, Hospital


class HospitalSerializer(serializers.ModelSerializer):
    # these come from properties on the model, not actual db fields, so
    # they need to be declared explicitly here
    available_ambulance_count = serializers.ReadOnlyField()
    total_ambulance_count = serializers.ReadOnlyField()
    bed_occupancy_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'hospital_type', 'address', 'city',
            'latitude', 'longitude', 'phone_number', 'email',
            'image', 'description', 'is_active',
            'total_beds', 'available_beds',
            'total_icu_beds', 'available_icu_beds',
            'available_ambulance_count', 'total_ambulance_count',
            'bed_occupancy_percentage',
        ]
        read_only_fields = ['id']


class HospitalAvailabilityUpdateSerializer(serializers.ModelSerializer):
    """
    Used specifically for the "update my hospital's availability" endpoint
    that hospital staff use (Step 8's dashboard hits this). Deliberately
    only exposes the 4 live counters - staff shouldn't be able to change
    the hospital's name/address/location through this one.
    """

    class Meta:
        model = Hospital
        fields = ['total_beds', 'available_beds', 'total_icu_beds', 'available_icu_beds']

    def validate(self, attrs):
        # run the same available <= total check that lives on the model,
        # so this endpoint can't be used to bypass it
        instance = self.instance
        total_beds = attrs.get('total_beds', instance.total_beds)
        available_beds = attrs.get('available_beds', instance.available_beds)
        total_icu = attrs.get('total_icu_beds', instance.total_icu_beds)
        available_icu = attrs.get('available_icu_beds', instance.available_icu_beds)

        errors = {}
        if available_beds > total_beds:
            errors['available_beds'] = 'Available beds cannot exceed total beds.'
        if available_icu > total_icu:
            errors['available_icu_beds'] = 'Available ICU beds cannot exceed total ICU beds.'
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class AmbulanceSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)

    class Meta:
        model = Ambulance
        fields = [
            'id', 'hospital', 'hospital_name', 'vehicle_number',
            'driver_name', 'driver_phone', 'status',
        ]


class AmbulanceRequestCreateSerializer(serializers.ModelSerializer):
    """What a citizen submits to ask for an ambulance. citizen and status
    get set automatically, not passed in by the client."""

    class Meta:
        model = AmbulanceRequest
        fields = [
            'id', 'patient_name', 'contact_number', 'pickup_address',
            'pickup_latitude', 'pickup_longitude', 'emergency_description',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data['citizen'] = self.context['request'].user
        return super().create(validated_data)


class AmbulanceRequestDetailSerializer(serializers.ModelSerializer):
    """Full read view of a request - used for listing/detail, and for
    citizens tracking their own request's status."""

    citizen_username = serializers.CharField(source='citizen.username', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True, default=None)
    ambulance_number = serializers.CharField(source='assigned_ambulance.vehicle_number', read_only=True, default=None)

    class Meta:
        model = AmbulanceRequest
        fields = [
            'id', 'citizen_username', 'patient_name', 'contact_number',
            'pickup_address', 'pickup_latitude', 'pickup_longitude',
            'emergency_description', 'status',
            'hospital', 'hospital_name', 'assigned_ambulance', 'ambulance_number',
            'requested_at', 'accepted_at', 'dispatched_at', 'completed_at', 'cancelled_at',
        ]
        read_only_fields = fields


class AcceptRequestSerializer(serializers.Serializer):
    """Input for the 'accept' action on a pending request - staff picks
    which of their hospital's ambulances to send."""
    ambulance_id = serializers.IntegerField()

    def validate_ambulance_id(self, value):
        try:
            self.ambulance = Ambulance.objects.get(pk=value)
        except Ambulance.DoesNotExist:
            raise serializers.ValidationError('Ambulance not found.')
        return value