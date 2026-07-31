from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Ambulance, AmbulanceStatus, Hospital, HospitalType


class HospitalValidationTests(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name='Bir Hospital', hospital_type=HospitalType.GOVERNMENT,
            address='Mahaboudha', city='Kathmandu',
            latitude='27.704000', longitude='85.313100',
            phone_number='014221119',
            total_beds=100, available_beds=15,
            total_icu_beds=20, available_icu_beds=2,
        )

    def test_valid_hospital_passes_clean(self):
        self.hospital.full_clean()

    def test_available_beds_cannot_exceed_total(self):
        self.hospital.available_beds = 999
        with self.assertRaises(ValidationError):
            self.hospital.full_clean()

    def test_available_icu_cannot_exceed_total(self):
        self.hospital.available_icu_beds = 999
        with self.assertRaises(ValidationError):
            self.hospital.full_clean()

    def test_bed_occupancy_percentage(self):
        self.assertEqual(self.hospital.bed_occupancy_percentage, 85.0)


class AmbulanceCountTests(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name='TU Teaching Hospital', address='Maharajgunj', city='Kathmandu',
            latitude='27.740000', longitude='85.331000', phone_number='014412303',
        )

    def test_available_and_total_counts(self):
        Ambulance.objects.create(hospital=self.hospital, vehicle_number='Ba 1 Kha 1111')
        Ambulance.objects.create(hospital=self.hospital, vehicle_number='Ba 1 Kha 2222', status=AmbulanceStatus.DISPATCHED)

        self.assertEqual(self.hospital.total_ambulance_count, 2)
        self.assertEqual(self.hospital.available_ambulance_count, 1)