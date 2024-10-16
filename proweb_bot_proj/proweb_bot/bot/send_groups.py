from telebot import types
from proweb_bot.models import CustomUser
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .bot_instance import bot
from proweb_bot.translations import translations
from proweb_bot.models import CustomUser, AdminUser, Groups, GroupsCategory, Posts, MediaPost, GroupPost

bot_data = {}
broadcast_data = {}


def choose_language(message):
    try:
        user = CustomUser.objects.get(username_tg=message.from_user.username)
    except CustomUser.DoesNotExist:
        bot.send_message(message.chat.id, "Пользователь не найден.")
        return

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


def category(message):
    chat_id = message.chat.id
    courses = GroupsCategory.objects.all()
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for course in courses:
        markup.add(types.KeyboardButton(course.category_name))

    markup.add(types.KeyboardButton("Далее"))
    bot_data[chat_id] = {"selected_courses": []}
    bot.send_message(chat_id, "Выберите один или несколько курсов и нажмите 'Далее'", reply_markup=markup)


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


def handle_next_step(message):
    chat_id = message.chat.id
    selected_courses = bot_data[chat_id].get("selected_courses", [])

    if not selected_courses:
        bot.send_message(chat_id, "Вы не выбрали ни одного курса. Пожалуйста, выберите хотя бы один курс.")
        return

    choose_languages(chat_id)  # Исправлено на вызов функции для выбора языка


def choose_languages(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("РУС"), types.KeyboardButton("UZB"), types.KeyboardButton("Разослать всем"), )

    bot.send_message(chat_id, "Выберите язык для рассылки:", reply_markup=markup)


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


def mail(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Пришлите сюда сообщение, которое хотите переслать в группы')


# def handle_forwarding(message):
#     from .bot import show_admin_panel
#     chat_id = message.chat.id

# Проверяем, сохранены ли данные о группах для рассылки
# if chat_id in bot_data and "groups" in bot_data[chat_id]:
#     groups = bot_data[chat_id]["groups"]  # Получаем группы для рассылки
#
#     if groups.exists():
#         # Пересылаем сообщение во все группы
#         for group in groups:
#             try:
#                 bot.forward_message(group.group_id, chat_id, message.message_id)
#             except Exception as e:
#                 bot.send_message(chat_id, f"Ошибка при пересылке в группу {group.group_id}: {e}")
#
#     else:
#         bot.send_message(chat_id, "Не найдено групп для рассылки.")
#     bot.send_message(chat_id, f"Сообщение успешно переслано по {len(groups)} группам.")
#     show_admin_panel(chat_id)

# else:
#     bot.send_message(chat_id, "Ошибка: сначала выберите курсы и язык для рассылки.")

# выбор
def handle_initial_message(message):
    from .bot import show_admin_panel
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


# ОТПРАВКА
def send_broadcast(message):
    from .bot import show_admin_panel
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
                formatted_text = broadcast_text

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


def cancel_broadcast(message):
    chat_id = message.chat.id
    if chat_id in broadcast_data:
        broadcast_data.pop(chat_id)
        bot.send_message(chat_id, "Отправка сообщения была отменена.")
    else:
        bot.send_message(chat_id, "Нет данных для отмены.")


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
