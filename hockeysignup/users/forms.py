from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from .models import CustomUser


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)
    username = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'password1', 'password2']


class CustomLoginForm(AuthenticationForm):
    username = UsernameField(
        label='Email/Username',
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control form-control-lg'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control form-control-lg'})
    )
