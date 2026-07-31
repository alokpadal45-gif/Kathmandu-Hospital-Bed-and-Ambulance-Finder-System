from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User, UserRole

_BASE_WIDGET_ATTRS = {'class': 'form-control'}


class CitizenSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=_BASE_WIDGET_ATTRS))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=_BASE_WIDGET_ATTRS))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=_BASE_WIDGET_ATTRS))
    phone_number = forms.CharField(
        max_length=15, required=True,
        widget=forms.TextInput(attrs={**_BASE_WIDGET_ATTRS, 'placeholder': 'e.g. 98XXXXXXXX'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(_BASE_WIDGET_ATTRS)
        self.fields['password1'].widget.attrs.update(_BASE_WIDGET_ATTRS)
        self.fields['password2'].widget.attrs.update(_BASE_WIDGET_ATTRS)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRole.CITIZEN
        user.is_verified = True
        if commit:
            user.save()
        return user


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(_BASE_WIDGET_ATTRS)
        self.fields['password'].widget.attrs.update(_BASE_WIDGET_ATTRS)


class AdminCreateHospitalStaffForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=_BASE_WIDGET_ATTRS))
    password = forms.CharField(widget=forms.PasswordInput(attrs=_BASE_WIDGET_ATTRS))
    hospital = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs=_BASE_WIDGET_ATTRS))
    position = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={**_BASE_WIDGET_ATTRS, 'placeholder': 'e.g. Bed Manager (optional)'}),
    )

    def __init__(self, *args, **kwargs):
        from apps.hospitals.models import Hospital
        super().__init__(*args, **kwargs)
        self.fields['hospital'].queryset = Hospital.objects.filter(is_active=True)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean_password(self):
        password = self.cleaned_data['password']
        password_validation.validate_password(password)
        return password