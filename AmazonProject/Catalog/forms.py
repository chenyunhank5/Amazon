from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import Profile

class CleanLoginForm(AuthenticationForm):
    """Custom Login Form for Username/Phone authentication"""
    username = forms.CharField(
        label="Enter Username or Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': 'Username or Phone...',
            'class': 'form-control'
        })
    )

    error_messages = {
        'invalid_login': _("Oops! Incorrect details. Check your username and password."),
    }

class UserRegistrationForm(forms.ModelForm):
    """Custom Registration Form with Phone and Withdrawal PIN"""
    phone_number = forms.CharField(
        label="Enter Phone Number",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. +123456789', 'type': 'tel'})
    )
    password = forms.CharField(
        label="Enter Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Min 8 characters'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'})
    )
    withdrawal_pin = forms.CharField(
        label="Create 6-Digit Withdrawal PIN",
        min_length=6, 
        max_length=6, 
        widget=forms.PasswordInput(attrs={
            'inputmode': 'numeric',
            'placeholder': '••••••'
        })
    )

    class Meta:
        model = User
        fields = ['username']

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.order_fields([
            'username', 
            'phone_number', 
            'password', 
            'confirm_password', 
            'withdrawal_pin'
        ])

    def clean_phone_number(self):
        """Prevents the UNIQUE constraint IntegrityError"""
        phone = self.cleaned_data.get('phone_number')
        if Profile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean_withdrawal_pin(self):
        """Ensure the PIN is strictly numeric"""
        pin = self.cleaned_data.get('withdrawal_pin')
        if pin and not pin.isdigit():
            raise forms.ValidationError("PIN must contain only numbers.")
        return pin

    def clean(self):
        """Cross-field validation for password matching"""
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")

        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match!")
        
        return cleaned_data