from django.contrib import admin
from .models import Sale, SaleLineItem


class SaleLineItemInline(admin.TabularInline):
    model = SaleLineItem
    extra = 0
    readonly_fields = ('item_name', 'unit_price', 'quantity')
    can_delete = False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'total', 'payment_method', 'recorded_by')
    list_filter = ('payment_method', 'created_at')
    readonly_fields = ('total', 'created_at')
    inlines = [SaleLineItemInline]
