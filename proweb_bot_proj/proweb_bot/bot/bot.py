import logging
import telebot
from django.db.models.signals import post_save
from django.dispatch import receiver
from telebot import types
from django.conf import settings
from proweb_bot.models import CustomUser, AdminUser, Groups, GroupsCategory
from proweb_bot.translations import translations

bot = telebot.TeleBot(settings.TG_BOT_TOKEN, parse_mode=None)
telebot.logger.setLevel(logging.DEBUG)


def set_webhook():
    webhook_url = f"https://cfb0-192-166-230-205.ngrok-free.app/webhook/"
    bot.set_webhook(url=webhook_url)


set_webhook()

logging.basicConfig(level=logging.INFO)


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
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    # добавляем на нее кнопки
    support = types.InlineKeyboardButton(text="Тех. поддержка", url='t.me/itsmylifestyle')
    coworking = types.InlineKeyboardButton(text="Коворкинг", url='t.me/proweb_coworking')
    keyboard.add(support, coworking)

    competitions = types.InlineKeyboardButton(text="Конкурсы🎉", callback_data='competitions')
    web_site = types.InlineKeyboardButton(text="Посетить сайт", url='proweb.uz')
    keyboard.add(competitions, web_site)

    well = types.InlineKeyboardButton(text="Базовый курс", callback_data='well')
    review = types.InlineKeyboardButton(text="Оствить отзыв", callback_data='review')
    keyboard.add(well, review)

    rules = types.InlineKeyboardButton(text="Правила обучения", callback_data="rules")
    keyboard.add(rules)

    

    if message.contact:
        try:
            user = CustomUser.objects.get(username_tg=message.from_user.username)
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

    show_admin_panel(chat_id)


def show_admin_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_send_messages = types.KeyboardButton("📩 Сделать рассылку по пользователям")
    button_view_courses = types.KeyboardButton("📚 Выбрать курсы для рассылки")
    markup.add(button_send_messages, button_view_courses)
    bot.send_message(chat_id, "Панель администратора👇", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "📩 Сделать рассылку по пользователям")
def handle_broadcast_to_users(message):
    chat_id = message.chat.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_ru = types.KeyboardButton('Рус🇷🇺')
    button_uz = types.KeyboardButton('Uzb🇺🇿')
    button_all = types.KeyboardButton('Отправить всем')
    markup.add(button_ru, button_uz)
    markup.add(button_all)

    bot.send_message(chat_id, 'Выберите язык интерфайса пользователей', reply_markup=markup)


lang_button = {}


@bot.message_handler(func=lambda message: message.text in ['Рус🇷🇺', 'Uzb🇺🇿', 'Отправить всем'])
def lang(message):
    chat_id = message.chat.id
    info_button = message.text

    # Сохраняем выбранный язык или опцию "Отправить всем"
    lang_button[chat_id] = {
        'info_button': info_button
    }

    bot.send_message(chat_id, "Введите сообщение для рассылки по выбранным пользователям:")
    bot.register_next_step_handler(message, send_broadcast_to_all_users)


def send_broadcast_to_all_users(message):
    chat_id = message.chat.id
    broadcast_text = message.text
    selected_language = lang_button[chat_id]['info_button']

    if selected_language == 'Рус🇷🇺':
        users = CustomUser.objects.filter(is_admin=False, language='ru')
    elif selected_language == 'Uzb🇺🇿':
        users = CustomUser.objects.filter(is_admin=False, language='uz')
    else:
        users = CustomUser.objects.filter(is_admin=False)

    total_users = users.count()
    success_count = 0
    failed_count = 0

    for user in users:
        try:
            bot.send_message(user.tg_id, broadcast_text)
            success_count += 1
        except Exception as e:
            failed_count += 1

    bot.send_message(chat_id,
                     f'Отправлено успешных сообщений: {success_count}/{total_users}\n'
                     f'Не удалось отправить: {failed_count} сообщений.')
    show_admin_panel(chat_id)


@bot.message_handler(func=lambda message: message.text == '📚 Выбрать курсы для рассылки')
def category(message):
    chat_id = message.chat.id

    courses = GroupsCategory.objects.all()

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for course in courses:
        markup.add(types.KeyboardButton(course.category_name))

    markup.add(types.KeyboardButton("Далее"))

    bot_data[chat_id] = {"selected_courses": []}

    bot.send_message(chat_id, "Выберите один или несколько курсов и нажмите 'Далее'", reply_markup=markup)


