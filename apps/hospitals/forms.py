from django import forms

from .models import Ambulance, Hospital

_BASE_WIDGET_ATTRS = {'class': 'form-control form-control-sm'}


class HospitalAvailabilityForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['total_beds', 'available_beds', 'total_icu_beds', 'available_icu_beds']
        widgets = {
            'total_beds': forms.NumberInput(attrs={**_BASE_WIDGET_ATTRS, 'min': 0}),
            'available_beds': forms.NumberInput(attrs={**_BASE_WIDGET_ATTRS, 'min': 0}),
            'total_icu_beds': forms.NumberInput(attrs={**_BASE_WIDGET_ATTRS, 'min': 0}),
            'available_icu_beds': forms.NumberInput(attrs={**_BASE_WIDGET_ATTRS, 'min': 0}),
        }

    def clean(self):
        cleaned = super().clean()
        total_beds = cleaned.get('total_beds')
        available_beds = cleaned.get('available_beds')
        total_icu = cleaned.get('total_icu_beds')
        available_icu = cleaned.get('available_icu_beds')

        if total_beds is not None and available_beds is not None and available_beds > total_beds:
            self.add_error('available_beds', 'Available beds cannot exceed total beds.')
        if total_icu is not None and available_icu is not None and available_icu > total_icu:
            self.add_error('available_icu_beds', 'Available ICU beds cannot exceed total ICU beds.')

        return cleaned


class AmbulanceForm(forms.ModelForm):
    class Meta:
        model = Ambulance
        fields = ['vehicle_number', 'driver_name', 'driver_phone', 'status']
        widgets = {
            'vehicle_number': forms.TextInput(attrs={**_BASE_WIDGET_ATTRS, 'placeholder': 'e.g. Ba 1 Kha 1234'}),
            'driver_name': forms.TextInput(attrs=_BASE_WIDGET_ATTRS),
            'driver_phone': forms.TextInput(attrs=_BASE_WIDGET_ATTRS),
            'status': forms.Select(attrs=_BASE_WIDGET_ATTRS),
        }