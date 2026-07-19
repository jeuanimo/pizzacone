from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from menu.csv_import import DEFAULT_IMAGES_DIR, import_menu_items_csv


class Command(BaseCommand):
    help = 'Create or update menu items (and attach their images) from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path', nargs='?', default=str(settings.BASE_DIR / 'menu' / 'data' / 'menu_items.csv'),
            help='Path to the CSV file (default: menu/data/menu_items.csv)',
        )
        parser.add_argument(
            '--images-dir', default=str(DEFAULT_IMAGES_DIR),
            help='Directory to look up image filenames in (default: menu/seed_images/)',
        )
        parser.add_argument(
            '--overwrite-images', action='store_true',
            help='Replace existing images too (default: only fill in items missing an image)',
        )

    def handle(self, *args, **options):
        try:
            with open(options['csv_path'], encoding='utf-8-sig'):
                pass
        except OSError as exc:
            raise CommandError(f'Could not open {options["csv_path"]}: {exc}')

        result = import_menu_items_csv(
            options['csv_path'],
            images_dir=options['images_dir'],
            overwrite_images=options['overwrite_images'],
        )

        self.stdout.write(self.style.SUCCESS(
            f'Created {result.created}, updated {result.updated}, '
            f'images attached {result.images_attached}.'
        ))
        for error in result.errors:
            self.stderr.write(self.style.ERROR(error))

        if result.errors:
            raise CommandError(f'{len(result.errors)} row(s) failed — see above.')
