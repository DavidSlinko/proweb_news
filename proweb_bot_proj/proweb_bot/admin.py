from django.contrib import admin
from .models import AdminUser, CustomUser


# Register your models here.


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_id')
    list_display_links = ('user', 'telegram_id')


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'username_tg', 'name_tg', 'is_admin')
    list_display_links = ('user', 'username_tg')
