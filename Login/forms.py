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
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "Email",
                "id": "email",
                "title": "Введіть вашу електронну пошту.",
                "class": "w-full px-3 py-2 border rounded-lg",
            }
        ),
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        help_text="Обов’язково. Не більше 150 символів. Лише літери, цифри та @/./+/-/_.",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "placeholder": "Username",
                "id": "username",
                "title": "Не більше 150 символів. Лише літери, цифри та @/./+/-/_.",
                "class": "w-full px-3 py-2 border rounded-lg",
            }
        ),
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "autocomplete":"new-password",
                "placeholder": "Пароль",
                "id": "password1",
                "title": "Пароль має містити принаймні 8 символів, не бути схожим на особисту інформацію, не бути занадто поширеним та не складатися лише з цифр.",
                "class": "w-full px-3 py-2 border rounded-lg",
            }
        ),
        help_text=(
            "Пароль не має бути надто схожим на вашу особисту інформацію.<br>"
            "Має містити принаймні 8 символів.<br>"
            "Не має бути поширеним паролем.<br>"
            "Не може складатися лише з цифр."
        ),
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Повторіть пароль",
                "id": "password2",
                "title": "Введіть той самий пароль ще раз для перевірки.",
                "class": "w-full px-3 py-2 border rounded-lg",
            }
        ),
        help_text="Введіть той самий пароль, що й вище, для перевірки.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")



class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()

    fields = ("username", "password")

    widgets_log = {
        "username": forms.TextInput(
            attrs={"placeholder": "Username", "id": "username_log", "class": "w-full px-3 py-2 border rounded-lg"}
        ),
        "password": forms.PasswordInput(
            attrs={"placeholder": "Password", "id": "password_log", "class": "w-full px-3 py-2 border rounded-lg"}
        ),
    }

    # Оновлення поля форми, щоб застосовувати віджети
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = self.widgets_log.get(field, self.fields[field].widget)


class PasswordResetRequestForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        label="Ім'я користувача", 
        widget=forms.TextInput(attrs={"class": "w-full px-3 py-2 border rounded-lg"})
    )
    email = forms.EmailField(
        label="Електронна пошта", 
        widget=forms.EmailInput(attrs={"class": "w-full px-3 py-2 border rounded-lg"})
    )

class PasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "w-full px-3 py-2 border rounded-lg"}), 
        label="Новий пароль"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "w-full px-3 py-2 border rounded-lg"}), 
        label="Повторіть пароль"
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error("new_password2", "Паролі не співпадають.")
        return cleaned_data