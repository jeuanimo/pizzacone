from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.forms import inlineformset_factory

from menu.models import Category, MenuItem, Ingredient, MenuItemIngredient
from sales.models import Sale
from core.models import LocationStop, VenueRequest

User = get_user_model()


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'category', 'name', 'description', 'price', 'image',
            'is_available', 'is_featured', 'calories', 'display_order',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'calories': forms.NumberInput(attrs={'class': 'form-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.TextInput(attrs={'class': 'form-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'unit', 'quantity_on_hand', 'reorder_threshold', 'cost_per_unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'unit': forms.Select(attrs={'class': 'form-input'}),
            'quantity_on_hand': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'reorder_threshold': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'cost_per_unit': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }


class RestockForm(forms.Form):
    amount = forms.DecimalField(
        min_value=0, decimal_places=2, max_digits=10,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Amount to add'}),
    )


MenuItemIngredientFormSet = inlineformset_factory(
    MenuItem,
    MenuItemIngredient,
    fields=['ingredient', 'quantity_required'],
    extra=1,
    can_delete=True,
    widgets={
        'ingredient': forms.Select(attrs={'class': 'form-input'}),
        'quantity_required': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
    },
)


class SaleNoteForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'note']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-input'}),
            'note': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional note'}),
        }


class LocationStopForm(forms.ModelForm):
    class Meta:
        model = LocationStop
        fields = [
            'date', 'start_time', 'end_time', 'name', 'address',
            'latitude', 'longitude', 'image', 'notes', 'map_url', 'is_cancelled',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Downtown Farmers Market'}),
            'address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street address (optional)'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input', 'step': 'any', 'placeholder': 'e.g. 39.781721'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input', 'step': 'any', 'placeholder': 'e.g. -89.650148'}),
            'notes': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Look for the red tent!'}),
            'map_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://maps.google.com/...'}),
        }


class StaffCreateForm(forms.ModelForm):
    """Used by superusers to create a new staff login from the dashboard
    (replaces the need to use `manage.py createsuperuser` or Django admin)."""

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }
        labels = {'is_superuser': 'Grant full admin (superuser) access — can manage other staff accounts'}

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords don't match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # always staff, so they can log into the dashboard
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class StaffEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active', 'is_superuser']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'is_active': 'Active (unchecked disables this login)',
            'is_superuser': 'Grant full admin (superuser) access — can manage other staff accounts',
        }


class StaffSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})


class SaleEditForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['payment_method', 'note']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-input'}),
            'note': forms.TextInput(attrs={'class': 'form-input'}),
        }


class VenueRequestUpdateForm(forms.ModelForm):
    class Meta:
        model = VenueRequest
        fields = ['status', 'staff_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
            'staff_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Internal notes for staff only'}),
        }


class GmailComposeForm(forms.Form):
    to_email = forms.EmailField(
        label='To',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'recipient@example.com'}),
    )
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Subject'}),
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 10, 'placeholder': 'Write your message...'}),
    )
