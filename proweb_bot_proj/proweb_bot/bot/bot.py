import logging

import telebot
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from telebot import types
from django.conf import settings
from proweb_bot.models import CustomUser, AdminUser
from proweb_bot.translations import translations

bot = telebot.TeleBot(settings.TG_BOT_TOKEN)

logging.basicConfig(level=logging.INFO)


@bot.message_handler(commands=['start'])
def start(message):
    random_password = get_random_string(10)

    user, created = CustomUser.objects.get_or_create(
        username_tg=message.from_user.username,
        tg_id=message.chat.id,
        defaults={'password': random_password, 'name_tg': message.from_user.first_name}
    )

    if created:
        user.set_password(random_password)
        user.save()
        logging.info(f"Создан пользователь: {user.username_tg} с паролем {random_password}")
    else:
        logging.info(f"Пользователь {user.username_tg} уже существует.")

    # Запрос на выбор языка
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    btn_en = types.KeyboardButton(text="Русский язык 🇷🇺")
    btn_ru = types.KeyboardButton(text="O'zbek tili 🇺🇿")
    markup.add(btn_en, btn_ru)

    bot.send_message(message.chat.id, 'Выберите язык/Tilni tanlang', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ["Русский язык 🇷🇺", "O'zbek tili 🇺🇿"])
def choose_language(message):
    user = CustomUser.objects.get(username_tg=message.from_user.username)

    if message.text == "Русский язык 🇷🇺":
        user.language = 'ru'
    elif message.text == "O'zbek tili 🇺🇿":
        user.language = 'uz'

    user.save()

    # Отправка сообщения после выбора языка
    bot.send_message(message.chat.id, translations[user.language]['btn_send_phone'])

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    button_phone = types.KeyboardButton(text=translations[user.language]['btn_send_phone'], request_contact=True)
    markup.add(button_phone)
    bot.send_message(message.chat.id, translations[user.language]['btn_send_phone'], reply_markup=markup)


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact:
        try:
            user = CustomUser.objects.get(username_tg=message.from_user.username)
            user.phone_tg = message.contact.phone_number
            user.save()
            bot.send_message(message.chat.id, "Спасибо! Ваш номер сохранён.")
            logging.info(f"Номер телефона сохранён для пользователя {user.username_tg}")
        except CustomUser.DoesNotExist:
            bot.send_message(message.chat.id, "Ошибка: пользователь не найден.")
            logging.error("Пользователь не найден для сохранения номера телефона.")


@receiver(post_save, sender=CustomUser)
def create_admin_user(sender, instance, created, **kwargs):
    if instance.is_admin:
        AdminUser.objects.create(user=instance, telegram_id=instance.username_tg)
        bot.send_message(instance.tg_id, translations[instance.language]['text_admin_notification'])
    # else:
    #     # Если статус администратора снят
    #     AdminUser.objects.filter(user=instance).delete()
    #     print(f"Пользователь {instance.username} больше не является администратором.")


def start_bot():
    bot.infinity_polling()
