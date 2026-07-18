from django.contrib import admin
from .models import LocationStop


@admin.register(LocationStop)
class LocationStopAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start_time', 'end_time', 'is_cancelled')
    list_filter = ('is_cancelled', 'date')
    ordering = ['date', 'start_time']
