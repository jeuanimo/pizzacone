from datetime import timedelta, time

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import LocationStop


class Command(BaseCommand):
    help = 'Seeds a few sample location stops (today + upcoming) for The Pizza Cone Co.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        sample_stops = [
            {
                'date': today,
                'start_time': time(11, 0),
                'end_time': time(19, 0),
                'name': 'Downtown Farmers Market',
                'address': '200 Main St, Anytown, USA',
                'latitude': 39.781721,
                'longitude': -89.650148,
                'notes': 'Look for the red tent by the fountain!',
            },
            {
                'date': today + timedelta(days=2),
                'start_time': time(11, 30),
                'end_time': time(20, 0),
                'name': 'Riverside Food Truck Park',
                'address': '450 Riverside Dr, Anytown, USA',
                'latitude': 39.789200,
                'longitude': -89.644500,
                'notes': '',
            },
            {
                'date': today + timedelta(days=5),
                'start_time': time(12, 0),
                'end_time': time(18, 0),
                'name': 'Oak Street Block Party',
                'address': 'Oak St & 5th Ave, Anytown, USA',
                'latitude': 39.775300,
                'longitude': -89.657900,
                'notes': 'Live music all afternoon.',
            },
            {
                'date': today + timedelta(days=9),
                'start_time': time(11, 0),
                'end_time': time(19, 0),
                'name': 'Downtown Farmers Market',
                'address': '200 Main St, Anytown, USA',
                'latitude': 39.781721,
                'longitude': -89.650148,
                'notes': '',
            },
        ]

        for data in sample_stops:
            obj, created = LocationStop.objects.get_or_create(
                date=data['date'], name=data['name'], defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Added stop: {obj.name} on {obj.date}'))
            else:
                self.stdout.write(f'Stop on {obj.date} already exists, skipping.')

        self.stdout.write(self.style.SUCCESS('Schedule seeding complete.'))
