from telebot import types
# from proweb_bot.models import
from .bot_instance import bot
from ..models import UserPost, CustomUser

bot_data = {}
lang_button = {}
broadcast_data = {}


def handle_broadcast_to_users(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_ru = types.KeyboardButton('Рус🇷🇺')
    button_uz = types.KeyboardButton('Uzb🇺🇿')
    button_all = types.KeyboardButton('Отправить всем')
    markup.add(button_ru, button_uz)
    markup.add(button_all)

    bot.send_message(chat_id, 'Выберите язык интерфейса пользователей', reply_markup=markup)


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
    from .bot import show_admin_panel
    chat_id = message.chat.id
    if chat_id in broadcast_data:
        users = CustomUser.objects.filter(is_admin=False)  # Получаем всех пользователей, которые не администраторы
        posts = broadcast_data[chat_id]['posts']

        if not posts:
            bot.send_message(chat_id, "Нет постов для рассылки.")
            return

        success_count = 0
        failed_count = 0

        for user in users:
            for post_data in posts:
                media_group = post_data.get('media', [])
                broadcast_text = post_data.get('text', '')

                # Создаем новый пост
                post_instance = Posts.objects.create(text_post=broadcast_text)

                try:
                    if media_group:
                        # Отправляем медиа-группу (альбом)
                        sent_media_group = bot.send_media_group(user.tg_id, media_group)
                        for sent_message in sent_media_group:
                            UserPost.objects.create(post=post_instance, user=user,
                                                    message_id=sent_message.message_id)
                            post_instance.users.add(user)

                        # Отправляем текст (описание) отдельно после альбома, если оно есть
                        if broadcast_text:
                            sent_message = bot.send_message(user.tg_id, broadcast_text, parse_mode='MarkdownV2')
                            UserPost.objects.create(post=post_instance, user=user,
                                                    message_id=sent_message.message_id)
                            post_instance.users.add(user)
                    else:
                        # Отправляем только текст, если нет медиа
                        sent_message = bot.send_message(user.tg_id, broadcast_text, parse_mode='MarkdownV2')
                        UserPost.objects.create(post=post_instance, user=user,
                                                message_id=sent_message.message_id)
                        post_instance.users.add(user)

                    success_count += 1  # Успешно отправлено
                except Exception as e:
                    failed_count += 1  # Ошибка отправки
                    bot.send_message(chat_id, f"Ошибка при рассылке пользователю {user.tg_id}: {e}")

        # Информируем администратора о результатах рассылки
        bot.send_message(chat_id,
                         f"Сообщение успешно разослано {success_count} пользователям.\n"
                         f"Не удалось отправить: {failed_count} сообщений.")
        show_admin_panel(chat_id)

        broadcast_data.pop(chat_id)  # Удаляем данные после рассылки
    else:
        bot.send_message(chat_id, "Нет данных для отправки.")



