from django.shortcuts import render, get_object_or_404
from .models import Category, MenuItem


def menu_list(request):
    """Full menu, grouped by category."""
    categories = Category.objects.prefetch_related('items').all()
    # Only show categories that actually have an available item, but keep
    # ordering/grouping intact.
    categories = [c for c in categories if c.items.filter(is_available=True).exists()]
    return render(request, 'menu/menu_list.html', {
        'categories': categories,
    })


def item_detail(request, slug):
    item = get_object_or_404(MenuItem, slug=slug, is_available=True)
    related_items = MenuItem.objects.filter(
        category=item.category, is_available=True
    ).exclude(pk=item.pk)[:3]
    return render(request, 'menu/item_detail.html', {
        'item': item,
        'related_items': related_items,
    })
