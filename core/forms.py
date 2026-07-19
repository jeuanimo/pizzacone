from django import forms

from .models import VenueRequest


class VenueRequestForm(forms.ModelForm):
    class Meta:
        model = VenueRequest
        fields = [
            'organization_name',
            'contact_name',
            'contact_email',
            'contact_phone',
            'requested_date',
            'requested_start_time',
            'requested_end_time',
            'venue_name',
            'venue_address',
            'estimated_attendance',
            'message',
        ]
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Organization or event host'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your full name'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(555) 555-5555'}),
            'requested_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'requested_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'requested_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Venue name'}),
            'venue_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street, city, state'}),
            'estimated_attendance': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Approximate guest count'}),
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Tell us about your event and what you need.'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('requested_start_time')
        end_time = cleaned_data.get('requested_end_time')
        if start_time and end_time and end_time <= start_time:
            self.add_error('requested_end_time', 'End time must be after the start time.')
        return cleaned_data
