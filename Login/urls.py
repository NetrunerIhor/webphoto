from django.urls import path
from . import views
from .views import profile_view

urlpatterns = [
    path("register/", views.Register.as_view(), name="register-page"),
    path("login/", views.Login.as_view(), name="login-page"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", profile_view, name="profile-page"),
    path('password-reset-request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    
]