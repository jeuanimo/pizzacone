"""Shared CSV import logic for menu items, used by both the
`import_menu_items` management command and the staff dashboard's
CSV upload view.

Expected columns (header row required): slug, name, category, price,
description, image, calories, display_order, is_available, is_featured

`image` is a filename looked up in `images_dir` (defaults to
menu/seed_images/, which is committed to git) — set it blank to leave
an item's image untouched.
"""
import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import transaction

from .models import Category, MenuItem

DEFAULT_IMAGES_DIR = Path(settings.BASE_DIR) / 'menu' / 'seed_images'
REQUIRED_COLUMNS = {'slug', 'name', 'category', 'price'}
TRUE_VALUES = {'1', 'true', 'yes', 'y'}


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    images_attached: int = 0
    errors: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors


def _parse_bool(value, default=False):
    if value is None or value == '':
        return default
    return value.strip().lower() in TRUE_VALUES


def _parse_decimal(value, field_name):
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f'invalid {field_name} "{value}"')


def _parse_int(value):
    value = (value or '').strip()
    return int(value) if value else None


def import_menu_items_csv(csv_file, images_dir=None, overwrite_images=False):
    """Import/update menu items from a CSV file-like object or path.

    `csv_file` may be a path (str/Path), a text-mode file object, or an
    uploaded file (bytes) such as request.FILES['csv_file'].
    """
    images_dir = Path(images_dir) if images_dir else DEFAULT_IMAGES_DIR
    result = ImportResult()

    if isinstance(csv_file, (str, Path)):
        text = Path(csv_file).read_text(encoding='utf-8-sig')
    elif hasattr(csv_file, 'read'):
        raw = csv_file.read()
        text = raw.decode('utf-8-sig') if isinstance(raw, bytes) else raw
    else:
        raise ValueError('csv_file must be a path or a file-like object')

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        result.errors.append(f'CSV is missing required column(s): {", ".join(sorted(missing))}')
        return result

    for line_num, row in enumerate(reader, start=2):  # header is line 1
        slug = (row.get('slug') or '').strip()
        name = (row.get('name') or '').strip()
        category_name = (row.get('category') or '').strip()

        if not slug or not name or not category_name:
            result.errors.append(f'Row {line_num}: slug, name, and category are required')
            continue

        try:
            with transaction.atomic():
                price = _parse_decimal(row.get('price'), 'price')
                category, _ = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'display_order': 0},
                )

                item, created = MenuItem.objects.get_or_create(
                    slug=slug,
                    defaults={'name': name, 'category': category, 'price': price},
                )
                item.name = name
                item.category = category
                item.price = price
                item.description = row.get('description') or ''
                item.calories = _parse_int(row.get('calories'))
                item.display_order = _parse_int(row.get('display_order')) or 0
                item.is_available = _parse_bool(row.get('is_available'), default=True)
                item.is_featured = _parse_bool(row.get('is_featured'), default=False)

                image_name = (row.get('image') or '').strip()
                if image_name and (overwrite_images or not item.image):
                    image_path = images_dir / image_name
                    if not image_path.exists():
                        raise ValueError(f'image "{image_name}" not found in {images_dir}')
                    with open(image_path, 'rb') as f:
                        item.image.save(image_name, File(f), save=False)
                    result.images_attached += 1

                item.full_clean()
                item.save()

            if created:
                result.created += 1
            else:
                result.updated += 1
        except Exception as exc:
            result.errors.append(f'Row {line_num} ({slug or name}): {exc}')

    return result
