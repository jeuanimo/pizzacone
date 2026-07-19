import logging

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.utils import timezone

from menu.models import MenuItem
from .models import LocationStop
from .forms import VenueRequestForm, ContactMessageForm

logger = logging.getLogger('django')


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


def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            _notify_staff_of_contact_message(contact_message)
            messages.success(
                request,
                "Thanks for reaching out — we'll get back to you soon. "
                "Planning an event? Head to our Find Us page for full venue booking details."
                if contact_message.reason == contact_message.REASON_VENUE
                else "Thanks for reaching out — we'll get back to you soon.",
            )
            return redirect('core:contact')
    else:
        form = ContactMessageForm()
    return render(request, 'core/contact.html', {
        'form': form,
        'store_phone': settings.STORE_PHONE,
    })


def _notify_staff_of_contact_message(contact_message):
    """Best-effort email notification — a failed send should never block the
    submission, since the message is already safely stored in the database.
    """
    recipient = settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL
    if not recipient:
        return
    body = (
        f'From: {contact_message.name} <{contact_message.email}>\n'
        f'Phone: {contact_message.phone or "—"}\n'
        f'Reason: {contact_message.get_reason_display()}\n'
        + (f'Rating: {contact_message.rating} star(s)\n' if contact_message.rating else '')
        + f'\n{contact_message.message}\n'
        + '\n---\nView and manage this in the staff dashboard under Contact Messages.'
    )
    try:
        email = EmailMessage(
            subject=f'[Pizza Cone Website] {contact_message.get_reason_display()} from {contact_message.name}',
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
            reply_to=[contact_message.email],
        )
        email.send(fail_silently=False)
    except Exception:
        logger.exception('Failed to send contact message notification email.')


def visit(request):
    today = timezone.localdate()
    todays_stop = LocationStop.objects.filter(date=today, is_cancelled=False).first()
    upcoming_stops = LocationStop.objects.filter(date__gt=today, is_cancelled=False).order_by('date', 'start_time')[:14]

    if request.method == 'POST':
        venue_request_form = VenueRequestForm(request.POST)
        if venue_request_form.is_valid():
            venue_request_form.save()
            messages.success(request, 'Thanks for reaching out. Your venue request was sent to our staff team.')
            return redirect('core:visit')
    else:
        venue_request_form = VenueRequestForm()

    return render(request, 'core/visit.html', {
        'store_phone': settings.STORE_PHONE,
        'store_hours': settings.STORE_HOURS,
        'todays_stop': todays_stop,
        'upcoming_stops': upcoming_stops,
        'venue_request_form': venue_request_form,
    })
