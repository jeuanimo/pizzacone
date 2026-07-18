from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Sum

from menu.models import MenuItem


class Sale(models.Model):
    """A single counter transaction, logged by staff after ringing up a customer."""

    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_OTHER = 'other'
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_CARD, 'Card'),
        (PAYMENT_OTHER, 'Other'),
    ]

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales'
    )
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Sale #{self.pk} — ${self.total} ({self.created_at:%b %d, %Y %I:%M %p})'

    def recalculate_total(self):
        total = self.line_items.aggregate(
            total=Sum(F('unit_price') * F('quantity'))
        )['total'] or Decimal('0.00')
        self.total = total
        self.save(update_fields=['total'])


class SaleLineItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='line_items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name='sale_lines', on_delete=models.PROTECT)
    item_name = models.CharField(max_length=100)  # snapshot
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f'{self.quantity} x {self.item_name}'

    def deduct_inventory(self):
        """Deduct this line's required ingredients from stock."""
        for line in self.menu_item.recipe:
            ingredient = line.ingredient
            used = line.quantity_required * self.quantity
            ingredient.quantity_on_hand = max(Decimal('0'), ingredient.quantity_on_hand - used)
            ingredient.save(update_fields=['quantity_on_hand'])
