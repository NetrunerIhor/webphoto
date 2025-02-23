from django import forms
from .models import Photo, Folder

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image', 'description', 'folder']

class FolderCreateForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'parent']