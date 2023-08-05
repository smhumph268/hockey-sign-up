from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.forms import ModelForm
from .models import CustomUser, SKILL_LEVEL_CHOICES, PREFERRED_POSITION


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.widgets.EmailInput(attrs={'class': 'form-control form-control-lg'})
    )
    username = forms.CharField(
        max_length=30,
        widget=forms.widgets.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.widgets.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.widgets.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    skill_level = forms.Select(
        choices=SKILL_LEVEL_CHOICES
    )
    preferred_position = forms.Select(
        choices=PREFERRED_POSITION
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control form-control-lg'}),
        help_text=password_validation.password_validators_help_text_html()
    )
    password2 = forms.CharField(
        label="Password confirmation",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control form-control-lg'}),
        help_text="Enter the same password as before, for verification."
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'skill_level', 'preferred_position', 'password1', 'password2']


class CustomLoginForm(AuthenticationForm):
    username = UsernameField(
        label='Email/Username',
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control form-control-lg'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control form-control-lg'})
    )


class UserDetailsForm(ModelForm):
    skill_level = forms.Select(
        choices=SKILL_LEVEL_CHOICES
    )
    preferred_position = forms.Select(
        choices=PREFERRED_POSITION
    )

    class Meta:
        model = CustomUser
        fields = ['skill_level', 'preferred_position']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(UserDetailsForm, self).__init__(*args, **kwargs)
        self.fields['skill_level'].initial = user.skill_level
        self.fields['preferred_position'].initial = user.preferred_position
