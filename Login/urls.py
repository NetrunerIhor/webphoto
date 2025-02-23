from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.Register.as_view(), name="register-page"),
    path("login/", views.Login.as_view(), name="login-page"),
    path("logout/", views.logout_view, name="logout"),
]