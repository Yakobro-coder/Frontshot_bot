from telebot.async_telebot import AsyncTeleBot
import asyncio
from telebot import types
from celery_screenshot_tasks import screen_create
from postgres_stat import insert_db
from datetime import datetime
import validators
import whois
import socket
import logging
import os

from dotenv import load_dotenv
load_dotenv()

import re
url_pattern_regex = '(([\da-zA-Z])([_\w-]{,62})\.){,127}(([\da-zA-Z])[_\w-]{,61})?([\da-zA-Z]\.((xn\-\-[a-zA-Z\d]+)|([a-zA-Z\d]{2,})))'

logging.basicConfig(filename='bot_log', level=logging.INFO)

bot = AsyncTeleBot(os.getenv('TOKEN'))

start_text = """👋🏻 Привет! Меня зовут <b>FrontShot.</b>
Я - Бот для создания веб-скриншотов.
Чтобы получить скриншот - отправьте URL адрес сайта. Например, wikipedia.org

• С помощью бота вы можете проверять подозрительные ссылки. <i>(Айпилоггеры, фишинговые веб-сайты, скримеры и т.п)</i>

• Вы также можете добавить меня в свои чаты, и я смогу проверять ссылки, которые отправляют пользователи.

 <b>FrontShot</b> использует <b>chromedriver.</b>
Работает с протоколами <b>http, https.</b>

<s>И находится в постоянной разработке.</s>"""

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_start = types.KeyboardButton('/start')
markup.add(btn_start)


@bot.message_handler(commands=['start', 'help'])
async def start_message(message):
    await bot.send_message(message.chat.id, start_text, parse_mode="HTML", reply_markup=markup)


@bot.message_handler(content_types='text')
async def screenshot_url(message):
    """
    Получив сообщение, проверяет что это URL и передаёт необходимые данные для создания снимка сайта в celery.
    :param message: инфо о сообщении.
    :return: None
    """
    url = re.search(url_pattern_regex, message.text.split(' ')[0]).group(0)
    if validators.domain(url):
        # write in db
        insert_db.insert_msg_info(message.from_user.id, message.id, datetime.utcfromtimestamp(message.date + 10800), url)

        url = 'http://' + url
        res = await bot.send_animation(
            chat_id=message.chat.id,
            animation=open('please-wait.mp4', 'rb'),
            caption="⚡️Ваш запрос обрабатывается..."
        )
        info_msg = {'date': res.date, 'chat_id': res.chat.id, 'message_id': res.message_id}

        # Отправка в задачу celery, через redis
        screen_create.delay(info_msg, url)


@bot.callback_query_handler(func=lambda call: True)
async def whois_msg(message):
    """
    Функция обрабатывает нажатие по кнопке "Подробнее" и отображает WHOIS о полученной ссылке в сообщении.
    :param message: инфо о сообщении.
    :return: None
    """
    whois_info = whois.whois(message.data)
    ip_who = socket.gethostbyname(whois_info.get('domain_name') if isinstance(whois_info.get('domain_name'), str) else
                                  whois_info.get('domain_name')[0])

    msg = f"ip: {str(ip_who)}\n" \
          f"Имя домена: {whois_info.get('domain_name')}\n" \
          f"Организация: {whois_info.get('org')}\n" \
          f"Страна: {whois_info.get('country')}"

    await bot.answer_callback_query(callback_query_id=message.id, text=msg, show_alert=True)


asyncio.run(bot.polling(non_stop=True))
