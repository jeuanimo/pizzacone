from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from menu.models import Category, MenuItem, Ingredient
from sales.models import Sale, SaleLineItem
from core.models import LocationStop
from core.security_utils import RateLimitMixin
from .forms import (
    MenuItemForm, CategoryForm, IngredientForm, RestockForm,
    MenuItemIngredientFormSet, SaleNoteForm, LocationStopForm,
)


def is_staff_user(user):
    return user.is_active and user.is_staff


# OWASP #7: Rate limiting on login to prevent brute force attacks
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def staff_login(request):
    if request.user.is_authenticated and is_staff_user(request.user):
        return redirect('dashboard:home')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if is_staff_user(user):
            login(request, user)
            return redirect('dashboard:home')
        messages.error(request, "That account doesn't have staff access.")
    return render(request, 'dashboard/login.html', {'form': form})


def staff_logout(request):
    logout(request)
    return redirect('core:home')


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def dashboard_home(request):
    today = timezone.localdate()
    today_sales = Sale.objects.filter(created_at__date=today)

    stats = {
        'total_items': MenuItem.objects.count(),
        'available_items': MenuItem.objects.filter(is_available=True).count(),
        'unavailable_items': MenuItem.objects.filter(is_available=False).count(),
        'total_categories': Category.objects.count(),
        'today_sale_count': today_sales.count(),
        'today_revenue': today_sales.aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
    }
    recent_items = MenuItem.objects.select_related('category').order_by('-updated_at')[:5]
    low_stock = Ingredient.objects.filter(quantity_on_hand__lte=F('reorder_threshold')).order_by('quantity_on_hand')
    recent_sales = Sale.objects.order_by('-created_at')[:6]

    return render(request, 'dashboard/home.html', {
        'stats': stats,
        'recent_items': recent_items,
        'low_stock': low_stock,
        'recent_sales': recent_sales,
    })


