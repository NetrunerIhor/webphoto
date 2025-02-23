from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from .models import Photo, Folder, FolderPermission
from .forms import PhotoUploadForm, FolderCreateForm
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
#from django.contrib.auth import get_user_model
import uuid

#User = get_user_model()

class HomeView(TemplateView):
    template_name = 'home.html'

def user_has_access(user, folder):
    """ Перевіряє, чи користувач має права перегляду для папки """
    if folder.user == user:
        return True  # Власник має всі права
    return FolderPermission.objects.filter(folder=folder, user=user).exists()

def user_can_edit(user, folder):
    """Перевіряє, чи користувач має право редагувати папку"""
    if folder.user == user:
        return True  # Власник має всі права
    return FolderPermission.objects.filter(folder=folder, user=user, permission=FolderPermission.EDIT).exists()

@method_decorator(login_required, name='dispatch')
class PhotoAlbumView(View):
    template_name = "photo_album.html"

    def get(self, request, folder_id=None):
        folder = None
        shared_users = []
        if folder_id:
            folder = get_object_or_404(Folder, id=folder_id)
            if not user_has_access(request.user, folder):
                return HttpResponseForbidden("Ви не маєте доступу до цієї папки")
            shared_users = FolderPermission.objects.filter(folder=folder).select_related('user')
        
        folders = Folder.objects.filter(
            Q(user=request.user) | Q(permissions__user=request.user), 
            parent=folder
        ).distinct()
        photos = Photo.objects.filter(folder=folder)
        photo_form = PhotoUploadForm()
        folder_form = FolderCreateForm()

        return render(request, self.template_name, {
            "folder": folder,
            "folders": folders,
            "photos": photos,
            "photo_form": photo_form,
            "folder_form": folder_form,
            "shared_users": shared_users, 
        })

    def post(self, request, folder_id=None):
        folder = None
        if folder_id:
            folder = get_object_or_404(Folder, id=folder_id, user=request.user)

        """if "profile_picture" in request.FILES:
            request.user.profile_picture = request.FILES["profile_picture"]
            request.user.save()
            messages.success(request, "Фото профілю оновлено!")
"""
        if "upload_photo" in request.POST:
            photo_form = PhotoUploadForm(request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.user = request.user
                photo.folder = folder
                photo.save()
                return redirect("photo_album_with_folder", folder_id=folder.id) if folder else redirect("photo_album")

        elif "create_folder" in request.POST:
            folder_form = FolderCreateForm(request.POST)
            if folder_form.is_valid():
                new_folder = folder_form.save(commit=False)
                new_folder.user = request.user
                new_folder.parent = folder
                new_folder.save()
                return redirect("photo_album_with_folder", folder_id=new_folder.id) if new_folder else redirect("photo_album")

        return self.get(request, folder_id)
    
class SharedPhotoView(View):
    template_name = "shared_photo.html"

    def get(self, request, share_link):
        photo = get_object_or_404(Photo, share_link=share_link)
        return render(request, self.template_name, {"photo": photo})
    
class GenerateShareLinkView(View):
    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id, user=request.user)
        
        # Генеруємо share_link, якщо він ще не згенерований
        if not photo.share_link:
            photo.share_link = str(uuid.uuid4())  # Унікальний ідентифікатор
            photo.save()

        # Перевірка, чи є folder, і редирект у відповідну папку
        if photo.folder:
            return redirect('photo_album_with_folder', folder_id=photo.folder.id)
        else:
            return redirect('photo_album')  # Якщо folder = None, повертаємось до кореневої папки

class ShareFolderView(View):
    
    def post(self, request, folder_id):
        
        folder = get_object_or_404(Folder, id=folder_id, user=request.user)
        username = request.POST.get("username")
        permission_type = request.POST.get("permission")

        if permission_type not in [FolderPermission.READ_ONLY, FolderPermission.EDIT]:
            messages.error(request, "Невірний тип доступу")
            return redirect('photo_album_with_folder', folder_id=folder.id)

        try:
            user_to_share = User.objects.get(username=username)
            
            # Оновлюємо або створюємо запис у FolderPermission
            permission, created = FolderPermission.objects.get_or_create(folder=folder, user=user_to_share)
            permission.permission = permission_type
            permission.save()

            messages.success(request, f"Папку поділено з {username} ({permission.get_permission_display()})")
        except User.DoesNotExist:
            messages.error(request, "Користувача не знайдено")

        return redirect('photo_album_with_folder', folder_id=folder.id)
    
class DeletePhotoView(View):
    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id)
        if not user_can_edit(request.user, photo.folder):
            return HttpResponseForbidden("Ви не маєте права видаляти це фото")
        folder_id = photo.folder.id if photo.folder else None
        photo.delete()
        messages.success(request, "Фото успішно видалено.")
        
        if folder_id:
            return redirect('photo_album_with_folder', folder_id=folder_id)
        return redirect('photo_album')
    
class DeleteFolderView(View):
    def post(self, request, folder_id):
        folder = Folder.objects.filter(
            Q(id=folder_id) & (Q(user=request.user) | Q(permissions__user=request.user))
        ).first()

        if not folder:
            return HttpResponseForbidden("Ви не маєте доступу до цієї папки або вона не існує.")

        # Якщо користувач є власником, видаляємо папку
        if folder.user == request.user:
            folder.delete()
            messages.success(request, "Папку успішно видалено.")
        else:
            # Якщо користувач має доступ (перегляд або редагування), просто видаляємо його дозвіл
            FolderPermission.objects.filter(folder=folder, user=request.user).delete()
            messages.success(request, "Ви більше не маєте доступу до цієї папки.")
        
        return redirect('photo_album')
        

class RemoveUserPermissionView(View):
    def post(self, request, folder_id, user_id):
        folder = get_object_or_404(Folder, id=folder_id, user=request.user)  # Тільки власник папки може змінювати доступ
        user_to_remove = get_object_or_404(User, id=user_id)

        # Видаляємо доступ
        FolderPermission.objects.filter(folder=folder, user=user_to_remove).delete()

        messages.success(request, f"Доступ для {user_to_remove.username} видалено.")
        return redirect('photo_album_with_folder', folder_id=folder.id)

class SearchUsersView(View):
    def get(self, request):
        query = request.GET.get("query", "").strip()

        if len(query) < 3:  # Запуск пошуку тільки після 3+ символів
            return JsonResponse({"users": []})

        users = User.objects.filter(username__icontains=query)[:10]  # Обмежуємо 10 результатами
        users_data = [{"id": user.id, "username": user.username} for user in users]

        return JsonResponse({"users": users_data})