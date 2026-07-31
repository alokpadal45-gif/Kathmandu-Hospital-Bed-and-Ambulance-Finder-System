from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import User, UserRole
from apps.hospitals.models import Ambulance, AmbulanceStatus, Hospital

from .models import AmbulanceRequest, RequestStatus


class AmbulanceRequestLifecycleTests(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name='Bir Hospital', address='Mahaboudha', city='Kathmandu',
            latitude='27.704000', longitude='85.313100', phone_number='014221119',
        )
        self.ambulance = Ambulance.objects.create(hospital=self.hospital, vehicle_number='Ba 1 Kha 1234')
        self.citizen = User.objects.create_user(username='citizen1', password='Pass!2026', role=UserRole.CITIZEN)
        self.staff = User.objects.create_user(username='staff1', password='Pass!2026', role=UserRole.HOSPITAL_STAFF)
        self.request = AmbulanceRequest.objects.create(
            citizen=self.citizen, patient_name='Test Patient',
            contact_number='9800000000', pickup_address='Baneshwor',
        )

    def test_starts_pending(self):
        self.assertEqual(self.request.status, RequestStatus.PENDING)

    def test_cannot_complete_pending_request(self):
        with self.assertRaises(ValidationError):
            self.request.mark_completed()

    def test_accept_assigns_ambulance_and_dispatches_it(self):
        self.request.accept(hospital=self.hospital, ambulance=self.ambulance, staff_user=self.staff)
        self.ambulance.refresh_from_db()
        self.assertEqual(self.request.status, RequestStatus.ACCEPTED)
        self.assertEqual(self.ambulance.status, AmbulanceStatus.DISPATCHED)

    def test_cannot_double_accept(self):
        self.request.accept(hospital=self.hospital, ambulance=self.ambulance, staff_user=self.staff)
        with self.assertRaises(ValidationError):
            self.request.accept(hospital=self.hospital, ambulance=self.ambulance, staff_user=self.staff)

    def test_full_lifecycle_frees_ambulance(self):
        self.request.accept(hospital=self.hospital, ambulance=self.ambulance, staff_user=self.staff)
        self.request.mark_dispatched()
        self.request.mark_completed()
        self.ambulance.refresh_from_db()
        self.assertEqual(self.request.status, RequestStatus.COMPLETED)
        self.assertEqual(self.ambulance.status, AmbulanceStatus.AVAILABLE)

    def test_cancel_after_accept_frees_ambulance(self):
        self.request.accept(hospital=self.hospital, ambulance=self.ambulance, staff_user=self.staff)
        self.request.cancel()
        self.ambulance.refresh_from_db()
        self.assertEqual(self.request.status, RequestStatus.CANCELLED)
        self.assertEqual(self.ambulance.status, AmbulanceStatus.AVAILABLE)

    def test_completed_request_cannot_be_cancelled(self):
        self.request.accept(hospital=self.hospital, ambulance=self.ambulance, staff_user=self.staff)
        self.request.mark_dispatched()
        self.request.mark_completed()
        with self.assertRaises(ValidationError):
            self.request.cancel()