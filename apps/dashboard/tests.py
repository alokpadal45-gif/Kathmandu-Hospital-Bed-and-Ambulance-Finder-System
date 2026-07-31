from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.ambulances.models import AmbulanceRequest
from apps.hospitals.models import Ambulance, Hospital, HospitalStaffProfile


class CitizenDashboardTests(TestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(username='citizen1', password='Pass!2026', role=UserRole.CITIZEN, is_verified=True)
        self.hospital = Hospital.objects.create(
            name='Bir Hospital', address='Mahaboudha', city='Kathmandu',
            latitude='27.704000', longitude='85.313100', phone_number='014221119',
        )
        self.client.login(username='citizen1', password='Pass!2026')

    def test_login_redirects_to_hospital_search(self):
        response = self.client.get(reverse('dashboard:home'), follow=True)
        self.assertRedirects(response, reverse('dashboard:citizen_hospitals'))

    def test_hospital_search_shows_active_hospitals(self):
        response = self.client.get(reverse('dashboard:citizen_hospitals'))
        self.assertContains(response, 'Bir Hospital')

    def test_ambulance_request_creation(self):
        response = self.client.post(reverse('dashboard:request_ambulance'), {
            'patient_name': 'Test Patient', 'contact_number': '9800000000', 'pickup_address': 'Baneshwor',
        }, follow=True)
        self.assertTrue(AmbulanceRequest.objects.filter(patient_name='Test Patient').exists())

    def test_cannot_view_someone_elses_request(self):
        other_citizen = User.objects.create_user(username='citizen2', password='Pass!2026', role=UserRole.CITIZEN, is_verified=True)
        req = AmbulanceRequest.objects.create(
            citizen=other_citizen, patient_name='Other Patient',
            contact_number='9800000001', pickup_address='Koteshwor',
        )
        response = self.client.get(reverse('dashboard:request_detail', args=[req.id]))
        self.assertEqual(response.status_code, 404)


class HospitalStaffDashboardTests(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(
            name='Bir Hospital', address='Mahaboudha', city='Kathmandu',
            latitude='27.704000', longitude='85.313100', phone_number='014221119',
        )
        self.ambulance = Ambulance.objects.create(hospital=self.hospital, vehicle_number='Ba 1 Kha 1234')
        self.staff = User.objects.create_user(username='staff1', password='Pass!2026', role=UserRole.HOSPITAL_STAFF, is_verified=True)
        HospitalStaffProfile.objects.create(user=self.staff, hospital=self.hospital)
        self.client.login(username='staff1', password='Pass!2026')

    def test_unlinked_staff_sees_setup_message(self):
        unlinked = User.objects.create_user(username='staff2', password='Pass!2026', role=UserRole.HOSPITAL_STAFF, is_verified=True)
        client = self.client_class()
        client.login(username='staff2', password='Pass!2026')
        response = client.get(reverse('dashboard:staff_dashboard'))
        self.assertContains(response, 'not linked to a hospital')

    def test_availability_update_rejects_invalid_data(self):
        response = self.client.post(reverse('dashboard:staff_update_availability'), {
            'total_beds': 10, 'available_beds': 999, 'total_icu_beds': 5, 'available_icu_beds': 0,
        })
        self.hospital.refresh_from_db()
        self.assertNotEqual(self.hospital.available_beds, 999)

    def test_accept_request_dispatches_ambulance(self):
        citizen = User.objects.create_user(username='citizen1', password='Pass!2026', role=UserRole.CITIZEN)
        req = AmbulanceRequest.objects.create(
            citizen=citizen, patient_name='Test Patient',
            contact_number='9800000000', pickup_address='Baneshwor',
        )
        self.client.post(reverse('dashboard:staff_accept_request', args=[req.id]), {'ambulance_id': self.ambulance.id})
        req.refresh_from_db()
        self.assertEqual(req.status, 'accepted')


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin1', password='Pass!2026', role=UserRole.ADMIN, is_verified=True)
        self.hospital = Hospital.objects.create(
            name='Bir Hospital', address='Mahaboudha', city='Kathmandu',
            latitude='27.704000', longitude='85.313100', phone_number='014221119',
        )
        self.client.login(username='admin1', password='Pass!2026')

    def test_verify_hospital_staff_creates_profile(self):
        pending = User.objects.create_user(username='staff1', password='Pass!2026', role=UserRole.HOSPITAL_STAFF, is_verified=False)
        self.client.post(reverse('dashboard:admin_verify_account', args=[pending.id]), {
            'hospital_id': self.hospital.id, 'position': 'Bed Manager',
        })
        pending.refresh_from_db()
        self.assertTrue(pending.is_verified)
        self.assertTrue(HospitalStaffProfile.objects.filter(user=pending, hospital=self.hospital).exists())

    def test_reject_account_deletes_it(self):
        pending = User.objects.create_user(username='sketchy', password='Pass!2026', role=UserRole.HOSPITAL_STAFF, is_verified=False)
        self.client.post(reverse('dashboard:admin_reject_account', args=[pending.id]))
        self.assertFalse(User.objects.filter(username='sketchy').exists())

    def test_toggle_hospital_active(self):
        self.client.post(reverse('dashboard:admin_toggle_hospital', args=[self.hospital.id]))
        self.hospital.refresh_from_db()
        self.assertFalse(self.hospital.is_active)