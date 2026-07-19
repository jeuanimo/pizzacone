import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from html import escape

from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    # Fallback if django_ratelimit is not installed
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from menu.models import Category, MenuItem, Ingredient
from menu.csv_import import import_menu_items_csv
from sales.models import Sale, SaleLineItem
from core.models import LocationStop, VenueRequest, SiteText, ContactMessage
from .forms import (
    MenuItemForm, CategoryForm, IngredientForm, RestockForm,
    MenuItemIngredientFormSet, SaleNoteForm, LocationStopForm,
    StaffCreateForm, StaffEditForm, StaffSetPasswordForm, SaleEditForm,
    VenueRequestUpdateForm, GmailComposeForm, MenuItemCSVImportForm,
    SiteTextForm, ContactMessageUpdateForm,
)
from .gmail_client import GmailClient

User = get_user_model()

# URL name constants to avoid duplication
CATEGORY_LIST_URL = 'dashboard:category_list'
INVENTORY_LIST_URL = 'dashboard:inventory_list'
SCHEDULE_LIST_URL = 'dashboard:schedule_list'
SALES_HISTORY_URL = 'dashboard:sales_history'
STAFF_USER_LIST_URL = 'dashboard:staff_user_list'
VENUE_REQUEST_LIST_URL = 'dashboard:venue_request_list'
MAILBOX_INBOX_URL = 'dashboard:mailbox_inbox'


def is_staff_user(user):
    return user.is_active and user.is_staff


def is_superuser(user):
    return user.is_active and user.is_superuser


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


@require_http_methods(["GET", "POST"])
def staff_logout(request):
    logout(request)
    return redirect('core:home')


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
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
        'new_venue_requests': VenueRequest.objects.filter(status=VenueRequest.STATUS_NEW).count(),
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


def _parse_calendar_month(month_value, today):
    if month_value:
        try:
            parsed = datetime.strptime(month_value, '%Y-%m').date()
            return date(parsed.year, parsed.month, 1)
        except ValueError:
            pass
    return date(today.year, today.month, 1)


def _build_calendar_weeks(month_start, stops, venue_requests):
    month_calendar = calendar.Calendar(firstweekday=6)
    weeks = month_calendar.monthdatescalendar(month_start.year, month_start.month)

    stops_by_day = {}
    for stop in stops:
        stops_by_day.setdefault(stop.date, []).append(stop)

    requests_by_day = {}
    for venue_request in venue_requests:
        requests_by_day.setdefault(venue_request.requested_date, []).append(venue_request)

    week_rows = []
    for week in weeks:
        week_rows.append([
            {
                'date': day,
                'in_month': day.month == month_start.month,
                'stops': stops_by_day.get(day, []),
                'venue_requests': requests_by_day.get(day, []),
            }
            for day in week
        ])
    return week_rows


