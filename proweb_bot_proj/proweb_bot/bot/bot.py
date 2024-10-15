import logging
import telebot
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from telebot import types
from django.conf import settings
from proweb_bot.models import CustomUser, AdminUser, Groups, GroupsCategory
from proweb_bot.translations import translations




def set_webhook():
    webhook_url = f"https://cfb0-192-166-230-205.ngrok-free.app/webhook/"
    bot.set_webhook(url=webhook_url)


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


    show_admin_panel(chat_id)


def show_admin_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_send_messages = types.KeyboardButton("📩 Сделать рассылку")
    button_view_courses = types.KeyboardButton("📚 Выбрать курсы")
    markup.add(button_send_messages, button_view_courses)
    bot.send_message(chat_id, "Панель администратора:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '📚 Выбрать курсы')
def category(message):
    chat_id = message.chat.id
    get_category = GroupsCategory.objects.all()
    if get_category.exists():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        for cat in get_category:
            button = types.KeyboardButton(cat.category_name)
            markup.add(button)

        bot.send_message(chat_id, 'Выберите категорию:', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Категории не найдены.')


bot_data = {}


@bot.message_handler(func=lambda message: message.text in [cat.category_name for cat in GroupsCategory.objects.all()])
def handle_category_selection(message):
    chat_id = message.chat.id
    selected_category_name = message.text  # Сохраняем выбранную категорию

    # Получаем группы по выбранной категории
    groups = Groups.objects.filter(category__category_name=selected_category_name)

    if groups.exists():
        # Сохраняем категорию в bot_data
        bot_data[chat_id] = {
            "selected_category": selected_category_name
        }

        # Создаем кнопки для выбора языка
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_ru = types.KeyboardButton("РУС")
        button_uzb = types.KeyboardButton("UZB")
        button_all = types.KeyboardButton('Разослать всем')
        markup.add(button_ru, button_uzb, button_all)

        bot.send_message(chat_id, f"Группы в категории '{selected_category_name}':", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Группы не найдены для этой категории.")


@bot.message_handler(func=lambda message: message.text in ["РУС", "UZB", "Разослать всем"])
def handle_language_selection(message):
    chat_id = message.chat.id
    selected_language = message.text

    if chat_id in bot_data:
        selected_category = bot_data[chat_id]["selected_category"]

        if selected_language == "Разослать всем":
            groups = Groups.objects.filter(category__category_name=selected_category)
        else:
            groups = Groups.objects.filter(category__category_name=selected_category, language=selected_language)

        bot_data[chat_id]["selected_language"] = selected_language
        bot_data[chat_id]["groups"] = groups  # Сохраняем группы для дальнейшей рассылки

        bot.send_message(chat_id, f"Введите текст сообщения для рассылки по группам с языком '{selected_language}'")
    else:
        bot.send_message(chat_id, "Ошибка: данные категории не найдены. Начните сначала.")






@bot.message_handler(func=lambda message: message.chat.id in bot_data and "selected_language" in bot_data[message.chat.id])
def handle_broadcast_message(message):
    chat_id = message.chat.id
    groups = bot_data[chat_id].get("groups", [])

    # Проверяем тип сообщения
    if message.content_type == 'text':
        broadcast_text = message.text
        media = None
    elif message.content_type == 'photo':
        broadcast_text = message.caption or ""  # Подпись к фото, если есть
        media = message.photo[-1].file_id  # Получаем последнюю и самую большую версию фото
    else:
        bot.send_message(chat_id, "Пожалуйста, отправьте текст или фото для рассылки.")
        return

    # Лог для проверки
    if media:
        print(f'Отправка фото {media} с текстом "{broadcast_text}"')
    else:
        print(f'Отправка текста: "{broadcast_text}"')

    # Проверка на наличие групп
    if groups.exists():
        for group in groups:
            try:
                # Если есть фото, отправляем его с текстом (или без текста)
                if media:
                    bot.send_photo(group.group_id, photo=media, caption=broadcast_text)
                else:
                    bot.send_message(group.group_id, broadcast_text)

                print(f"Сообщение отправлено в группу: {group.name_group}")  # Для отладки
            except Exception as e:
                print(f"Ошибка отправки в группу {group.name_group}: {e}")

        # Сообщение о завершении рассылки
        bot.send_message(chat_id, f"Сообщение успешно разослано по {len(groups)} группам с языком '{bot_data[chat_id]['selected_language']}'.")
        del bot_data[chat_id]  # Очищаем данные после рассылки
    else:
        bot.send_message(chat_id, "Не найдено групп для рассылки на выбранном языке.")


    # Очищаем данные после рассылки


# добавление группы в модель
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
