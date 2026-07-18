from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from core.security_utils import validate_file_upload


class Category(models.Model):
    """A grouping for menu items, e.g. Pizza Cones, Drinks."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    """A single item for sale, e.g. Pepperoni Pizza Cone."""

    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True, help_text='Uncheck to 86 this item from the menu.')
    is_featured = models.BooleanField(default=False, help_text='Show a "New!" style badge on the menu.')
    calories = models.PositiveIntegerField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__display_order', 'display_order', 'name']

    def __str__(self):
        return self.name

    def clean(self):
        """OWASP #10: File upload validation."""
        super().clean()
        if self.image:
            validate_file_upload(self.image)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('menu:item_detail', kwargs={'slug': self.slug})

    @property
    def recipe(self):
        return self.ingredient_lines.select_related('ingredient').all()

    def missing_ingredients(self):
        """Return a list of ingredients this item needs but doesn't have enough of."""
        missing = []
        for line in self.recipe:
            if line.ingredient.quantity_on_hand < line.quantity_required:
                missing.append(line.ingredient)
        return missing

    def is_in_stock(self):
        """An item with no recipe defined is assumed always in stock."""
        return len(self.missing_ingredients()) == 0

    def max_sellable_quantity(self):
        """How many of this item could be sold right now, limited by ingredients on hand."""
        lines = list(self.recipe)
        if not lines:
            return None  # unlimited / not tracked
        possible = []
        for line in lines:
            if line.quantity_required <= 0:
                continue
            possible.append(int(line.ingredient.quantity_on_hand // line.quantity_required))
        return min(possible) if possible else None


class Ingredient(models.Model):
    """A stock-tracked ingredient/supply, e.g. Mozzarella Cheese, Cones, Pepperoni."""

    UNIT_CHOICES = [
        ('each', 'Each'),
        ('oz', 'Ounces'),
        ('lb', 'Pounds'),
        ('g', 'Grams'),
        ('kg', 'Kilograms'),
        ('l', 'Liters'),
        ('ml', 'Milliliters'),
    ]

    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='each')
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Get a low-stock alert once quantity on hand falls to/below this level.',
    )
    cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.quantity_on_hand} {self.get_unit_display()})'

    @property
    def is_low_stock(self):
        return self.quantity_on_hand <= self.reorder_threshold


class MenuItemIngredient(models.Model):
    """Recipe line: how much of an ingredient one unit of a menu item uses."""

    menu_item = models.ForeignKey(MenuItem, related_name='ingredient_lines', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name='used_in', on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    class Meta:
        unique_together = ('menu_item', 'ingredient')

    def __str__(self):
        return f'{self.menu_item.name} needs {self.quantity_required} {self.ingredient.get_unit_display()} of {self.ingredient.name}'
