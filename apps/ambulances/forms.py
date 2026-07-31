from django import forms

from apps.hospitals.models import Hospital

from .models import AmbulanceRequest

_BASE_WIDGET_ATTRS = {'class': 'form-control'}


class AmbulanceRequestForm(forms.ModelForm):
    hospital = forms.ModelChoiceField(
        queryset=Hospital.objects.filter(is_active=True),
        required=False,
        empty_label='Any nearby hospital (recommended for fastest response)',
        widget=forms.Select(attrs=_BASE_WIDGET_ATTRS),
        label='Preferred hospital',
    )

    class Meta:
        model = AmbulanceRequest
        fields = ['hospital', 'patient_name', 'contact_number', 'pickup_address',
                  'pickup_latitude', 'pickup_longitude', 'emergency_description']
        widgets = {
            'patient_name': forms.TextInput(attrs=_BASE_WIDGET_ATTRS),
            'contact_number': forms.TextInput(attrs={**_BASE_WIDGET_ATTRS, 'placeholder': 'e.g. 98XXXXXXXX'}),
            'pickup_address': forms.TextInput(attrs={**_BASE_WIDGET_ATTRS, 'placeholder': 'e.g. Baneshwor, Kathmandu'}),
            'pickup_latitude': forms.HiddenInput(),
            'pickup_longitude': forms.HiddenInput(),
            'emergency_description': forms.Textarea(attrs={**_BASE_WIDGET_ATTRS, 'rows': 3}),
        }