from django.contrib import admin
from .models import LocationStop, VenueRequest


@admin.register(LocationStop)
class LocationStopAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start_time', 'end_time', 'is_cancelled')
    list_filter = ('is_cancelled', 'date')
    ordering = ['date', 'start_time']


@admin.register(VenueRequest)
class VenueRequestAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'requested_date', 'venue_name', 'contact_name', 'status', 'created_at')
    list_filter = ('status', 'requested_date')
    search_fields = ('organization_name', 'contact_name', 'contact_email', 'venue_name')
    ordering = ['requested_date', '-created_at']
