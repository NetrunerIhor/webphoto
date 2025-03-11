from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
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
    def get_ancestors(self):
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors

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
    image = CloudinaryField('image')
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
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Перевіряємо, чи це нове фото
        super().save(*args, **kwargs)  # Спочатку зберігаємо фото

        if is_new and self.folder:  # Якщо це нове фото і воно в папці
            # Додамо дозволи всім користувачам, які мають доступ до цієї папки
            users_with_access = FolderPermission.objects.filter(folder=self.folder).values_list('user', flat=True)
            # Додаємо доступ всім користувачам з дозволом на папку
            for user_id in users_with_access:
                PhotoPermission.objects.get_or_create(photo=self, user_id=user_id)

class PhotoPermission(models.Model):
    VIEW = "view"
    PERMISSION_CHOICES = [
        (VIEW, "Перегляд"),
    ]

    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="permissions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default=VIEW)

    class Meta:
        unique_together = ("photo", "user")  # Один користувач - одне фото


