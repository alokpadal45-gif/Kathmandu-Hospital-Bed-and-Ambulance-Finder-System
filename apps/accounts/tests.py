from django.test import Client, TestCase
from django.urls import reverse

from .models import User, UserRole


class SignUpTests(TestCase):
    def test_signup_creates_verified_citizen(self):
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'ram_thapa',
            'first_name': 'Ram',
            'last_name': 'Thapa',
            'email': 'ram@example.com',
            'phone_number': '9812345678',
            'password1': 'StrongPass!2026',
            'password2': 'StrongPass!2026',
        })
        self.assertRedirects(response, reverse('accounts:login'))
        user = User.objects.get(username='ram_thapa')
        self.assertEqual(user.role, UserRole.CITIZEN)
        self.assertTrue(user.is_verified)

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='existing', email='dupe@example.com', password='Pass!2026')
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'dupe@example.com',
            'phone_number': '9800000000',
            'password1': 'StrongPass!2026',
            'password2': 'StrongPass!2026',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class LoginVerificationTests(TestCase):
    def test_unverified_staff_cannot_login(self):
        User.objects.create_user(
            username='staff_unverified', password='Pass!2026',
            role=UserRole.HOSPITAL_STAFF, is_verified=False,
        )
        response = self.client.post(reverse('accounts:login'), {
            'username': 'staff_unverified', 'password': 'Pass!2026',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_verified_staff_can_login(self):
        User.objects.create_user(
            username='staff_verified', password='Pass!2026',
            role=UserRole.HOSPITAL_STAFF, is_verified=True,
        )
        response = self.client.post(reverse('accounts:login'), {
            'username': 'staff_verified', 'password': 'Pass!2026',
        }, follow=True)
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class RoleRequiredDecoratorTests(TestCase):
    def test_citizen_blocked_from_staff_dashboard(self):
        User.objects.create_user(username='citizen1', password='Pass!2026', role=UserRole.CITIZEN, is_verified=True)
        client = Client()
        client.login(username='citizen1', password='Pass!2026')
        response = client.get(reverse('dashboard:staff_dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[0][0], reverse('dashboard:home'))
        self.assertEqual(response.request['PATH_INFO'], reverse('dashboard:citizen_hospitals'))