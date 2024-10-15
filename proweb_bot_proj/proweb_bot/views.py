import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from telebot import types
from proweb_bot.bot.bot import bot

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        # logging.info(f"Webhook received: {request.body}")
        try:
            json_str = request.body.decode('UTF-8')
            update = types.Update.de_json(json_str)
            # logging.info(f"Обрабатываем обновление: {update}")
            bot.process_new_updates([update])
        except Exception as e:
            logging.error(f"Ошибка обработки вебхука: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'not allowed'})

