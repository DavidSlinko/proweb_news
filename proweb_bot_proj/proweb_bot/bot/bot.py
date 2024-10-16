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

bot = telebot.TeleBot(settings.TG_BOT_TOKEN, parse_mode=None)
telebot.logger.setLevel(logging.DEBUG)


def set_webhook():
    webhook_url = f"https://7ad7-192-166-230-205.ngrok-free.app/webhook/"
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
def choose_language(message):
    user = CustomUser.objects.get(username_tg=message.from_user.username)

    if message.text == "Русский язык 🇷🇺":
        user.language = 'ru'
    elif message.text == "O'zbek tili 🇺🇿":
        user.language = 'uz'

    user.save()

    bot.send_message(message.chat.id, translations[user.language]['btn_send_phone'])

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
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
    markup.add(types.KeyboardButton("РУС"), types.KeyboardButton("UZB"), types.KeyboardButton("Разослать всем"), )

    bot.send_message(chat_id, "Выберите язык для рассылки:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ["РУС", "UZB", "Разослать всем"])
def handle_language_selection(message):
    chat_id = message.chat.id
    selected_language = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.InlineKeyboardButton('Переслать'))

    if chat_id in bot_data:
        if "selected_courses" in bot_data[chat_id]:
            selected_courses = bot_data[chat_id]["selected_courses"]
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
                                 f"Введите текст сообщения для рассылки по группам с языком '{selected_language}'",
                                 reply_markup=markup)
            else:
                bot.send_message(chat_id, "Не найдено групп для рассылки на выбранном языке.")
        else:
            bot.send_message(chat_id, "Ошибка: выбранная категория не найдена. Пожалуйста, выберите категорию заново.")
    else:
        bot.send_message(chat_id, "Ошибка: данные не найдены. Начните сначала.")


@bot.message_handler(func=lambda message: message.text == 'Переслать')
def mail(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Пришлите сюда сообщение, которое хотите переслать в группы')


@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'poll'])
def handle_forwarding(message):
    chat_id = message.chat.id

    # Проверяем, сохранены ли данные о группах для рассылки
    if chat_id in bot_data and "groups" in bot_data[chat_id]:
        groups = bot_data[chat_id]["groups"]  # Получаем группы для рассылки

        if groups.exists():
            # Пересылаем сообщение во все группы
            for group in groups:
                try:
                    bot.forward_message(group.group_id, chat_id, message.message_id)
                except Exception as e:
                    bot.send_message(chat_id, f"Ошибка при пересылке в группу {group.group_id}: {e}")

            bot.send_message(chat_id, f"Сообщение успешно переслано по {len(groups)} группам.")
            show_admin_panel(chat_id)
        else:
            bot.send_message(chat_id, "Не найдено групп для рассылки.")
    else:
        bot.send_message(chat_id, "Ошибка: сначала выберите курсы и язык для рассылки.")


