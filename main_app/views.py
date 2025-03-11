from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from .models import Photo, Folder, FolderPermission, PhotoPermission
from .forms import PhotoUploadForm, FolderCreateForm
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
import uuid
from django.core.mail import send_mail

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
class PhotoAlbumView(TemplateView):
    template_name = "photo_album.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder_id = self.kwargs.get('folder_id')
        folder = get_object_or_404(Folder, id=folder_id) if folder_id else None
        user = self.request.user

        can_edit = user_can_edit(user, folder) if folder else False

        context.update({
            "folder": folder,
            "photos": Photo.objects.filter(folder=folder) if folder else [],
            "shared_users": FolderPermission.objects.filter(folder=folder) if folder else [],
            "has_access": user_has_access(user, folder) if folder else False,
            "can_edit": can_edit,  # Передаємо змінну can_edit
        })
        return context
    
    def get(self, request, folder_id=None):
        folder = None
        shared_users = []
        can_edit = False
        
        if folder_id:
            folder = get_object_or_404(Folder, id=folder_id)
            if not user_has_access(request.user, folder):
                return HttpResponseForbidden("Ви не маєте доступу до цієї папки")
            shared_users = FolderPermission.objects.filter(folder=folder).select_related("user")
            can_edit = user_can_edit(request.user, folder)
        # Отримуємо всі папки, які належать користувачу або доступні через FolderPermission
        allowed_folders = Folder.objects.filter(
            Q(user=request.user) | Q(permissions__user=request.user)
        ).distinct()

        # Виключаємо поточну папку (щоб фото не можна було перемістити туди ж)
        allowed_folders = allowed_folders.exclude(id=folder.id) if folder else allowed_folders

        # Отримуємо всі вкладені папки для поточної
        folders = allowed_folders.filter(parent=folder)

        # Отримуємо фото в папці, доступні користувачу
        photos = Photo.objects.filter(
            Q(user=request.user) |  
            Q(folder__permissions__user=request.user, permissions__isnull=False) |  
            Q(permissions__user=request.user),  
            folder=folder
        ).distinct()

        # Форми для завантаження фото та створення папок
        photo_form = PhotoUploadForm()
        folder_form = FolderCreateForm()

        return render(request, self.template_name, {
            "folder": folder,
            "folders": folders,
            "allowed_folders": allowed_folders,  # Додаємо список доступних папок
            "photos": photos,
            "photo_form": photo_form,
            "folder_form": folder_form,
            "shared_users": shared_users,
            "can_edit": can_edit,

        })
    
    def post(self, request, folder_id=None):
        folder = None
       
        if folder_id:
            folder = Folder.objects.filter(Q(id=folder_id) 
                                        & (Q(user=request.user) | Q(permissions__user=request.user))).first()

            if not folder:
                return HttpResponseForbidden("Ви не маєте доступу до цієї папки або вона не існує.")
        if "upload_photo" in request.POST:
            photo_form = PhotoUploadForm(request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.user = request.user
                photo.folder = folder
                photo.save()
                if folder:
                    users_with_access = FolderPermission.objects.filter(folder=folder).values_list('user', flat=True)
                    if folder.user.id not in users_with_access:
                        users_with_access = list(users_with_access)  # перетворюємо в список
                        users_with_access.append(folder.user.id)  # додаємо власника

                    for user_id in users_with_access:
                    # Для кожного користувача з доступом створюємо дозвіл на фото
                        PhotoPermission.objects.get_or_create(photo=photo, user_id=user_id)

                    send_folder_notification(folder, request.user, "upload")
                return redirect("photo_album_with_folder", folder_id=folder.id) if folder else redirect("photo_album")

        elif "create_folder" in request.POST:
            folder_form = FolderCreateForm(request.POST)
            if folder_form.is_valid():
                new_folder = folder_form.save(commit=False)
                new_folder.user = request.user  # Власник — це той, хто створює
                new_folder.parent = folder  # Прив'язка до батьківської папки
                new_folder.save()

                # Перевірка, чи є у батьківської папки користувачі з правом редагування
                if folder:
                    parent_permissions = FolderPermission.objects.filter(
                        folder=folder, permission=FolderPermission.EDIT
                    )

                    # Додаємо їх до нової папки
                    for perm in parent_permissions:
                        FolderPermission.objects.create(
                            folder=new_folder,
                            user=perm.user,
                            permission=FolderPermission.EDIT
                        )

                    # Додати власника батьківської папки, якщо він ще не є
                    if folder.user != request.user:
                        FolderPermission.objects.create(
                            folder=new_folder,
                            user=folder.user,
                            permission=FolderPermission.EDIT
                        )

                return redirect("photo_album_with_folder", folder_id=new_folder.id)
        return self.get(request, folder_id)
    
class SharedPhotoView(View):
    template_name = "shared_photo.html"
    
    def get(self, request, photo_id=None, share_link=None):
        if share_link:
            # Доступ за унікальним посиланням
            photo = get_object_or_404(Photo, share_link=share_link)
        else:
            # Доступ за ID тільки для власника або користувачів із дозволом
            photo = get_object_or_404(Photo, id=photo_id)
            if not (photo.user == request.user or PhotoPermission.objects.filter(photo=photo, user=request.user).exists()):
                return HttpResponseForbidden("Ви не маєте доступу до цього фото")

        return render(request, self.template_name, {"photo": photo})

    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id, user=request.user)
        username = request.POST.get("username")

        if username == request.user.username:
            messages.error(request, "Ви вже маєте це фото")
            return redirect("photo_album_with_folder", folder_id=photo.folder.id) if photo.folder else redirect("photo_album")

        try:
            user_to_share = User.objects.get(username=username)

            # Перевіряємо, чи у користувача є доступ до цієї папки
            has_folder_access = (
                photo.folder and FolderPermission.objects.filter(folder=photo.folder, user=user_to_share).exists()
            )

            if has_folder_access:
                # Якщо у користувача є доступ до папки, просто даємо дозвіл на це фото
                PhotoPermission.objects.get_or_create(photo=photo, user=user_to_share)
            else:
                # Якщо доступу до папки немає, робимо копію фото у його основну папку
                shared_photo = Photo.objects.create(
                    user=user_to_share,
                    folder=None,  # Основна папка user_to_share
                    image=photo.image  # Копія фото
                )

                # Додаємо дозвіл на нове фото
                PhotoPermission.objects.get_or_create(photo=shared_photo, user=user_to_share)

            messages.success(request, f"Фото поділено з {username}.")
            send_photo_shared_email(photo, user_to_share)

        except User.DoesNotExist:
            messages.error(request, "Користувача не знайдено")

        return redirect("photo_album_with_folder", folder_id=photo.folder.id) if photo.folder else redirect("photo_album")
        
