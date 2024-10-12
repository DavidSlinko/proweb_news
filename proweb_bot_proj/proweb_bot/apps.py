from django.apps import AppConfig
import logging


class ProwebBotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proweb_bot'

    def ready(self):
        import proweb_bot.signals


