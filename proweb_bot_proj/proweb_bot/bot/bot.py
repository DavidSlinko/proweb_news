import logging
import telebot
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from telebot import types
from django.conf import settings
from proweb_bot.models import CustomUser, AdminUser, Groups, GroupsCategory, Posts, MediaPost, GroupPost
from proweb_bot.translations import translations
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .send_users import handle_broadcast_to_users, lang
from .send_groups import category, handle_course_selection, choose_language, handle_next_step, choose_languages, \
    handle_language_selection, mail, handle_initial_message, send_broadcast, cancel_broadcast, handle_post_actions, \
    pin_post_in_groups, delete_post_from_groups
from .bot_instance import bot


# bot = telebot.TeleBot(settings.TG_BOT_TOKEN, parse_mode=None)
# telebot.logger.setLevel(logging.DEBUG)


def set_webhook():
    webhook_url = f"https://4968-192-166-230-205.ngrok-free.app/webhook/"
    bot.set_webhook(url=webhook_url)


set_webhook()
lang_button = {}
bot_data = {}
broadcast_data = {}


# logging.basicConfig(level=logging.INFO)


@bot.message_handler(commands=['start'])
def start(message):
    user, created = CustomUser.objects.get_or_create(
        username_tg=message.from_user.username,
        tg_id=message.chat.id,
        defaults={'name_tg': message.from_user.first_name}
    )

    if created:

        user.save()
        logging.info(f"Создан пользователь: {user.username_tg}")
    else:
        logging.info(f"Пользователь {user.username_tg} уже существует.")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_en = types.KeyboardButton(text="Русский язык 🇷🇺")
    btn_ru = types.KeyboardButton(text="O'zbek tili 🇺🇿")
    markup.add(btn_en, btn_ru)

    bot.send_message(message.chat.id, 'Выберите язык/Tilni tanlang', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ["Русский язык 🇷🇺", "O'zbek tili 🇺🇿"])
def choose_language_group(message):
    choose_language(message)


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user = CustomUser.objects.get(username_tg=message.from_user.username)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    # добавляем на нее кнопки
    support = types.InlineKeyboardButton(text=translations[user.language]['btn_support'], url='t.me/itsmylifestyle')
    coworking = types.InlineKeyboardButton(text=translations[user.language]['btn_coworking'], url='t.me/proweb_coworking')
    keyboard.add(support, coworking)

    competitions = types.InlineKeyboardButton(text=translations[user.language]['btn_competitions'], callback_data='competitions')
    web_site = types.InlineKeyboardButton(text=translations[user.language]['btn_web_site'], url='proweb.uz')
    keyboard.add(competitions, web_site)

    well = types.InlineKeyboardButton(text=translations[user.language]['btn_well'], callback_data='well')
    review = types.InlineKeyboardButton(text=translations[user.language]['btn_review'], callback_data='review')
    keyboard.add(well, review)

    rules = types.InlineKeyboardButton(text=translations[user.language]['btn_rules'], callback_data="rules")
    keyboard.add(rules)

    if message.contact:
        try:

            user.phone_tg = message.contact.phone_number
            user.save()
            bot.send_message(message.chat.id, "Спасибо! Ваш номер сохранён.")
            bot.send_message(message.chat.id, translations[user.language]['text_info'], reply_markup=keyboard)

        except CustomUser.DoesNotExist:
            bot.send_message(message.chat.id, "Ошибка: пользователь не найден.")


@receiver(post_save, sender=CustomUser)
def create_admin_user(sender, instance, created, **kwargs):
    markup = types.InlineKeyboardMarkup()
    confirm_button = types.InlineKeyboardButton(text="Подтвердить", callback_data="confirm_admin")
    markup.add(confirm_button)
    if instance.is_admin:
        AdminUser.objects.create(user=instance, telegram_id=instance.username_tg)
        bot.send_message(instance.tg_id, translations[instance.language]['text_admin_notification'],
                         reply_markup=markup)
    # else:
    #     AdminUser.objects.filter(user=instance).delete()
    #     print(f"Пользователь {instance.username} больше не является администратором.")


@bot.callback_query_handler(func=lambda call: call.data == "confirm_admin")
def handle_confirm_admin(call):
    chat_id = call.message.chat.id

    bot.send_message(chat_id, "Спасибо! Вы подтвердили своё назначение администратором.")

    show_admin_panel(chat_id, call)