# ---------------------------------------------------------------- Menu items

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def menu_item_list(request):
    items = MenuItem.objects.select_related('category').all()
    return render(request, 'dashboard/menu_item_list.html', {'items': items})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def menu_item_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Menu item created. You can now add its recipe/ingredients.')
            return redirect('dashboard:menu_item_edit', pk=item.pk)
    else:
        form = MenuItemForm()
    return render(request, 'dashboard/menu_item_form.html', {'form': form, 'title': 'Add Menu Item'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def menu_item_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        formset = MenuItemIngredientFormSet(request.POST, instance=item)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'{item.name} updated.')
            return redirect('dashboard:menu_item_list')
    else:
        form = MenuItemForm(instance=item)
        formset = MenuItemIngredientFormSet(instance=item)
    return render(request, 'dashboard/menu_item_form.html', {
        'form': form, 'formset': formset, 'title': f'Edit {item.name}', 'item': item,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def menu_item_delete(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('dashboard:menu_item_list')
    return render(request, 'dashboard/menu_item_confirm_delete.html', {'item': item})


# ------------------------------------------------------------------ Categories

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'dashboard/category_list.html', {'categories': categories})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('dashboard:category_list')
    else:
        form = CategoryForm()
    return render(request, 'dashboard/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('dashboard:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'dashboard/category_form.html', {'form': form, 'title': f'Edit {category.name}'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('dashboard:category_list')
    return render(request, 'dashboard/category_confirm_delete.html', {'category': category})


# ------------------------------------------------------------------ Inventory

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def inventory_list(request):
    ingredients = Ingredient.objects.all().order_by('quantity_on_hand')
    return render(request, 'dashboard/inventory_list.html', {'ingredients': ingredients})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def ingredient_create(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingredient added.')
            return redirect('dashboard:inventory_list')
    else:
        form = IngredientForm()
    return render(request, 'dashboard/ingredient_form.html', {'form': form, 'title': 'Add Ingredient'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def ingredient_edit(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            messages.success(request, f'{ingredient.name} updated.')
            return redirect('dashboard:inventory_list')
    else:
        form = IngredientForm(instance=ingredient)
    return render(request, 'dashboard/ingredient_form.html', {'form': form, 'title': f'Edit {ingredient.name}'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def ingredient_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        name = ingredient.name
        ingredient.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('dashboard:inventory_list')
    return render(request, 'dashboard/ingredient_confirm_delete.html', {'ingredient': ingredient})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def ingredient_restock(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            ingredient.quantity_on_hand += form.cleaned_data['amount']
            ingredient.save(update_fields=['quantity_on_hand'])
            messages.success(request, f'Added {form.cleaned_data["amount"]} {ingredient.get_unit_display()} to {ingredient.name}.')
    return redirect('dashboard:inventory_list')


# --------------------------------------------------------------------- Sales

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def record_sale(request):
    items = MenuItem.objects.filter(is_available=True).select_related('category')

    if request.method == 'POST':
        note_form = SaleNoteForm(request.POST)
        line_data = []
        for item in items:
            try:
                qty = int(request.POST.get(f'qty_{item.id}', 0) or 0)
            except ValueError:
                qty = 0
            if qty > 0:
                line_data.append((item, qty))

        if not line_data:
            messages.error(request, 'Add at least one item with a quantity before recording the sale.')
        elif note_form.is_valid():
            sale = note_form.save(commit=False)
            sale.recorded_by = request.user
            sale.save()
            for item, qty in line_data:
                line = SaleLineItem.objects.create(
                    sale=sale, menu_item=item, item_name=item.name,
                    unit_price=item.price, quantity=qty,
                )
                line.deduct_inventory()
            sale.recalculate_total()
            messages.success(request, f'Sale #{sale.pk} recorded — ${sale.total}.')
            return redirect('dashboard:record_sale')
    else:
        note_form = SaleNoteForm()

    return render(request, 'dashboard/record_sale.html', {'items': items, 'note_form': note_form})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def sales_history(request):
    sales = Sale.objects.prefetch_related('line_items').all()[:100]
    return render(request, 'dashboard/sales_history.html', {'sales': sales})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def sales_reports(request):
    period = request.GET.get('period', 'today')
    today = timezone.localdate()

    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        label = 'This Week'
    elif period == 'month':
        start_date = today.replace(day=1)
        label = 'This Month'
    elif period == 'all':
        start_date = None
        label = 'All Time'
    else:
        start_date = today
        period = 'today'
        label = 'Today'

    sales = Sale.objects.all()
    if start_date:
        sales = sales.filter(created_at__date__gte=start_date)

    summary = sales.aggregate(total_revenue=Sum('total'), sale_count=Count('id'))
    best_sellers = (
        SaleLineItem.objects.filter(sale__in=sales)
        .values('item_name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum(F('unit_price') * F('quantity')))
        .order_by('-total_qty')[:10]
    )

    return render(request, 'dashboard/sales_reports.html', {
        'period': period,
        'label': label,
        'summary': summary,
        'best_sellers': best_sellers,
    })


# ---------------------------------------------------------------- Schedule

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def schedule_list(request):
    stops = LocationStop.objects.all().order_by('date', 'start_time')
    return render(request, 'dashboard/schedule_list.html', {'stops': stops})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def schedule_create(request):
    if request.method == 'POST':
        form = LocationStopForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stop added to the schedule.')
            return redirect('dashboard:schedule_list')
    else:
        form = LocationStopForm()
    return render(request, 'dashboard/schedule_form.html', {'form': form, 'title': 'Add a Stop'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def schedule_edit(request, pk):
    stop = get_object_or_404(LocationStop, pk=pk)
    if request.method == 'POST':
        form = LocationStopForm(request.POST, request.FILES, instance=stop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stop updated.')
            return redirect('dashboard:schedule_list')
    else:
        form = LocationStopForm(instance=stop)
    return render(request, 'dashboard/schedule_form.html', {'form': form, 'title': f'Edit {stop.name}', 'stop': stop})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
def schedule_delete(request, pk):
    stop = get_object_or_404(LocationStop, pk=pk)
    if request.method == 'POST':
        name = stop.name
        stop.delete()
        messages.success(request, f'Removed "{name}" from the schedule.')
        return redirect('dashboard:schedule_list')
    return render(request, 'dashboard/schedule_confirm_delete.html', {'stop': stop})