@bot.message_handler(content_types=['text', 'photo', 'video', 'voice'])
def handle_initial_message(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_send = types.KeyboardButton('Отправить')
    button_cancel = types.KeyboardButton('Отмена')
    button_new_post = types.KeyboardButton('Новый пост')
    markup.add(button_send, button_cancel, button_new_post)

    if chat_id not in bot_data or "selected_language" not in bot_data[chat_id]:
        bot.send_message(chat_id, "Сначала выберите язык.")
        return

    # Инициализация записи для пользователя, если она ещё не создана
    if chat_id not in broadcast_data:
        broadcast_data[chat_id] = {
            'posts': []  # Список постов для хранения каждого поста
        }

    # Если пользователь отправил фото, видео или голосовое сообщение
    if message.content_type in ['photo', 'video', 'voice']:
        # Создаем новый пост, если его нет
        if not broadcast_data[chat_id]['posts']:
            broadcast_data[chat_id]['posts'].append({
                'media': [],
                'text': None
            })

        # Добавляем медиа в последний пост
        current_post = broadcast_data[chat_id]['posts'][-1]
        if message.content_type == 'photo':
            media = types.InputMediaPhoto(message.photo[-1].file_id, caption=message.caption or "")
        elif message.content_type == 'video':
            media = types.InputMediaVideo(message.video.file_id, caption=message.caption or "")
        elif message.content_type == 'voice':
            # Прямо добавляем ID голосового сообщения
            media = {'type': 'voice', 'file_id': message.voice.file_id}

        current_post['media'].append(media)
        print(f'Медиа добавлено: {current_post["media"]}')

        bot.send_message(chat_id, "Медиа добавлено. Напишите текст для рассылки или отправьте еще медиа.",
                         reply_markup=markup)

    elif message.content_type == 'text':
        if message.text == 'Отправить':
            if not broadcast_data[chat_id]['posts']:
                bot.send_message(chat_id, "Нет постов для отправки.")
                return
            send_broadcast(message)

        elif message.text == 'Отмена':
            cancel_broadcast(message)

        elif message.text == 'Новый пост':
            # Создаем новый пост
            broadcast_data[chat_id]['posts'].append({
                'media': [],
                'text': None
            })
            bot.send_message(chat_id, "Создан новый пост. Вы можете отправить медиа или текст.")

        else:
            # Проверяем, есть ли посты
            if not broadcast_data[chat_id]['posts']:
                # Если нет постов, создаем новый пост
                broadcast_data[chat_id]['posts'].append({
                    'media': [],
                    'text': message.text
                })
                bot.send_message(chat_id,
                                 "Текст добавлен в новый пост. Вы можете отправить ещё медиа или нажать 'Отправить'.",
                                 reply_markup=markup)
            else:
                current_post = broadcast_data[chat_id]['posts'][-1]
                current_post['text'] = message.text
                bot.send_message(chat_id, "Текст добавлен. Вы можете отправить ещё медиа или нажать 'Отправить'.",
                                 reply_markup=markup)


# Обработка команды "Отправить"
def send_broadcast(message):
    chat_id = message.chat.id
    if chat_id in broadcast_data:
        groups = bot_data[chat_id].get("groups", [])
        posts = broadcast_data[chat_id]['posts']

        if groups:
            if not posts:
                bot.send_message(chat_id, "Нет постов для рассылки.")
                return

            for post_data in posts:
                media_group = post_data.get('media', [])
                broadcast_text = post_data.get('text', '')

                # Форматируем текст для Telegram
                formatted_text = format_text_telegram(broadcast_text)

                # Создаем новый пост
                post_instance = Posts.objects.create(text_post=formatted_text)

                if media_group:
                    for media in media_group:
                        if isinstance(media, types.InputMediaPhoto):
                            MediaPost.objects.create(post=post_instance, photo=media.media)
                        elif isinstance(media, types.InputMediaVideo):
                            MediaPost.objects.create(post=post_instance, video=media.media)

                for group in groups:
                    try:
                        if media_group:
                            sent_media_group = bot.send_media_group(group.group_id, media_group)
                            for sent_message in sent_media_group:
                                GroupPost.objects.create(post=post_instance, group=group,
                                                         message_id=sent_message.message_id)
                                post_instance.groups.add(group)
                        else:
                            # Отправляем отформатированный текст с поддержкой всех стилей
                            sent_message = bot.send_message(group.group_id, formatted_text, parse_mode='MarkdownV2')
                            GroupPost.objects.create(post=post_instance, group=group,
                                                     message_id=sent_message.message_id)
                            post_instance.groups.add(group)

                        # Создаем инлайн-кнопки для удаления и закрепления поста
                        keyboard = InlineKeyboardMarkup()
                        delete_button = InlineKeyboardButton("Удалить пост", callback_data=f"delete_{post_instance.id}")
                        pin_button = InlineKeyboardButton("Закрепить пост", callback_data=f"pin_{post_instance.id}")
                        keyboard.add(delete_button, pin_button)

                    except Exception as e:
                        bot.send_message(chat_id, f"Ошибка при рассылке в группу {group.group_id}: {e}")

            bot.send_message(chat_id, f"Сообщение успешно разослано по {len(groups)} группам.", reply_markup=keyboard)
            show_admin_panel(chat_id)
        else:
            bot.send_message(chat_id, "Не найдено групп для рассылки на выбранном языке.")

        broadcast_data.pop(chat_id)
    else:
        bot.send_message(chat_id, "Нет данных для отправки.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('pin_') or call.data.startswith('delete_'))
def handle_post_actions(call):
    action, post_id_str = call.data.split('_', 1)  #

    post_id = int(post_id_str.replace('post_', ''))
    print(f"это список данных что мы получаем: {post_id}")
    post = Posts.objects.get(id=post_id)

    if action == 'pin':
        pin_post_in_groups(post)
        bot.answer_callback_query(call.id, "Пост закреплен.")
    elif action == 'delete':
        delete_post_from_groups(post)
        bot.answer_callback_query(call.id, "Пост удален.")


def pin_post_in_groups(post):
    group_posts = GroupPost.objects.filter(post=post)  # Получаем все записи о постах в группах
    for group_post in group_posts:
        try:
            # Закрепляем сообщение в группе
            bot.pin_chat_message(chat_id=group_post.group.group_id, message_id=group_post.message_id)
        except Exception as e:
            pass


def delete_post_from_groups(post):
    post_id = post.id
    posts = Posts.objects.filter(id=post_id)

    group_posts = GroupPost.objects.filter(post=post)

    for group_post in group_posts:
        try:
            # Удаляем сообщение в группе
            bot.delete_message(chat_id=group_post.group.group_id, message_id=group_post.message_id)
        except Exception as e:
            pass

    posts.delete()


# Обработка команды "Отмена"
def cancel_broadcast(message):
    chat_id = message.chat.id
    if chat_id in broadcast_data:
        broadcast_data.pop(chat_id)
        bot.send_message(chat_id, "Отправка сообщения была отменена.")
    else:
        bot.send_message(chat_id, "Нет данных для отмены.")


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