def show_admin_panel(chat_id, call):
    try:
        user = CustomUser.objects.get(username_tg=call.from_user.username)
        language = user.language  # Получаем язык пользователя
    except CustomUser.DoesNotExist:
        bot.send_message(chat_id, "Ошибка: пользователь не найден.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_send_messages = types.KeyboardButton("📩 Сделать рассылку по пользователям")
    button_view_courses = types.KeyboardButton(translations[user.language]['btn_send_groups'])
    markup.add(button_send_messages, button_view_courses)
    bot.send_message(chat_id, "Панель администратора👇", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "📩 Сделать рассылку по пользователям" or "📚 Pochta uchun kurslarni tanlang")
def broadcast_command_handler(message):
    handle_broadcast_to_users(message)


@bot.message_handler(func=lambda message: message.text in ['Рус🇷🇺', 'Uzb🇺🇿', 'Отправить всем'])
def language_selection_handler(message):
    lang(message)


@bot.message_handler(func=lambda message: message.text == '📚 Выбрать курсы для рассылки')
def category_group(message):
    category(message)


@bot.message_handler(func=lambda message: message.text in [cat.category_name for cat in GroupsCategory.objects.all()])
def handle_course_selection_group(message):
    handle_course_selection(message)


@bot.message_handler(func=lambda message: message.text == "Далее")
def handle_next_step_group(message):
    handle_next_step(message)


def choose_languages_group(chat_id):
    choose_languages(chat_id)


@bot.message_handler(func=lambda message: message.text in ["РУС", "UZB", "Разослать всем"])
def handle_language_selection_group(message):
    handle_language_selection(message)


@bot.message_handler(func=lambda message: message.text == 'Переслать')
def mail_group(message):
    mail(message)


# @bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'poll'])
# def handle_forwarding_group(message):
#     handle_forwarding(message)


@bot.message_handler(content_types=['text', 'photo', 'video', 'voice'])
def handle_initial_message_group(message):
    handle_initial_message(message)


# Обработка команды "Отправить"
def send_broadcast_group(message):
    send_broadcast(message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('pin_') or call.data.startswith('delete_'))
def handle_post_actions_group(call):
    handle_post_actions(call)


def pin_post_in_groups_group(post):
    pin_post_in_groups(post)


def delete_post_from_groups_groups(post):
    delete_post_from_groups(post)


# Обработка команды "Отмена"
def cancel_broadcast_group(message):
    cancel_broadcast(message)


@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    for new_user in message.new_chat_members:
        if new_user.id == bot.get_me().id:
            group_id = message.chat.id
            group_name = message.chat.title
            list_name = group_name[:-1].replace('.', ' ').split()[1]
            language = group_name[:-1].replace('.', ' ').split()[2]

            category_group, created = GroupsCategory.objects.get_or_create(category_name=("".join(list_name)))

            group, created = Groups.objects.get_or_create(group_id=group_id, category=category_group,
                                                          defaults={'name_group': group_name}, language=language)


# исключение из группы и удаления записи
@bot.message_handler(content_types=['left_chat_member'])
def handle_bot_removed(message):
    if message.left_chat_member.id == bot.get_me().id:
        group_id = message.chat.id
        try:
            group = Groups.objects.get(group_id=group_id)
            group.delete()

        except Groups.DoesNotExist:
            pass


# группы в суппергруппы
@bot.message_handler(content_types=['new_chat_members', 'migrate_to_chat_id', 'migrate_from_chat_id'])
def handle_group_id_change(message):
    chat_id = message.chat.id

    # событие migrate_to_chat_id означает, что группа преобразована в супергруппу и ID изменился
    if message.migrate_to_chat_id:
        new_chat_id = message.migrate_to_chat_id
        old_chat_id = chat_id
        try:
            group = Groups.objects.get(group_id=old_chat_id)
            group.group_id = new_chat_id
            group.save()
            bot.send_message(new_chat_id, f"ID группы был изменён на {new_chat_id}")

        except Groups.DoesNotExist:
            pass
        except Exception as e:
            pass

    # событие migrate_from_chat_id , что это старая группа, откуда был мигрирован чат
    elif message.migrate_from_chat_id:
        old_chat_id = message.migrate_from_chat_id
        new_chat_id = chat_id
        try:
            group = Groups.objects.get(group_id=old_chat_id)
            group.group_id = new_chat_id
            group.save()

        except Groups.DoesNotExist:
            pass
        except Exception as e:
            pass
