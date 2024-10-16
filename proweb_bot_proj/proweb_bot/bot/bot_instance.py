import telebot
from django.conf import settings
bot = telebot.TeleBot(settings.TG_BOT_TOKEN, parse_mode=None)
