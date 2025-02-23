from django.db import models
from django.contrib.auth.models import User
#from django.conf import settings

"""class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    def __str__(self):
        return self.username"""

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #shared_with = models.ManyToManyField(User, related_name='shared_folders', blank=True)  # Поле для спільного доступу

    def __str__(self):
        return self.name

class FolderPermission(models.Model):
    READ_ONLY = 'read'
    EDIT = 'edit'
    PERMISSION_CHOICES = [
        (READ_ONLY, 'Тільки перегляд'),
        (EDIT, 'Редагування'),
    ]
    
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default=READ_ONLY)

    class Meta:
        unique_together = ('folder', 'user')  # Один користувач - один дозвіл у папці

    def __str__(self):
        return f"{self.user.username} - {self.permission} ({self.folder.name})"


class Photo(models.Model):
    image = models.ImageField(upload_to='photos/')
    description = models.TextField(blank=True, null=True)  # Додано поле description
    folder = models.ForeignKey('Folder', 
        on_delete=models.CASCADE, 
        related_name='photos', 
        null=True,  # Додаємо дозволення на NULL
        blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    share_link = models.CharField(max_length=64, unique=True, blank=True, null=True)  # Додаємо поле


    def __str__(self):
        return self.image.name
