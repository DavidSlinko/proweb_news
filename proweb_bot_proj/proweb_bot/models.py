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
