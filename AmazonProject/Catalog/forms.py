from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserRegistrationForm(UserCreationForm):
    # Add the custom phone number field
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter phone number',
            'type': 'tel' # Opens numeric keypad on mobile
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Fields shown in the form
        fields = UserCreationForm.Meta.fields + ('phone_number',)