from django.shortcuts import render
from django.conf import settings
from django.utils import timezone

from menu.models import MenuItem
from .models import LocationStop


def home(request):
    featured_items = MenuItem.objects.filter(is_available=True).order_by('category__display_order', 'display_order')[:5]
    today = timezone.localdate()
    todays_stop = LocationStop.objects.filter(date=today, is_cancelled=False).first()
    next_stop = None
    if not todays_stop:
        next_stop = LocationStop.objects.filter(date__gt=today, is_cancelled=False).order_by('date', 'start_time').first()
    return render(request, 'core/home.html', {
        'featured_items': featured_items,
        'todays_stop': todays_stop,
        'next_stop': next_stop,
    })


def about(request):
    return render(request, 'core/about.html')


def visit(request):
    today = timezone.localdate()
    todays_stop = LocationStop.objects.filter(date=today, is_cancelled=False).first()
    upcoming_stops = LocationStop.objects.filter(date__gt=today, is_cancelled=False).order_by('date', 'start_time')[:14]
    return render(request, 'core/visit.html', {
        'store_phone': settings.STORE_PHONE,
        'store_hours': settings.STORE_HOURS,
        'todays_stop': todays_stop,
        'upcoming_stops': upcoming_stops,
    })