# ---------------------------------------------------------------- Menu items

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def menu_item_list(request):
    items = MenuItem.objects.select_related('category').all()
    return render(request, 'dashboard/menu_item_list.html', {'items': items})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
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
@require_http_methods(["GET", "POST"])
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
@require_http_methods(["GET", "POST"])
def menu_item_import(request):
    if request.method == 'POST':
        form = MenuItemCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            result = import_menu_items_csv(
                form.cleaned_data['csv_file'],
                overwrite_images=form.cleaned_data['overwrite_images'],
            )
            if result.created or result.updated:
                messages.success(
                    request,
                    f'Imported: {result.created} created, {result.updated} updated, '
                    f'{result.images_attached} image(s) attached.',
                )
            for error in result.errors:
                messages.error(request, error)
            if result.ok:
                return redirect('dashboard:menu_item_list')
    else:
        form = MenuItemCSVImportForm()
    return render(request, 'dashboard/menu_item_import.html', {'form': form})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def menu_item_delete(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('dashboard:menu_item_list')
    return render(request, 'dashboard/menu_item_confirm_delete.html', {'item': item})


# ------------------------------------------------------------------ Site Text

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def site_text_list(request):
    blocks = SiteText.objects.all()
    return render(request, 'dashboard/site_text_list.html', {'blocks': blocks})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def site_text_create(request):
    if request.method == 'POST':
        form = SiteTextForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site text block created.')
            return redirect('dashboard:site_text_list')
    else:
        form = SiteTextForm()
    return render(request, 'dashboard/site_text_form.html', {'form': form, 'title': 'Add Site Text Block'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def site_text_edit(request, pk):
    block = get_object_or_404(SiteText, pk=pk)
    if request.method == 'POST':
        form = SiteTextForm(request.POST, instance=block)
        form.fields['key'].disabled = True
        if form.is_valid():
            form.save()
            messages.success(request, f'"{block.label}" updated.')
            return redirect('dashboard:site_text_list')
    else:
        form = SiteTextForm(instance=block)
        form.fields['key'].disabled = True
    return render(request, 'dashboard/site_text_form.html', {
        'form': form, 'title': f'Edit "{block.label}"', 'block': block,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def site_text_delete(request, pk):
    block = get_object_or_404(SiteText, pk=pk)
    if request.method == 'POST':
        label = block.label
        block.delete()
        messages.success(request, f'"{label}" deleted — that spot on the site will show its default wording again.')
        return redirect('dashboard:site_text_list')
    return render(request, 'dashboard/site_text_confirm_delete.html', {'block': block})


# ------------------------------------------------------------------ Categories

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'dashboard/category_list.html', {'categories': categories})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect(CATEGORY_LIST_URL)
    else:
        form = CategoryForm()
    return render(request, 'dashboard/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect(CATEGORY_LIST_URL)
    else:
        form = CategoryForm(instance=category)
    return render(request, 'dashboard/category_form.html', {'form': form, 'title': f'Edit {category.name}'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'{name} deleted.')
        return redirect(CATEGORY_LIST_URL)
    return render(request, 'dashboard/category_confirm_delete.html', {'category': category})


# ------------------------------------------------------------------ Inventory

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def inventory_list(request):
    ingredients = Ingredient.objects.all().order_by('quantity_on_hand')
    return render(request, 'dashboard/inventory_list.html', {'ingredients': ingredients})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def ingredient_create(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ingredient added.')
            return redirect(INVENTORY_LIST_URL)
    else:
        form = IngredientForm()
    return render(request, 'dashboard/ingredient_form.html', {'form': form, 'title': 'Add Ingredient'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def ingredient_edit(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            messages.success(request, f'{ingredient.name} updated.')
            return redirect(INVENTORY_LIST_URL)
    else:
        form = IngredientForm(instance=ingredient)
    return render(request, 'dashboard/ingredient_form.html', {'form': form, 'title': f'Edit {ingredient.name}'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def ingredient_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        name = ingredient.name
        ingredient.delete()
        messages.success(request, f'{name} deleted.')
        return redirect(INVENTORY_LIST_URL)
    return render(request, 'dashboard/ingredient_confirm_delete.html', {'ingredient': ingredient})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["POST"])
def ingredient_restock(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            ingredient.quantity_on_hand += form.cleaned_data['amount']
            ingredient.save(update_fields=['quantity_on_hand'])
            messages.success(request, f'Added {form.cleaned_data["amount"]} {ingredient.get_unit_display()} to {ingredient.name}.')
    return redirect(INVENTORY_LIST_URL)


# --------------------------------------------------------------------- Sales

def _collect_sale_line_data(request, items):
    line_data = []
    for item in items:
        raw_qty = request.POST.get(f'qty_{item.id}', 0) or 0
        try:
            qty = int(raw_qty)
        except (TypeError, ValueError):
            qty = 0
        if qty > 0:
            line_data.append((item, qty))
    return line_data


def _create_sale_with_lines(note_form, user, line_data):
    sale = note_form.save(commit=False)
    sale.recorded_by = user
    sale.save()

    for item, qty in line_data:
        line = SaleLineItem.objects.create(
            sale=sale,
            menu_item=item,
            item_name=item.name,
            unit_price=item.price,
            quantity=qty,
        )
        line.deduct_inventory()

    sale.recalculate_total()
    return sale

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def record_sale(request):
    items = MenuItem.objects.filter(is_available=True).select_related('category')

    if request.method == 'POST':
        note_form = SaleNoteForm(request.POST)
        line_data = _collect_sale_line_data(request, items)

        if not line_data:
            messages.error(request, 'Add at least one item with a quantity before recording the sale.')
        elif note_form.is_valid():
            sale = _create_sale_with_lines(note_form, request.user, line_data)
            messages.success(request, f'Sale #{sale.pk} recorded — ${sale.total}.')
            return redirect('dashboard:record_sale')
    else:
        note_form = SaleNoteForm()

    return render(request, 'dashboard/record_sale.html', {'items': items, 'note_form': note_form})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def sales_history(request):
    sales = Sale.objects.prefetch_related('line_items').all()[:100]
    return render(request, 'dashboard/sales_history.html', {'sales': sales})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
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
@require_http_methods(["GET"])
def schedule_list(request):
    stops = LocationStop.objects.all().order_by('date', 'start_time')
    return render(request, 'dashboard/schedule_list.html', {'stops': stops})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def venue_request_list(request):
    status_filter = request.GET.get('status', '').strip()
    venue_requests = VenueRequest.objects.all()
    if status_filter:
        venue_requests = venue_requests.filter(status=status_filter)

    return render(request, 'dashboard/venue_request_list.html', {
        'venue_requests': venue_requests,
        'status_filter': status_filter,
        'status_choices': VenueRequest.STATUS_CHOICES,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def venue_request_edit(request, pk):
    venue_request = get_object_or_404(VenueRequest, pk=pk)
    if request.method == 'POST':
        form = VenueRequestUpdateForm(request.POST, instance=venue_request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venue request updated.')
            return redirect(VENUE_REQUEST_LIST_URL)
    else:
        form = VenueRequestUpdateForm(instance=venue_request)

    return render(request, 'dashboard/venue_request_form.html', {
        'form': form,
        'venue_request': venue_request,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def venue_calendar(request):
    today = timezone.localdate()
    month_start = _parse_calendar_month(request.GET.get('month'), today)
    month_calendar = calendar.Calendar(firstweekday=6)
    weeks = month_calendar.monthdatescalendar(month_start.year, month_start.month)
    start_day = weeks[0][0]
    end_day = weeks[-1][-1]

    stops = LocationStop.objects.filter(date__gte=start_day, date__lte=end_day, is_cancelled=False).order_by('date', 'start_time')
    venue_requests = VenueRequest.objects.filter(requested_date__gte=start_day, requested_date__lte=end_day).order_by('requested_date')

    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)

    return render(request, 'dashboard/venue_calendar.html', {
        'month_start': month_start,
        'week_rows': _build_calendar_weeks(month_start, stops, venue_requests),
        'prev_month': prev_month,
        'next_month': next_month,
        'today': today,
    })


# ------------------------------------------------------------ Contact Messages

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def contact_message_list(request):
    reason_filter = request.GET.get('reason', '').strip()
    contact_messages = ContactMessage.objects.all()
    if reason_filter:
        contact_messages = contact_messages.filter(reason=reason_filter)

    return render(request, 'dashboard/contact_message_list.html', {
        'contact_messages': contact_messages,
        'reason_filter': reason_filter,
        'reason_choices': ContactMessage.REASON_CHOICES,
        'unread_count': ContactMessage.objects.filter(is_read=False).count(),
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def contact_message_detail(request, pk):
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        form = ContactMessageUpdateForm(request.POST, instance=contact_message)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact message updated.')
            return redirect('dashboard:contact_message_list')
    else:
        if not contact_message.is_read:
            contact_message.is_read = True
            contact_message.save(update_fields=['is_read'])
        form = ContactMessageUpdateForm(instance=contact_message)

    return render(request, 'dashboard/contact_message_detail.html', {
        'form': form,
        'contact_message': contact_message,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def contact_message_delete(request, pk):
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        contact_message.delete()
        messages.success(request, 'Contact message deleted.')
        return redirect('dashboard:contact_message_list')
    return render(request, 'dashboard/contact_message_confirm_delete.html', {'contact_message': contact_message})


def _quote_body_for_reply(original_message):
    original_lines = (original_message.get('body') or '').splitlines()
    if not original_lines:
        return ''
    quoted = '\n'.join(f'> {line}' for line in original_lines)
    return f"\n\n----- Original message -----\n{quoted}"


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def mailbox_inbox(request):
    inbox_messages = []
    mailbox_error = ''
    try:
        inbox_messages = GmailClient().list_inbox_messages(limit=20)
    except Exception as exc:  # noqa: BLE001
        mailbox_error = str(exc)

    return render(request, 'dashboard/mailbox_inbox.html', {
        'inbox_messages': inbox_messages,
        'mailbox_error': mailbox_error,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET"])
def mailbox_message_detail(request, uid):
    try:
        message_data = GmailClient().read_message(uid)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f'Unable to load email: {exc}')
        return redirect(MAILBOX_INBOX_URL)

    return render(request, 'dashboard/mailbox_detail.html', {
        'message_data': message_data,
        'escaped_body': escape(message_data.get('body', '')),
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def mailbox_compose(request):
    if request.method == 'POST':
        form = GmailComposeForm(request.POST)
        if form.is_valid():
            try:
                GmailClient().send_message(
                    to_email=form.cleaned_data['to_email'],
                    subject=form.cleaned_data['subject'],
                    body=form.cleaned_data['body'],
                )
                messages.success(request, 'Email sent successfully.')
                return redirect(MAILBOX_INBOX_URL)
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f'Email could not be sent: {exc}')
    else:
        form = GmailComposeForm(
            initial={
                'to_email': request.GET.get('to', ''),
                'subject': request.GET.get('subject', ''),
                'body': request.GET.get('body', ''),
            }
        )

    return render(request, 'dashboard/mailbox_compose.html', {'form': form})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def mailbox_reply(request, uid):
    try:
        original_message = GmailClient().read_message(uid)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f'Unable to load email for reply: {exc}')
        return redirect(MAILBOX_INBOX_URL)

    default_subject = original_message.get('subject') or '(No subject)'
    if not default_subject.lower().startswith('re:'):
        default_subject = f'Re: {default_subject}'

    if request.method == 'POST':
        form = GmailComposeForm(request.POST)
        if form.is_valid():
            try:
                GmailClient().send_message(
                    to_email=form.cleaned_data['to_email'],
                    subject=form.cleaned_data['subject'],
                    body=form.cleaned_data['body'],
                    in_reply_to=original_message.get('message_id') or None,
                    references=original_message.get('message_id') or None,
                )
                messages.success(request, 'Reply sent successfully.')
                return redirect('dashboard:mailbox_message_detail', uid=uid)
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f'Reply could not be sent: {exc}')
    else:
        form = GmailComposeForm(
            initial={
                'to_email': original_message.get('from_email', ''),
                'subject': default_subject,
                'body': _quote_body_for_reply(original_message),
            }
        )

    return render(request, 'dashboard/mailbox_compose.html', {
        'form': form,
        'is_reply': True,
        'reply_uid': uid,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["POST"])
def mailbox_delete(request, uid):
    try:
        GmailClient().delete_message(uid)
        messages.success(request, 'Email deleted.')
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f'Email could not be deleted: {exc}')
    return redirect(MAILBOX_INBOX_URL)


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def schedule_create(request):
    if request.method == 'POST':
        form = LocationStopForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stop added to the schedule.')
            return redirect(SCHEDULE_LIST_URL)
    else:
        form = LocationStopForm()
    return render(request, 'dashboard/schedule_form.html', {'form': form, 'title': 'Add a Stop'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def schedule_edit(request, pk):
    stop = get_object_or_404(LocationStop, pk=pk)
    if request.method == 'POST':
        form = LocationStopForm(request.POST, request.FILES, instance=stop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stop updated.')
            return redirect(SCHEDULE_LIST_URL)
    else:
        form = LocationStopForm(instance=stop)
    return render(request, 'dashboard/schedule_form.html', {'form': form, 'title': f'Edit {stop.name}', 'stop': stop})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def schedule_delete(request, pk):
    stop = get_object_or_404(LocationStop, pk=pk)
    if request.method == 'POST':
        name = stop.name
        stop.delete()
        messages.success(request, f'Removed "{name}" from the schedule.')
        return redirect(SCHEDULE_LIST_URL)
    return render(request, 'dashboard/schedule_confirm_delete.html', {'stop': stop})


# ------------------------------------------------------------ Sale editing

@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleEditForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sale #{sale.pk} updated.')
            return redirect(SALES_HISTORY_URL)
    else:
        form = SaleEditForm(instance=sale)
    return render(request, 'dashboard/sale_detail.html', {'sale': sale, 'form': form})


@login_required(login_url='dashboard:login')
@user_passes_test(is_staff_user, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def sale_void(request, pk):
    """Delete a sale and restore the ingredients it used back to inventory."""
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        for line in sale.line_items.all():
            for recipe_line in line.menu_item.recipe:
                ingredient = recipe_line.ingredient
                restored = recipe_line.quantity_required * line.quantity
                ingredient.quantity_on_hand += restored
                ingredient.save(update_fields=['quantity_on_hand'])
        sale_id = sale.pk
        sale.delete()
        messages.success(request, f'Sale #{sale_id} voided and inventory restored.')
        return redirect(SALES_HISTORY_URL)
    return render(request, 'dashboard/sale_confirm_void.html', {'sale': sale})


# ------------------------------------------------------------- Staff accounts
# Superuser-only: fully replaces the need for Django admin's user management.

@login_required(login_url='dashboard:login')
@user_passes_test(is_superuser, login_url='dashboard:login')
@require_http_methods(["GET"])
def staff_user_list(request):
    staff_users = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'dashboard/staff_user_list.html', {'staff_users': staff_users})


@login_required(login_url='dashboard:login')
@user_passes_test(is_superuser, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def staff_user_create(request):
    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Staff account "{user.username}" created.')
            return redirect(STAFF_USER_LIST_URL)
    else:
        form = StaffCreateForm()
    return render(request, 'dashboard/staff_user_form.html', {'form': form, 'title': 'Add Staff Account'})


@login_required(login_url='dashboard:login')
@user_passes_test(is_superuser, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def staff_user_edit(request, pk):
    staff_member = get_object_or_404(User, pk=pk, is_staff=True)
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Updated "{staff_member.username}".')
            return redirect(STAFF_USER_LIST_URL)
    else:
        form = StaffEditForm(instance=staff_member)
    return render(request, 'dashboard/staff_user_form.html', {
        'form': form, 'title': f'Edit {staff_member.username}', 'staff_member': staff_member,
    })


@login_required(login_url='dashboard:login')
@user_passes_test(is_superuser, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def staff_user_set_password(request, pk):
    staff_member = get_object_or_404(User, pk=pk, is_staff=True)
    if request.method == 'POST':
        form = StaffSetPasswordForm(staff_member, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password updated for "{staff_member.username}".')
            return redirect(STAFF_USER_LIST_URL)
    else:
        form = StaffSetPasswordForm(staff_member)
    return render(request, 'dashboard/staff_user_password_form.html', {'form': form, 'staff_member': staff_member})


@login_required(login_url='dashboard:login')
@user_passes_test(is_superuser, login_url='dashboard:login')
@require_http_methods(["GET", "POST"])
def staff_user_delete(request, pk):
    staff_member = get_object_or_404(User, pk=pk, is_staff=True)
    if staff_member == request.user:
        messages.error(request, "You can't delete your own account while logged in as it.")
        return redirect(STAFF_USER_LIST_URL)
    if request.method == 'POST':
        username = staff_member.username
        staff_member.delete()
        messages.success(request, f'Deleted staff account "{username}".')
        return redirect(STAFF_USER_LIST_URL)
    return render(request, 'dashboard/staff_user_confirm_delete.html', {'staff_member': staff_member})
