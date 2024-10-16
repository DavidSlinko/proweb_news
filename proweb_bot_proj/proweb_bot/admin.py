from django.contrib import admin
from .models import *


# Register your models here.
@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_id')
    list_display_links = ('user', 'telegram_id')


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username_tg', 'name_tg', 'is_admin')
    list_display_links = ('username_tg', 'name_tg')


@admin.register(Groups)
class GroupsAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'name_group')
    list_display_links = ('group_id', 'name_group')


@admin.register(GroupsCategory)
class GroupsCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name')
    list_display_links = ('id', 'category_name')


@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_post', )
    list_display_links = ('id', 'text_post')


@admin.register(MediaPost)
class MediaPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'post')
    list_display_links = ('id', 'post')


@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'group_id', 'message_id')
    list_display_links = ('id', 'post')

@admin.register(UserGroupPost)
class UserGroupPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_post', 'chat_id', 'message_id')
    list_display_links = ('id', 'user_post')








