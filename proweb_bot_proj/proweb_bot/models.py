from django.db import models


# Create your models here.

class CustomUser(models.Model):
    username_tg = models.CharField(max_length=150, blank=True, null=True, verbose_name='Юсер пользователя')
    name_tg = models.CharField(max_length=150, blank=True, null=True, verbose_name='Имя пользователя')
    phone_tg = models.CharField(max_length=20, blank=True, null=True, verbose_name='Номер телефона')
    tg_id = models.CharField(max_length=20, blank=True, null=True, verbose_name='ID Телеграм')
    is_admin = models.BooleanField(default=False, verbose_name='Статус администратора')
    language = models.CharField(max_length=10, default='ru', verbose_name='Язык интерфейса')

    def __str__(self):
        return self.tg_id

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class AdminUser(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    telegram_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def __str__(self):
        return f'{self.user.tg_id} - Админ'

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'


class GroupsCategory(models.Model):
    category_name = models.CharField(max_length=100, verbose_name='Название курса')

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'


class Groups(models.Model):
    category = models.ForeignKey(GroupsCategory, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Курс')
    group_id = models.CharField(max_length=100, unique=True, verbose_name='ID группы')
    name_group = models.CharField(max_length=200, verbose_name='Название группы')
    language = models.CharField(max_length=5, blank=True, null=True, verbose_name='Язык группы')

    def __str__(self):
        return self.name_group

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Posts(models.Model):
    groups = models.ManyToManyField(Groups, blank=True, null=True, verbose_name='Группы')
    user = models.ManyToManyField(CustomUser, blank=True, null=True, verbose_name='Пользователи')
    text_post = models.TextField(blank=True, null=True, verbose_name='Описание для поста')
    media = models.JSONField(default=list, verbose_name='Список медиа')

    # def __str__(self):
    #     return self.

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class MediaPost(models.Model):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, verbose_name='Пост')
    photo = models.ImageField(upload_to='post_media/photo/', blank=True, null=True, verbose_name='Фото поста')
    video = models.FileField(upload_to='post_media/video/', blank=True, null=True, verbose_name='Видео')
    voice = models.FileField(upload_to='post_media/voices/', blank=True, null=True)

    def __str__(self):
        return f"Медиа для поста {self.post.id}"

    class Meta:
        verbose_name = 'Медиа для поста'
        verbose_name_plural = 'Медиа для постов'


class GroupPost(models.Model):
    post = models.ForeignKey(Posts, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Пост')
    group = models.ForeignKey(Groups, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Группа')
    message_id = models.CharField(max_length=100, verbose_name='ID сообщения в группе')

    def __str__(self):
        return f'Post {self.post.id} in group {self.group.name_group}'

    class Meta:
        verbose_name = 'Пост в Группе'
        verbose_name_plural = 'Посты в Группах'


class UserGroupPost(models.Model):
    user_post = models.ForeignKey(Posts, on_delete=models.CASCADE, verbose_name='Пост для пользователя')
    chat_id = models.CharField(max_length=255, verbose_name='ID чата')
    message_id = models.CharField(max_length=255, verbose_name='ID сообщения')

    def __str__(self):
        return self.user_post

    class Meta:
        verbose_name = 'Пост в Чате'
        verbose_name_plural = 'Посты в Чатах'


# class UserPost(models.Model):
#     user = models.ManyToManyField(CustomUser, verbose_name='Пользователи')
#     message_id = models.CharField(max_length=255, verbose_name='ID сообщения')
#     text = models.TextField(null=True, blank=True, verbose_name='Текст')
#     media = models.JSONField(default=list, verbose_name='Список медиа')
#
#     def __str__(self):
#         return self.message_id
#
#     class Meta:
#         verbose_name = 'Пост для пользователя'
#         verbose_name_plural = 'Посты для пользователей'
