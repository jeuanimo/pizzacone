from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.conf import settings

from menu.models import Category, MenuItem, Ingredient, MenuItemIngredient


class Command(BaseCommand):
    help = 'Seeds the database with The Pizza Cone Co. starter menu.'

    def handle(self, *args, **options):
        cones, _ = Category.objects.get_or_create(
            slug='pizza-cones',
            defaults={
                'name': 'Pizza Cones',
                'description': 'Hot, fresh pizza baked right into a crispy cone.',
                'display_order': 1,
            },
        )
        drinks, _ = Category.objects.get_or_create(
            slug='drinks',
            defaults={'name': 'Drinks', 'description': 'Something cold to wash it down.', 'display_order': 2},
        )

        items = [
            {
                'name': 'Cheese',
                'slug': 'cheese',
                'category': cones,
                'price': '6.99',
                'description': 'Classic, creamy melted mozzarella cheese with zesty pizza sauce in a golden baked cone.',
                'image': 'cheese.jpg',
                'display_order': 1,
            },
            {
                'name': 'Pepperoni',
                'slug': 'pepperoni',
                'category': cones,
                'price': '7.99',
                'description': 'Zesty pepperoni and gooey mozzarella cheese with zesty pizza sauce in every delicious bite.',
                'image': 'pepperoni.jpg',
                'display_order': 2,
            },
            {
                'name': 'Italian Sausage',
                'slug': 'italian-sausage',
                'category': cones,
                'price': '7.99',
                'description': 'Savory Italian sausage and melted mozzarella cheese with zesty pizza sauce in our signature cone.',
                'image': 'italian-sausage.jpg',
                'display_order': 3,
            },
            {
                'name': 'Veggie',
                'slug': 'veggie',
                'category': cones,
                'price': '7.99',
                'description': 'Fresh bell peppers, onions, olives, mushrooms, melted mozzarella cheese, and our zesty pizza sauce in a crispy cone.',
                'image': 'veggie.jpg',
                'display_order': 4,
            },
            {
                'name': 'Meat Lovers',
                'slug': 'meat-lovers',
                'category': cones,
                'price': '8.99',
                'description': "Loaded with pepperoni, Italian sausage, bacon, and melted mozzarella cheese with our zesty pizza sauce — our ultimate cone.",
                'image': 'meat-lovers.jpg',
                'display_order': 5,
            },
            {
                'name': 'Frozen Lemonade',
                'slug': 'frozen-lemonade',
                'category': drinks,
                'price': '4.49',
                'description': 'Frozen lemonade with real strawberries. Choose your fruit: strawberries, pineapples, or peaches.',
                'image': 'frozen-lemonade.jpg',
                'display_order': 1,
                'is_featured': True,
            },
        ]

        media_dir = Path(__file__).resolve().parent.parent.parent / 'seed_images'

        for data in items:
            image_name = data.pop('image')
            obj, created = MenuItem.objects.get_or_create(slug=data['slug'], defaults=data)
            if created:
                image_path = media_dir / image_name
                if image_path.exists():
                    with open(image_path, 'rb') as f:
                        obj.image.save(image_name, File(f), save=True)
                self.stdout.write(self.style.SUCCESS(f'Created "{obj.name}"'))
            else:
                self.stdout.write(f'"{obj.name}" already exists, skipping.')

        self.stdout.write(self.style.SUCCESS('Menu seeding complete.'))

        # ---------------- Ingredients & recipes ----------------
        ingredients_data = [
            {'name': 'Cone Shell', 'unit': 'each', 'quantity_on_hand': 100, 'reorder_threshold': 20},
            {'name': 'Mozzarella Cheese', 'unit': 'oz', 'quantity_on_hand': 400, 'reorder_threshold': 50},
            {'name': 'Pizza Sauce', 'unit': 'oz', 'quantity_on_hand': 300, 'reorder_threshold': 40},
            {'name': 'Pepperoni', 'unit': 'oz', 'quantity_on_hand': 150, 'reorder_threshold': 25},
            {'name': 'Italian Sausage', 'unit': 'oz', 'quantity_on_hand': 150, 'reorder_threshold': 25},
            {'name': 'Bacon', 'unit': 'oz', 'quantity_on_hand': 100, 'reorder_threshold': 20},
            {'name': 'Bell Peppers', 'unit': 'oz', 'quantity_on_hand': 80, 'reorder_threshold': 15},
            {'name': 'Red Onions', 'unit': 'oz', 'quantity_on_hand': 80, 'reorder_threshold': 15},
            {'name': 'Black Olives', 'unit': 'oz', 'quantity_on_hand': 60, 'reorder_threshold': 10},
            {'name': 'Mushrooms', 'unit': 'oz', 'quantity_on_hand': 60, 'reorder_threshold': 10},
            {'name': 'Frozen Lemonade Base', 'unit': 'oz', 'quantity_on_hand': 200, 'reorder_threshold': 30},
            {'name': 'Strawberries', 'unit': 'oz', 'quantity_on_hand': 100, 'reorder_threshold': 20},
        ]
        ingredients = {}
        for data in ingredients_data:
            obj, created = Ingredient.objects.get_or_create(name=data['name'], defaults=data)
            ingredients[data['name']] = obj
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created ingredient "{obj.name}"'))

        recipes = {
            'cheese': [('Cone Shell', 1), ('Mozzarella Cheese', 4), ('Pizza Sauce', 2)],
            'pepperoni': [('Cone Shell', 1), ('Mozzarella Cheese', 4), ('Pizza Sauce', 2), ('Pepperoni', 2)],
            'italian-sausage': [('Cone Shell', 1), ('Mozzarella Cheese', 4), ('Pizza Sauce', 2), ('Italian Sausage', 2)],
            'veggie': [
                ('Cone Shell', 1), ('Mozzarella Cheese', 4), ('Pizza Sauce', 2),
                ('Bell Peppers', 1), ('Red Onions', 1), ('Black Olives', 1), ('Mushrooms', 1),
            ],
            'meat-lovers': [
                ('Cone Shell', 1), ('Mozzarella Cheese', 4), ('Pizza Sauce', 2),
                ('Pepperoni', 1), ('Italian Sausage', 1), ('Bacon', 1),
            ],
            'frozen-lemonade': [('Frozen Lemonade Base', 8), ('Strawberries', 2)],
        }

        for slug, lines in recipes.items():
            try:
                item = MenuItem.objects.get(slug=slug)
            except MenuItem.DoesNotExist:
                continue
            for ingredient_name, qty in lines:
                MenuItemIngredient.objects.get_or_create(
                    menu_item=item,
                    ingredient=ingredients[ingredient_name],
                    defaults={'quantity_required': qty},
                )

        self.stdout.write(self.style.SUCCESS('Inventory + recipes seeded.'))
