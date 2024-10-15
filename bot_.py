import telebot
from telebot import types

token = "7242746752:AAFR4ewWStQK0xhUEa_3ty5-6B8pmX6emaM"
bot = telebot.TeleBot(token=token)


@bot.message_handler(commands=["start"])
def repeat_all_messages(message):
    chat_id = message.chat.id
    text = '''Данный бот разработан специально для студентов центра PROWEB.\n
Возможности бота:\n
▪️ Отправить текстовое сообщение - задать любой вопрос, связанный с вашим обучением, и получить обратную связь в ближайшее время.\n        
▪️ Тех. поддержка - связаться с технической поддержкой и решить вопросы, связанные с компьютерной техникой. Также можно получить консультацию и помощь в сборке личного комьютера.\n            
▪️ Коворкинг - связаться с коворкинг администратором и забронировать место на посещение.\n            
▪️ Конкурсы - принять участие в ежемесечных конкурсах, где можно выиграть ценные призы.\n           
▪ Посетить сайт - переход на страницу центра PROWEB, где вы найдете всю подробную информацию о центре и о доступных курсах.\n            
▪ Базовый курс - записаться на бесплатный базовый курс компьютерной грамотности.\n           
▪️ Оставить отзыв - возможность поделиться приятными впечетлениями об обучении в центре PROWEB. Если вы столкнулись с трудностями, можно оставить жалобу или пожелание. Мы благодарны каждому отзыву.\n            
▪ Правила обучения - подробная информация о правилах обучения в центре PROWEB.\n            
▪ На главную - возможность вернуться на главную страницу бота и увидеть все его возможности.\n            
▪ O'zbek tili - переключение языка с русского на узбекский.\n           
▪ Поделиться контактом - если ваш вопрос имеет личный характер, оставьте свои данные и администрация центра свяжется с вами лично в ближайшее время.'''

    bot.send_message(chat_id, 'Вас приветствует центр современных профессий PROWEB! 🤗')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn_ru = types.KeyboardButton('Русский язык🇷🇺')
    btn_uzb = types.KeyboardButton('Узбекский язык🇺🇿')
    markup.add(btn_ru, btn_uzb)
    bot.send_message(chat_id, 'Выберите язык', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def uzb_ru(message):
    chat_id = message.chat.id

    if (message.text == 'Русский язык🇷🇺')
        pass

    else:
        pass

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

    bot.send_message(chat_id, text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "support":
            bot.send_message(call.message.chat.id, "Вы нажали на первую кнопку.")
        if call.data == "competitions":
            bot.send_message(call.message.chat.id, "Вы нажали на вторую кнопку.")


bot.polling(none_stop=True)
