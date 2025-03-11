from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None  # Перевіряємо, чи є введені дані
        
        user = User.objects.filter(Q(username=username) | Q(email=username)).first()  # Уникаємо MultipleObjectsReturned
        if user and user.check_password(password):
            return user
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