bot_data = {}
photo_list = []

@bot.message_handler(func=lambda message: message.text in [cat.category_name for cat in GroupsCategory.objects.all()])
def handle_course_selection(message):
    chat_id = message.chat.id
    selected_course = message.text

    if "selected_courses" in bot_data[chat_id]:
        if selected_course not in bot_data[chat_id]["selected_courses"]:
            bot_data[chat_id]["selected_courses"].append(selected_course)
            bot.send_message(chat_id, f"Курс '{selected_course}' добавлен к выбранным.")
        else:
            bot.send_message(chat_id, f"Курс '{selected_course}' уже выбран.")
    else:
        bot.send_message(chat_id, "Произошла ошибка, начните заново с команды /choose_courses.")


@bot.message_handler(func=lambda message: message.text == "Далее")
def handle_next_step(message):
    chat_id = message.chat.id
    selected_courses = bot_data[chat_id].get("selected_courses", [])

    if not selected_courses:
        bot.send_message(chat_id, "Вы не выбрали ни одного курса. Пожалуйста, выберите хотя бы один курс.")
        return

    choose_language(chat_id)


def choose_language(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("РУС"), types.KeyboardButton("UZB"), types.KeyboardButton("Разослать всем"))

    bot.send_message(chat_id, "Выберите язык для рассылки:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ["РУС", "UZB", "Разослать всем"])
def handle_language_selection(message):
    chat_id = message.chat.id
    selected_language = message.text

    if chat_id in bot_data:
        if "selected_courses" in bot_data[chat_id]:
            selected_courses = bot_data[chat_id]["selected_courses"]

            print(f"Фильтрация групп по курсам: {selected_courses}, язык: {selected_language}")

            groups = Groups.objects.none()

            if selected_language == "Разослать всем":
                for course in selected_courses:
                    groups = groups | Groups.objects.filter(category__category_name=course)
            else:
                for course in selected_courses:
                    groups = groups | Groups.objects.filter(category__category_name=course,
                                                            language=selected_language)

            if groups.exists():
                bot_data[chat_id]["selected_language"] = selected_language
                bot_data[chat_id]["groups"] = groups  # Сохраняем группы для дальнейшей рассылки

                bot.send_message(chat_id,
                                 f"Введите текст сообщения для рассылки по группам с языком '{selected_language}'")
            else:
                bot.send_message(chat_id, "Не найдено групп для рассылки на выбранном языке.")
        else:
            bot.send_message(chat_id, "Ошибка: выбранная категория не найдена. Пожалуйста, выберите категорию заново.")
    else:
        bot.send_message(chat_id, "Ошибка: данные не найдены. Начните сначала.")


@bot.message_handler(content_types=['photo', 'text'])
def handle_initial_message(message):
    chat_id = message.chat.id

    if chat_id not in bot_data or "selected_language" not in bot_data[chat_id]:
        bot.send_message(chat_id, "Сначала выберите язык.")
        return

    if message.content_type == 'photo':
        #photo_id = message.photo[-1].file_id

        if message.photo[-1].file_id not in photo_list:
            photo_list.append(message.photo[-1].file_id)


        caption = message.caption or ""

        print(f'инфа по фоткам {photo_list}')

        handle_broadcast_message(chat_id, photo_list, caption)

    elif message.content_type == 'text':
        handle_broadcast_message(chat_id, None, message.text)


@bot.message_handler(
    func=lambda message: message.chat.id in bot_data and "selected_language" in bot_data[message.chat.id])
def handle_broadcast_message(chat_id, media, broadcast_text):
    groups = bot_data[chat_id].get("groups", [])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_back = types.KeyboardButton('↩️Вернуться к выбору курсов')
    markup.add(button_back)

    if groups:
        for group in groups:
            try:
                if media:
                    bot.send_media_group(group.group_id, photo_list, broadcast_text)
                else:
                    bot.send_message(group.group_id, broadcast_text)

            except Exception as e:
                pass

        bot.send_message(chat_id,
                         f"Сообщение успешно разослано по {len(groups)} группам.")
        #del bot_data[chat_id]
        show_admin_panel(chat_id)
    else:
        bot.send_message(chat_id, "Не найдено групп для рассылки на выбранном языке.")


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
