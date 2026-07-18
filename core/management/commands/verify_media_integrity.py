from django.core.management.base import BaseCommand, CommandError

from core.models import LocationStop
from menu.models import MenuItem


class Command(BaseCommand):
    help = (
        'Checks that image files referenced in the database exist in media storage '
        '(menu items and location stops).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-on-missing',
            action='store_true',
            help='Exit with non-zero status when any missing files are found.',
        )

    def handle(self, *args, **options):
        fail_on_missing = options['fail_on_missing']

        missing = []
        summary = {
            'menu_items_checked': 0,
            'location_stops_checked': 0,
        }

        for item in MenuItem.objects.exclude(image='').exclude(image__isnull=True):
            summary['menu_items_checked'] += 1
            if not item.image.storage.exists(item.image.name):
                missing.append(
                    f'MenuItem id={item.id} name="{item.name}" missing file: {item.image.name}'
                )

        for stop in LocationStop.objects.exclude(image='').exclude(image__isnull=True):
            summary['location_stops_checked'] += 1
            if not stop.image.storage.exists(stop.image.name):
                missing.append(
                    f'LocationStop id={stop.id} name="{stop.name}" missing file: {stop.image.name}'
                )

        self.stdout.write(self.style.NOTICE('Media integrity report'))
        self.stdout.write(
            f'- Menu item images checked: {summary["menu_items_checked"]}\n'
            f'- Location stop images checked: {summary["location_stops_checked"]}'
        )

        if missing:
            self.stdout.write(self.style.WARNING(f'- Missing files found: {len(missing)}'))
            for entry in missing:
                self.stdout.write(self.style.WARNING(f'  * {entry}'))
            if fail_on_missing:
                raise CommandError('Missing media files detected.')
        else:
            self.stdout.write(self.style.SUCCESS('- Missing files found: 0'))
            self.stdout.write(self.style.SUCCESS('All referenced image files are present.'))
