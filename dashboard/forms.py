from django import forms
from django.forms import inlineformset_factory

from menu.models import Category, MenuItem, Ingredient, MenuItemIngredient
from sales.models import Sale
from core.models import LocationStop


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
