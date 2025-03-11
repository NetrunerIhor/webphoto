from django.contrib.auth import authenticate, login, logout
from django.shortcuts import HttpResponseRedirect, render , redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.models import User
#from django.contrib.auth import get_user_model
from .forms import LoginForm, SignUpForm, PasswordResetRequestForm, PasswordResetForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

#User = get_user_model()

class Register(View):
    template_name = "register.html"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('photo_album') 
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        context = {"form": SignUpForm()}
        return render(request, self.template_name, context)

    def post(self, request):
        if request.method == "POST":
            form = SignUpForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get("username")
                email = form.cleaned_data.get("email")
                password = form.cleaned_data.get("password1")

                if User.objects.filter(username=username).exists():
                    form.add_error("username", "Користувач із таким ім'ям вже існує.")
                    messages.error(request, "Користувач із таким ім'ям вже існує.")
                    return render(request, self.template_name, {"form": form})

                if User.objects.filter(email=email).exists():
                    form.add_error("email", "Ця електронна пошта вже використовується.")
                    messages.error(request, "Ця електронна пошта вже використовується.")
                    return render(request, self.template_name, {"form": form})
                
                user = form.save()
                user.set_password(password)  # Упевнюємось, що пароль хешується
                user.save()
                user = authenticate(username=username, email=email, password=password)
                if user is not None:
                    login(request, user)
                return redirect("photo_album")

        # Якщо форма не пройшла валідацію, або є інші помилки
        context = {"form": form}
        return render(request, self.template_name, context)

class Login(View):
    template_name = "Login.html"  
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('photo_album')  
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        context = {"form": LoginForm()}
        return render(request, self.template_name, context)

    def post(self, request):
        if request.method == "POST":
            form = LoginForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password")
                user = authenticate(username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    return redirect("photo_album")
                else:
                    messages.error(request, "Невірне ім'я користувача або пароль.")
                    return render(request, self.template_name, {"form": form})

        context = {"form": form}
        return render(request, self.template_name, context)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("home"))

class PasswordResetRequestView(View):
    template_name = "password_reset_request.html"

    def get(self, request):
        form = PasswordResetRequestForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            try:
                user = User.objects.get(username=username, email=email)
                request.session['reset_user_id'] = user.id
                return redirect("password_reset")
            except User.DoesNotExist:
                messages.error(request, "Користувача з такими даними не знайдено.")
        return render(request, self.template_name, {"form": form})

class PasswordResetView(View):
    template_name = "password_reset.html"

    def get(self, request):
        if "reset_user_id" not in request.session:
            return redirect("password_reset_request")
        form = PasswordResetForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if "reset_user_id" not in request.session:
            return redirect("password_reset_request")
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user = User.objects.get(id=request.session["reset_user_id"])
            new_password = form.cleaned_data.get("new_password1")
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Залишаємо користувача в системі
            del request.session["reset_user_id"]
            messages.success(request, "Пароль успішно змінено.")
            return redirect("login-page")
        return render(request, self.template_name, {"form": form})


@login_required
def profile_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        new_password = request.POST.get("new_password")

        user = request.user
        changes_made = False

        # Перевірка, чи username вже зайнятий іншим користувачем
        if username != user.username and User.objects.filter(username=username).exists():
            messages.error(request, "Цей username вже використовується іншим користувачем.")
            return redirect("profile-page")

        # Перевірка, чи email вже зайнятий іншим користувачем
        if email != user.email and User.objects.filter(email=email).exists():
            messages.error(request, "Ця email-адреса вже зареєстрована іншим користувачем.")
            return redirect("profile-page")

        """# Якщо email змінено – надсилаємо лист для підтвердження
        if email != user.email:
            send_mail(
                subject="Підтвердження зміни email",
                message=f"Будь ласка, підтвердіть зміну email, перейшовши за посиланням:\n"
                        f"{settings.SITE_URL}/confirm-email-change/{user.id}/?new_email={email}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.info(request, "На новий email надіслано лист для підтвердження змін.")
        """
        # Оновлення username та email
        user.username = username
        user.email = email
        changes_made = True

        # Оновлення паролю, якщо введено новий
        if new_password:
            user.set_password(new_password)
            update_session_auth_hash(request, user)  # Щоб користувач не вилогінився після зміни пароля
            changes_made = True

        if changes_made:
            user.save()
            messages.success(request, "Зміни успішно збережені!")

        return redirect("profile-page")

    return render(request, "profile.html")

"""@login_required
def confirm_email_change(request, user_id):
    new_email = request.GET.get("new_email")
    if not new_email:
        messages.error(request, "Некоректний запит на зміну email.")
        return redirect("profile-page")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Користувача не знайдено.")
        return redirect("profile-page")

    if user != request.user:
        messages.error(request, "Ви не можете змінювати email інших користувачів.")
        return redirect("profile-page")

    user.email = new_email
    user.save()
    messages.success(request, "Email успішно оновлено!")
    return redirect("profile-page")"""