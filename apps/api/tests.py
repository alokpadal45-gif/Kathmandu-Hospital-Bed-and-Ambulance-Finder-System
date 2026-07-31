from rest_framework.test import APITestCase

from apps.accounts.models import User, UserRole
from apps.ambulances.models import AmbulanceRequest
from apps.hospitals.models import Ambulance, Hospital, HospitalStaffProfile


class HospitalPermissionTests(APITestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name='Bir Hospital', address='Mahaboudha', city='Kathmandu',
            latitude='27.704000', longitude='85.313100', phone_number='014221119',
            total_beds=100, available_beds=20,
        )
        self.citizen = User.objects.create_user(username='citizen1', password='Pass!2026', role=UserRole.CITIZEN)
        self.owning_staff = User.objects.create_user(username='staff1', password='Pass!2026', role=UserRole.HOSPITAL_STAFF)
        HospitalStaffProfile.objects.create(user=self.owning_staff, hospital=self.hospital)
        self.other_staff = User.objects.create_user(username='staff2', password='Pass!2026', role=UserRole.HOSPITAL_STAFF)

    def test_citizen_can_list_hospitals(self):
        self.client.force_authenticate(user=self.citizen)
        response = self.client.get('/api/hospitals/')
        self.assertEqual(response.status_code, 200)

    def test_citizen_cannot_update_hospital(self):
        self.client.force_authenticate(user=self.citizen)
        response = self.client.patch(f'/api/hospitals/{self.hospital.id}/', {'available_beds': 5})
        self.assertEqual(response.status_code, 403)

    def test_owning_staff_can_update_hospital(self):
        self.client.force_authenticate(user=self.owning_staff)
        response = self.client.patch(f'/api/hospitals/{self.hospital.id}/', {'available_beds': 5})
        self.assertEqual(response.status_code, 200)

    def test_other_hospital_staff_cannot_update(self):
        self.client.force_authenticate(user=self.other_staff)
        response = self.client.patch(f'/api/hospitals/{self.hospital.id}/', {'available_beds': 5})
        self.assertEqual(response.status_code, 403)

    def test_invalid_availability_rejected(self):
        self.client.force_authenticate(user=self.owning_staff)
        response = self.client.patch(f'/api/hospitals/{self.hospital.id}/', {'available_beds': 999})
        self.assertEqual(response.status_code, 400)


class AmbulanceRequestAPITests(APITestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name='Bir Hospital', address='Mahaboudha', city='Kathmandu',
            latitude='27.704000', longitude='85.313100', phone_number='014221119',
        )
        self.ambulance = Ambulance.objects.create(hospital=self.hospital, vehicle_number='Ba 1 Kha 1234')
        self.citizen = User.objects.create_user(username='citizen1', password='Pass!2026', role=UserRole.CITIZEN)
        self.staff = User.objects.create_user(username='staff1', password='Pass!2026', role=UserRole.HOSPITAL_STAFF)
        HospitalStaffProfile.objects.create(user=self.staff, hospital=self.hospital)

    def test_citizen_creates_and_sees_own_request(self):
        self.client.force_authenticate(user=self.citizen)
        response = self.client.post('/api/requests/', {
            'patient_name': 'Test Patient', 'contact_number': '9800000000', 'pickup_address': 'Baneshwor',
        })
        self.assertEqual(response.status_code, 201)

        listing = self.client.get('/api/requests/')
        self.assertEqual(len(listing.data['results'] if 'results' in listing.data else listing.data), 1)

    def test_staff_accepts_and_completes_request(self):
        req = AmbulanceRequest.objects.create(
            citizen=self.citizen, patient_name='Test Patient',
            contact_number='9800000000', pickup_address='Baneshwor',
        )
        self.client.force_authenticate(user=self.staff)

        accept_response = self.client.post(f'/api/requests/{req.id}/accept/', {'ambulance_id': self.ambulance.id})
        self.assertEqual(accept_response.status_code, 200)
        self.assertEqual(accept_response.data['status'], 'accepted')

        complete_response = self.client.post(f'/api/requests/{req.id}/mark-completed/')
        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(complete_response.data['status'], 'completed')

    def test_citizen_cannot_dispatch_request(self):
        req = AmbulanceRequest.objects.create(
            citizen=self.citizen, patient_name='Test Patient',
            contact_number='9800000000', pickup_address='Baneshwor',
        )
        self.client.force_authenticate(user=self.citizen)
        response = self.client.post(f'/api/requests/{req.id}/mark-dispatched/')
        self.assertEqual(response.status_code, 403)