from django.db import models
from django.contrib.auth.models import User, AbstractUser


# Create your models here.

class CustomUser(AbstractUser):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь', blank=True, null=True)
    username_tg = models.CharField(max_length=150, blank=True, null=True, verbose_name='Юсер пользователя')
    name_tg = models.CharField(max_length=150, blank=True, null=True, verbose_name='Имя пользователя')
    phone_tg = models.CharField(max_length=20, blank=True, null=True, verbose_name='Номер телефона')
    tg_id = models.CharField(max_length=20, blank=True, null=True, verbose_name='ID Телеграм')
    is_admin = models.BooleanField(default=False, verbose_name='Статус администратора')
    language = models.CharField(max_length=10, default='ru')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
    )


class AdminUser(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    telegram_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} - Админ'

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'
