from django.contrib import admin
from django.contrib.admin.sites import site

class CustomAdminSite(admin.AdminSite):
    site_header = "Поламаний Фотоальбом - Адмінка"
    site_title = "Адмінка Фотоальбому"
    index_title = "Керування сайтом"

admin.site = CustomAdminSite()

# Додаємо кастомний CSS
def custom_admin_css(request):
    return {
        'extra_css': ['/static/admin/css/custom_admin.css'],
    }

admin.site.each_context = lambda request: {**admin.site.each_context(request), **custom_admin_css(request)}
