from django.db import models
from django.utils import timezone


class LocationStop(models.Model):
    """A scheduled stop for a mobile/rotating pizza cone location."""

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    name = models.CharField(max_length=150, help_text='e.g. "Downtown Farmers Market" or "Oak St. & 5th Ave"')
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text='Optional — pinpoints the spot on the map (e.g. 39.781721).',
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text='Optional — pinpoints the spot on the map (e.g. -89.650148).',
    )
    image = models.ImageField(
        upload_to='location_stops/', blank=True, null=True,
        help_text='Optional photo for this stop — event flyer, venue photo, the truck at that spot, etc.',
    )
    notes = models.CharField(max_length=255, blank=True, help_text='Optional extra info, e.g. "Look for the red tent!"')
    map_url = models.URLField(blank=True, help_text='Optional link to Google Maps or similar (used if no lat/long is set).')
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f'{self.name} — {self.date} {self.start_time.strftime("%I:%M %p")}'

    @property
    def is_today(self):
        return self.date == timezone.localdate()

    @property
    def is_past(self):
        return self.date < timezone.localdate()

    @property
    def has_map_pin(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def directions_url(self):
        """Best available link to get directions to this stop."""
        if self.has_map_pin:
            return f'https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}'
        if self.map_url:
            return self.map_url
        if self.address:
            from urllib.parse import quote
            return f'https://www.google.com/maps/search/?api=1&query={quote(self.address)}'
        return ''

    @property
    def map_embed_url(self):
        if self.has_map_pin:
            return f'https://www.google.com/maps?q={self.latitude},{self.longitude}&output=embed'
        if self.address:
            from urllib.parse import quote
            return f'https://www.google.com/maps?q={quote(self.address)}&output=embed'
        return ''
