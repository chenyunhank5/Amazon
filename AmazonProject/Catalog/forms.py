from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserRegistrationForm(UserCreationForm):
    # Add the custom phone number field
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter phone number',
            'type': 'tel',
            'class': 'form-control' # Useful if you use Bootstrap
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Fields shown in the form: username, password1, password2 + phone_number
        fields = UserCreationForm.Meta.fields + ('phone_number',)

    def save(self, commit=True):
        user = super().save(commit=False)
        # We don't save the phone_number to the User model because it doesn't exist there.
        # We handle the phone_number in the view by accessing form.cleaned_data['phone_number']
        if commit:
            user.save()
        return user