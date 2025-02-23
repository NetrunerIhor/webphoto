from django.contrib.auth import authenticate, login, logout
from django.shortcuts import HttpResponseRedirect, render , redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.models import User
#from django.contrib.auth import get_user_model
from .forms import LoginForm, SignUpForm

#User = get_user_model()

class Register(View):
    template_name = (
        "register.html"
    ) 

    def get(self, request):
        context = {"form": SignUpForm()}
        return render(request, self.template_name, context)

    def post(self, request):
        if request.method == "POST":
            form = SignUpForm(request.POST)
            if form.is_valid():
                form.save()
                username = form.cleaned_data.get("username")
                email = form.cleaned_data.get("email")
                password = form.cleaned_data.get("password1")

                user = authenticate(username=username, email=email, password=password)
                login(request, user)
                User.objects.create(username=username, email=email, password=password)
                return redirect("profile.html")
        context = {"form": form}
        return render(request, self.template_name, context)


class Login(View):
    template_name = "Login.html"  #'signup/login.html'

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

        context = {"form": form}
        return render(request, self.template_name, context)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("home"))
