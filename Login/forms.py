from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

#User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    # username = forms.PasswordInput
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

        widgets = {
            "username": forms.TextInput(
                attrs={"placeholder": "Username", "id": "username"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "Email", "id": "email"}
            ),
            "password1": forms.PasswordInput(
                attrs={"placeholder": "password", "id": "password1"}
            ),
            "password2": forms.PasswordInput(
                attrs={"placeholder": "Repeat password", "id": "password2"}
            ),
        }


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()

    fields = ("username", "password")

    widgets_log = {
        "username": forms.TextInput(
            attrs={"placeholder": "Username", "id": "username_log"}
        ),
        "password": forms.PasswordInput(
            attrs={"placeholder": "password", "id": "password_log"}
        ),
    }
