# Custom user model.
# Using Django's default User isn't enough here because we have 4 types of
# users (citizen, hospital staff, admin, health authority) and each one
# needs different permissions/dashboards. Adding a role field to a custom
# user model from the start is easier than trying to change it later.

from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    # health_authority is a future feature mentioned in the report, adding
    # it now so I don't have to run a new migration for it later
    CITIZEN = 'citizen', 'Citizen'
    HOSPITAL_STAFF = 'hospital_staff', 'Hospital Staff'
    ADMIN = 'admin', 'System Administrator'
    HEALTH_AUTHORITY = 'health_authority', 'Health Authority'


class User(AbstractUser):
    # extending AbstractUser so we keep all the built in auth stuff
    # (password hashing, permissions etc) and just add what we need

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CITIZEN,
        help_text='Which dashboard/permissions this account gets.',
    )

    phone_number = models.CharField(max_length=15, blank=True)

    # citizens get verified automatically when they sign up, but hospital
    # staff/health authority accounts need an admin to approve them first
    is_verified = models.BooleanField(
        default=False,
        help_text='Non-citizen accounts need admin approval before they can log in.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    # small helper properties so I'm not typing user.role == 'citizen'
    # everywhere in views/templates
    @property
    def is_citizen(self):
        return self.role == UserRole.CITIZEN

    @property
    def is_hospital_staff(self):
        return self.role == UserRole.HOSPITAL_STAFF

    @property
    def is_admin_role(self):
        # called is_admin_role and not is_admin so it doesn't get confused
        # with django's built in is_staff/is_superuser
        return self.role == UserRole.ADMIN

    @property
    def is_health_authority(self):
        return self.role == UserRole.HEALTH_AUTHORITY