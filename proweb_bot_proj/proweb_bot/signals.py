from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import CustomUser, AdminUser
from .bot import bot


@receiver(post_save, sender=CustomUser)
def create_admin_user(sender, instance, created, **kwargs):
    # Если статус администратора изменился на True и записи в AdminUser ещё нет
    if instance.is_admin and not AdminUser.objects.filter(user=instance).exists():
        AdminUser.objects.create(user=instance, telegram_id=instance.username_tg)

        if instance.username_tg:
            try:
                bot.bot.send_message(instance.tg_id, "Вы были назначены администратором.")

            except Exception as e:
                print(f"Ошибка при отправке сообщения: {e}")

    # Если статус администратора изменился на False, удаляем запись из AdminUser
    elif not instance.is_admin and AdminUser.objects.filter(user=instance).exists():

        if instance.username_tg:
            try:
                bot.bot.send_message(instance.tg_id, "Ваши права администратора были отозваны.")

            except Exception as e:
                print(f"Ошибка при отправке сообщения: {e}")

        AdminUser.objects.filter(user=instance).delete()