class GenerateShareLinkView(View):
    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, Q(id=photo_id) & (Q(user=request.user) | Q(folder__permissions__user=request.user)))
        
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

        if username == request.user.username:
            messages.error(request, "Ви не можете поділитися папкою з самим собою")
            return redirect('photo_album_with_folder', folder_id=folder.id)

        try:
            user_to_share = User.objects.get(username=username)
            
            # Перевірка на наявність надпапки
            if folder.parent and not FolderPermission.objects.filter(folder=folder.parent, user=user_to_share).exists():
                # Якщо немає доступу до надпапки, створюємо копію папки у користувача
                new_folder_name = f"{folder.name} ({folder.user.username})"
                new_folder = Folder.objects.create(
                    name=new_folder_name,
                    user=user_to_share,
                    parent=None  # Нова папка буде корінною
                )
                
                # Копіюємо всі фото до нової папки
                for photo in folder.photos.all():
                    new_photo = Photo.objects.create(
                        image=photo.image,
                        description=photo.description,
                        user=user_to_share,
                        folder=new_folder  # Призначаємо нову папку
                    )
                    new_folder.photos.add(new_photo)

                # Оновлюємо доступ до нової папки
                FolderPermission.objects.create(folder=new_folder, user=user_to_share, permission=permission_type)
                permission_display = dict(FolderPermission.PERMISSION_CHOICES).get(permission_type)  # Отримуємо відображення
            else:
                # Якщо доступ до надпапки є, просто надаємо доступ до поточної папки
                permission, created = FolderPermission.objects.get_or_create(folder=folder, user=user_to_share)
                permission.permission = permission_type
                permission.save()

                # Додаємо права доступу до всіх фото в цій папці
                if created:
                    photos = folder.photos.all()  # Отримуємо всі фото в папці
                    PhotoPermission.objects.bulk_create([ 
                        PhotoPermission(photo=photo, user=user_to_share, permission=PhotoPermission.VIEW)
                        for photo in photos
                    ], ignore_conflicts=True)
                permission_display = permission.get_permission_display()  # Отримуємо відображення з об'єкта permission

            messages.success(request, f"Папку поділено з {username} ({permission_display})")
        except User.DoesNotExist:
            messages.error(request, "Користувача не знайдено")

        return redirect('photo_album_with_folder', folder_id=folder.id)

    
