from celery import Celery
from selenium import webdriver
from datetime import datetime
import telebot
from telebot import types
import logging
import os


from dotenv import load_dotenv
load_dotenv()

import re
url_pattern_regex = '(([\da-zA-Z])([_\w-]{,62})\.){,127}(([\da-zA-Z])[_\w-]{,61})?([\da-zA-Z]\.((xn\-\-[a-zA-Z\d]+)|([a-zA-Z\d]{2,})))'

logging.basicConfig(filename='celery_log', level=logging.INFO)
app = Celery('tasks', broker=os.getenv('BROKER_CELERY'))


@app.task
def screen_create(msg_info, url):
    """
    С помощью selenium через Chromedriver делает снимок сайта.

    :param msg_info: Данные о полученном сообщении от пользователя {chat_id, message_id, date(date received message)}
    :param url: URL полученный от пользователя
    :return: Возвратом вызывает функцию send_message_result() отправки\редактирования сообщения с фото сайта
    """
    start_time = datetime.now()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome(chrome_options=options)
    # Если выгрузка продлилась дольше 30 сек. то выдать ошибку
    driver.set_page_load_timeout(30)
    driver.set_window_size(1920, 1080)

    try:
        driver.get(url)
        url = driver.current_url
        domain = re.search(url_pattern_regex, url).group(9)
        domain_name = re.search(url_pattern_regex, url).group(0)

        filename = datetime.utcfromtimestamp(msg_info.get('date') + 10800).strftime('%H-%M-%S_%d-%m-%Y') + "_" + \
                   str(msg_info.get('chat_id')) + "_" + f'.{domain}' + '.png'

        screen_directory_save = f"save_screenshots_{datetime.now().strftime('%d-%m-%Y')}"
        if not os.path.exists(screen_directory_save):
            os.makedirs(screen_directory_save)
        driver.save_screenshot(f'./{screen_directory_save}/' + filename)
        title_site = driver.title
        driver.close()

        screen = f'./{screen_directory_save}/' + filename
        stop_time = (datetime.now() - start_time).seconds

        response = {
            'title': f"<b>{title_site}</b>",
            'screen': screen,
            'url': url,
            'processing_time': f"<b>Время обработки: </b>{stop_time} секунд",
            'chat_id': msg_info.get('chat_id'),
            'message_id': msg_info.get('message_id'),
            'domain_name': domain_name
        }
    except:
        logging.exception('exception')
        response = {
            'title': "Что то не так с ссылкой...\nПревышено время ожидания ответа.",
            'screen': './error.PNG',
            'url': url,
            'processing_time': '',
            'chat_id': msg_info.get('chat_id'),
            'message_id': msg_info.get('message_id'),
        }
    return send_message_result(response)


def send_message_result(screen):
    """
    Редактирует предыдущее сообщение пользователя с URL, добобляя фото сайта и кнопку "Подробнее" для получения
    whois об сайте.

    В случае какой либо ошибки, возвращает сообщение об ошибке. Бед whois.

    :param screen: Данные о сайте. {title:заголовок_сайта, screen:фото, url:ссылка,
    processing_time:время_выполния_проуесса, chat_id:id, message_id:id}
    :return: DONE!
    """
    bot = telebot.TeleBot(os.getenv('TOKEN'))

    markup = None
    if screen.get('domain_name') is not None:
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text="Подробнее", callback_data=screen.get('domain_name'))
        markup.add(button1)

    bot.edit_message_media(
        media=types.InputMediaPhoto(
            media=open(screen.get('screen'), 'rb'),
            caption=f"{screen.get('title')}\n\n<b>Веб-сайт: </b>{screen.get('url')}\n{screen.get('processing_time')}",
            parse_mode='HTML',
        ),
        chat_id=screen.get('chat_id'),
        message_id=screen.get('message_id'),
        reply_markup=markup,
    )

    return 'DONE!'
