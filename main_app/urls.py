from django.urls import path
from .views import (HomeView, PhotoAlbumView, 
                    SharedPhotoView, ShareFolderView, 
                    GenerateShareLinkView, DeletePhotoView, 
                    DeleteFolderView, RemoveUserPermissionView,
                    SearchUsersView,MovePhotoView,MoveFolderView,
                    
                    )

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path("album/", PhotoAlbumView.as_view(), name="photo_album"),
    path("album/<int:folder_id>/", PhotoAlbumView.as_view(), name="photo_album_with_folder"),
    path('photo/shared/<str:share_link>/', SharedPhotoView.as_view(), name='shared_photo'),
    path('photo/share/<int:photo_id>/', SharedPhotoView.as_view(), name='share_photo'),
    path('album/share/<int:folder_id>', ShareFolderView.as_view(), name='share_folder'),
    path('photo/generate-link/<int:photo_id>/', GenerateShareLinkView.as_view(), name='generate_share_link'),
    path('photo/delete/<int:photo_id>/', DeletePhotoView.as_view(), name='delete_photo'),
    path('album/delete-folder/<int:folder_id>/', DeleteFolderView.as_view(), name='delete_folder'),
    path('folder/<int:folder_id>/remove-user/<int:user_id>/', RemoveUserPermissionView.as_view(), name='remove_user_permission'),
    path("search-users/", SearchUsersView.as_view(), name="search_users"),
    path('move-photo/<int:photo_id>/', MovePhotoView.as_view(), name='move_photo'),
    path('move_folder/<int:folder_id>/', MoveFolderView.as_view(), name='move_folder'),

    ]