class DeletePhotoView(View):
    
    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, id=photo_id)
        permission = PhotoPermission.objects.filter(photo=photo, user=request.user).first()
        
        if photo.user == request.user:
            # Власник фото може його видалити
            folder_id = photo.folder.id if photo.folder else None
            photo.delete()
            messages.success(request, "Фото успішно видалено.")
            return redirect('photo_album_with_folder', folder_id=folder_id) if folder_id else redirect('photo_album')

        if photo.folder:
            # Перевірка доступу через редагування в папці
            if FolderPermission.objects.filter(folder=photo.folder, user=request.user, permission=FolderPermission.EDIT).exists():
                folder_id = photo.folder.id if photo.folder else None
                photo.delete()
                messages.success(request, "Фото успішно видалено.")
                return redirect('photo_album_with_folder', folder_id=folder_id) 

            # Перевірка доступу через читання (READ_ONLY)
            if FolderPermission.objects.filter(folder=photo.folder, user=request.user, permission=FolderPermission.READ_ONLY).exists():
                # Якщо користувач має доступ лише для читання, ми не можемо видалити фото, але можемо видалити дозвіл на це фото
                if permission:
                    permission.delete()
                    messages.success(request, "Ви більше не маєте доступу до цього фото.")
                    return redirect('photo_album_with_folder', folder_id=photo.folder.id)

        if permission:
            permission.delete()
            messages.success(request, "Ви більше не маєте доступу до цього фото.")
            return redirect('photo_album_with_folder', folder_id=photo.folder.id) if photo.folder else redirect('photo_album')

        return HttpResponseForbidden("Ви не маєте права видаляти це фото.")

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
            send_folder_notification(folder, request.user, "unsubscribe")
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
        current_user = request.user 
        users = User.objects.filter(username__icontains=query).exclude(id=current_user.id)[:10]  # Обмежуємо 10 результатами
        users_data = [{"id": user.id, "username": user.username} for user in users]

        return JsonResponse({"users": users_data})
    

def send_folder_notification(folder, user, action):
    """Надсилає email-сповіщення всім користувачам, які мають доступ до папки"""
    shared_users = FolderPermission.objects.filter(folder=folder).select_related("user")
    recipient_emails = [perm.user.email for perm in shared_users if perm.user.email]

    if not recipient_emails:
        return  # Немає кому надсилати

    action_messages = {
        "upload": f"Користувач {user.username} додав нове фото у папку '{folder.name}'.",
        "delete": f"Користувач {user.username} видалив фото з папки '{folder.name}'.",
        "unsubscribe": f"Користувач {user.username} більше не має доступу до папки '{folder.name}'.",
    }

    subject = "Оновлення у спільній папці"
    message = action_messages.get(action, "Відбулися зміни у папці.")

    send_mail(
        subject=subject,
        message=message,
        from_email="noreply@example.com",
        recipient_list=recipient_emails,
        fail_silently=True,
    )

def send_photo_shared_email(photo, user):
    """Надсилає email-сповіщення користувачу про доступ до фото"""
    if not user.email:
        return
    send_mail(
        subject="Вам надано доступ до фото",
        message=f"Користувач {photo.user.username} поділився з вами фото.",
        from_email="noreply@example.com",
        recipient_list=[user.email],
        fail_silently=True,
    )


class MovePhotoView(View):
    def post(self, request, photo_id):
        # Отримуємо фото та перевіряємо права доступу
        photo = get_object_or_404(Photo, id=photo_id, user=request.user)
        folder_id = request.POST.get("folder_id")

        if folder_id:
            # Отримуємо всі доступні папки
            allowed_folders = Folder.objects.filter(
                Q(user=request.user) | Q(permissions__user=request.user)
            ).distinct()

            # Перевіряємо, чи вибрана папка є в списку дозволених
            folder = allowed_folders.filter(id=folder_id).first()

            if folder:
                # Переміщення фото в обрану папку
                photo.folder = folder
                photo.save()
                messages.success(request, "Фото успішно переміщено.")
            else:
                messages.error(request, "У вас немає доступу до цієї папки.")
        else:
            # Якщо folder_id не передано, переміщаємо фото в головну папку
            photo.folder = None
            photo.save()
            messages.success(request, "Фото переміщено в головну папку.")
            return redirect("photo_album")
        return redirect("photo_album_with_folder", folder_id=photo.folder.id if photo.folder else "photo_album")

class MoveFolderView(View):
    def post(self, request, folder_id):
        # Отримуємо папку, яку потрібно перемістити
        folder = get_object_or_404(Folder, id=folder_id)

        # Перевіряємо, чи користувач має право редагувати цю папку
        if not (folder.user == request.user or FolderPermission.objects.filter(
                folder=folder, user=request.user, permission=FolderPermission.EDIT).exists()):
            return HttpResponseForbidden("У вас немає прав на переміщення цієї папки.")

        new_parent_id = request.POST.get("parent_id")

        # Якщо new_parent_id пустий → переміщуємо в кореневу папку (root)
        if new_parent_id:
            new_parent = get_object_or_404(Folder, id=new_parent_id)

            # **Заборона переміщення папки в саму себе або в свою підпапку**
            if new_parent == folder or folder in new_parent.get_ancestors():
                messages.error(request, "Неможливо перемістити папку в саму себе або в її підпапку.")
                return redirect("photo_album_with_folder", folder_id=folder.id)

            folder.parent = new_parent
        else:
            folder.parent = None  # Переміщуємо в головну папку

        folder.save()
        messages.success(request, "Папку успішно переміщено.")

        if folder.parent:
            return redirect("photo_album_with_folder", folder_id=folder.parent.id)
        else:
            return redirect("photo_album")