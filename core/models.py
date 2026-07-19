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


class SiteText(models.Model):
    """An editable block of copy shown somewhere on the public site.

    Templates look these up by `key` (see core.context_processors.site_text)
    with a hardcoded fallback, so deleting a block just reverts that spot to
    its original wording rather than leaving a blank gap.
    """

    SECTION_HOME = 'home'
    SECTION_ABOUT = 'about'
    SECTION_VISIT = 'visit'
    SECTION_CONTACT = 'contact'
    SECTION_FOOTER = 'footer'
    SECTION_OTHER = 'other'

    SECTION_CHOICES = [
        (SECTION_HOME, 'Home Page'),
        (SECTION_ABOUT, 'About Page'),
        (SECTION_VISIT, 'Find Us Page'),
        (SECTION_CONTACT, 'Contact Info'),
        (SECTION_FOOTER, 'Footer'),
        (SECTION_OTHER, 'Other'),
    ]

    key = models.SlugField(
        max_length=80, unique=True,
        help_text='Used by the site templates to find this text — changing it breaks the link to its spot on the site.',
    )
    label = models.CharField(max_length=150, help_text='Human-readable name shown here in the dashboard.')
    description = models.CharField(
        max_length=255, blank=True,
        help_text="Plain-English note on exactly where this shows up on the site, so it's easy to tell blocks apart.",
    )
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default=SECTION_OTHER)
    content = models.TextField(blank=True, help_text='Plain text — line breaks are preserved, no HTML needed.')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', 'label']
        verbose_name = 'Site Text'
        verbose_name_plural = 'Site Text'

    def __str__(self):
        return self.label


class ContactMessage(models.Model):
    """A message sent through the public Contact page — general inquiry,
    review/comment, or a lightweight venue-stop request. (Full venue-booking
    logistics still go through VenueRequest on the Find Us page.)
    """

    REASON_GENERAL = 'general'
    REASON_REVIEW = 'review'
    REASON_VENUE = 'venue'

    REASON_CHOICES = [
        (REASON_GENERAL, 'General Inquiry'),
        (REASON_REVIEW, 'Review / Comment'),
        (REASON_VENUE, 'Request a Venue Stop'),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default=REASON_GENERAL)
    rating = models.PositiveSmallIntegerField(
        blank=True, null=True,
        help_text='1–5 stars — only used for reviews.',
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_reason_display()} from {self.name} ({self.created_at:%Y-%m-%d})'


class VenueRequest(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_REVIEW = 'in_review'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_DECLINED = 'declined'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_IN_REVIEW, 'In Review'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_DECLINED, 'Declined'),
    ]

    organization_name = models.CharField(max_length=150)
    contact_name = models.CharField(max_length=120)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=40, blank=True)
    requested_date = models.DateField()
    requested_start_time = models.TimeField(blank=True, null=True)
    requested_end_time = models.TimeField(blank=True, null=True)
    venue_name = models.CharField(max_length=150)
    venue_address = models.CharField(max_length=255)
    estimated_attendance = models.PositiveIntegerField(blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['requested_date', '-created_at']

    def __str__(self):
        return f'{self.organization_name} - {self.requested_date}'
