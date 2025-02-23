from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from main_app.models import UserProfile

User = get_user_model()


@receiver(user_signed_up)
def create_user_profile(request, user, **kwargs):
    UserProfile.objects.create(user=user)