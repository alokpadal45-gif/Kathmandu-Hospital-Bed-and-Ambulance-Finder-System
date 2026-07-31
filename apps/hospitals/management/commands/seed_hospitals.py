from django.core.management.base import BaseCommand

from apps.hospitals.models import Ambulance, Hospital, HospitalType

HOSPITALS = [
    {
        'name': 'Bir Hospital',
        'hospital_type': HospitalType.GOVERNMENT,
        'address': 'Mahaboudha',
        'city': 'Kathmandu',
        'latitude': '27.704000',
        'longitude': '85.313100',
        'phone_number': '014221119',
        'total_beds': 350, 'available_beds': 42,
        'total_icu_beds': 20, 'available_icu_beds': 3,
        'ambulances': ['Ba 1 Kha 1001', 'Ba 1 Kha 1002'],
    },
    {
        'name': 'Tribhuvan University Teaching Hospital',
        'hospital_type': HospitalType.GOVERNMENT,
        'address': 'Maharajgunj',
        'city': 'Kathmandu',
        'latitude': '27.739600',
        'longitude': '85.331500',
        'phone_number': '014412303',
        'total_beds': 700, 'available_beds': 65,
        'total_icu_beds': 40, 'available_icu_beds': 5,
        'ambulances': ['Ba 2 Kha 2001', 'Ba 2 Kha 2002', 'Ba 2 Kha 2003'],
    },
    {
        'name': 'Civil Service Hospital',
        'hospital_type': HospitalType.GOVERNMENT,
        'address': 'Minbhawan',
        'city': 'Kathmandu',
        'latitude': '27.695900',
        'longitude': '85.337800',
        'phone_number': '014107001',
        'total_beds': 200, 'available_beds': 18,
        'total_icu_beds': 12, 'available_icu_beds': 0,
        'ambulances': ['Ba 3 Kha 3001'],
    },
    {
        'name': 'Norvic International Hospital',
        'hospital_type': HospitalType.PRIVATE,
        'address': 'Thapathali',
        'city': 'Kathmandu',
        'latitude': '27.693500',
        'longitude': '85.317500',
        'phone_number': '014258554',
        'total_beds': 150, 'available_beds': 30,
        'total_icu_beds': 15, 'available_icu_beds': 4,
        'ambulances': ['Ba 4 Kha 4001', 'Ba 4 Kha 4002'],
    },
    {
        'name': 'Grande International Hospital',
        'hospital_type': HospitalType.PRIVATE,
        'address': 'Dhapasi',
        'city': 'Kathmandu',
        'latitude': '27.743300',
        'longitude': '85.337800',
        'phone_number': '014412600',
        'total_beds': 200, 'available_beds': 55,
        'total_icu_beds': 20, 'available_icu_beds': 6,
        'ambulances': ['Ba 5 Kha 5001', 'Ba 5 Kha 5002'],
    },
    {
        'name': 'Patan Hospital',
        'hospital_type': HospitalType.COMMUNITY,
        'address': 'Lagankhel',
        'city': 'Lalitpur',
        'latitude': '27.666700',
        'longitude': '85.324700',
        'phone_number': '015522278',
        'total_beds': 300, 'available_beds': 38,
        'total_icu_beds': 18, 'available_icu_beds': 2,
        'ambulances': ['Ba 6 Kha 6001'],
    },
    {
        'name': 'Nepal Mediciti Hospital',
        'hospital_type': HospitalType.PRIVATE,
        'address': 'Bhaisepati',
        'city': 'Lalitpur',
        'latitude': '27.628000',
        'longitude': '85.312000',
        'phone_number': '015902000',
        'total_beds': 300, 'available_beds': 70,
        'total_icu_beds': 25, 'available_icu_beds': 8,
        'ambulances': ['Ba 7 Kha 7001', 'Ba 7 Kha 7002'],
    },
    {
        'name': 'Kathmandu Model Hospital',
        'hospital_type': HospitalType.COMMUNITY,
        'address': 'Baneshwor',
        'city': 'Kathmandu',
        'latitude': '27.693900',
        'longitude': '85.333600',
        'phone_number': '014102037',
        'total_beds': 100, 'available_beds': 12,
        'total_icu_beds': 8, 'available_icu_beds': 1,
        'ambulances': ['Ba 8 Kha 8001'],
    },
]


class Command(BaseCommand):
    help = 'Seeds the database with real, named Kathmandu-area hospitals for demo purposes.'

    def handle(self, *args, **options):
        created_count = 0
        for entry in HOSPITALS:
            ambulance_numbers = entry.pop('ambulances')
            hospital, created = Hospital.objects.get_or_create(
                name=entry['name'],
                defaults=entry,
            )
            if created:
                created_count += 1
                for vehicle_number in ambulance_numbers:
                    Ambulance.objects.get_or_create(hospital=hospital, vehicle_number=vehicle_number)
                self.stdout.write(self.style.SUCCESS(f'Created: {hospital.name}'))
            else:
                self.stdout.write(f'Already exists, skipped: {hospital.name}')

        self.stdout.write(self.style.SUCCESS(f'\nDone — {created_count} new hospital(s) added.'))