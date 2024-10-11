from django.db import models


# Create your models here.

class BotUser(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        self.name

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
