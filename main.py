import asyncio
import os
import time

import threading

import telegram

from telegram import *
from telegram.constants import ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, Application
from selenium import webdriver
import uuid
from jinja2 import Template
from pyvirtualdisplay import Display
import logging

import config
from db import *

token = config.Environment.token
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger("httpx").setLevel(logging.WARNING)

bot: telegram.Bot


def create_img(path):
    with Display(size=(1920 * 2, 1024 * 2)):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument("--headless")

        driver = webdriver.Chrome(options=options)
        driver.get(f'file:////{path}.html')

        main_element = driver.find_element("css selector", '.main')
        main_width = int(main_element.size['width'])
        main_height = int(main_element.rect['height'])

        driver.set_window_size(int(main_width * 100 / 45 * 2), int(main_height * 1.05 * 2))

        driver.save_screenshot(f"{path}.png")

        driver.quit()


async def create(update: Update, context: CallbackContext) -> None:
    messages = get_all_tasks(update.message.chat.id)

    try:
        bg = get_chat_bg(update.message.chat_id)
    except IndexError:
        await update.message.reply_text(text="Пожалуйста, вызовите /start для инициализации бота.")
        return

    if len(messages) == 0:
        await update.message.reply_text(
            text="База данных пуста.\nСкорее всего вы не прислали мне никаих сообщений")
        return

    await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)

    output = Template(open(config.Environment.index_path, 'r').read()).render(messages=messages, bg=bg,
                                                                              host=config.Environment.flask_path)

    path = f"{config.Environment.temp_path}/{uuid.uuid4()}"
    open(f"{path}.html", 'w').write(output)

    create_img(path)

    try:
        await update.message.reply_photo(photo=open(f'{path}.png', 'rb'),
                                         caption="Вот фотография.")
        await update.message.reply_document(document=open(f'{path}.png', 'rb'), caption="Вот файл.")
    except telegram.error.BadRequest as e:
        await update.message.reply_document(document=open(f'{path}.png', 'rb'),
                                            caption="Фотка слишком "
                                                    "большая для "
                                                    "телеграма, "
                                                    "так что вот "
                                                    "только файл.")
        logging.error(f"Bad request {e.message}")
        os.remove(f"{path}.html")
        return

    clear_all_tasks(update.message.chat.id)

    os.remove(f"{path}.html")
    os.remove(f"{path}.png")


async def message_handler(update: Update, context: CallbackContext) -> None:
    logging.info(f"Got message from {update.message.from_user.username}")

    forwarded_message: MessageOrigin | None = update.message.forward_origin
    if forwarded_message is not None:
        forwarded_message = forwarded_message.sender_user
        user_id = forwarded_message.id
        username = forwarded_message.first_name
    else:
        user_id = update.message.from_user.id
        username = update.message.from_user.first_name

    photos = await context.bot.get_user_profile_photos(user_id=user_id)

    if photos.photos:
        photo = photos.photos[0][-1]
        file = await context.bot.get_file(photo.file_id)
        file_url = file.file_path
        insert_task(update.message.chat.id, username, file_url, update.message.text)
    else:
        await update.message.reply_text(reply_to_message_id=update.message.message_id,
                                        text="У владельца этого сообщения либо скрыта аватарка, либо её нет.\nНа фотографии "
                                             "будет болванка.")
        insert_task(update.message.chat.id, username, f"http://{config.Environment.flask_path}/bg/ava.png",
                    update.message.text)


async def photo_handler(update: Update, context: CallbackContext) -> None:
    chat = get_chat(update.message.chat_id)

    if chat[4]:
        file_id = update.message.photo[-1].file_id

        file_obj = await context.bot.get_file(file_id)

        photo_path = f"{config.Environment.bg_path}/{update.message.chat.id}.jpg"

        await file_obj.download_to_drive(photo_path)

        set_chat_back(update.message.chat_id, f"{update.message.chat.id}.jpg")

        await update.message.reply_text("Теперь в качестве заднего фона будет Ваша фотография.")


async def start(update: Update, context: CallbackContext):
    logging.info(f"Got '/start' from {update.message.from_user.username}")
    insert_chat(update.message.chat_id, update.message.chat.title)
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    await update.message.reply_text(
        text="Привет!\nЧтобы получить фотографию, тебе нужно переслать мне сообщения, а затем ввести команду "
             "/create. Тогда я пришлю тебе эти сообщения в виде скриншота (почти).\nСтандартно фон белый, "
             "но можно поставить любое другое изображение")


async def info(update: Update, context: CallbackContext):
    logging.info(f"Got '/info' from {update.message.from_user.username}")
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    await update.message.reply_text(
        text="Чтобы получить фотографию, тебе нужно переслать мне сообщения, а затем ввести команду "
             "/create. Тогда я пришлю тебе эти сообщения в виде скриншота (почти).\nСтандартно фон белый, "
             "но можно поставить любое другое изображение")


async def back(update: Update, context: CallbackContext):
    chat = get_chat(update.message.chat_id)

    if chat[3] != "def":
        await update.message.reply_photo(photo=open(f'{config.Environment.bg_path}/{chat[3]}', 'rb'),
                                         caption="Сейчас у вас такой задний фон.")
    else:
        await update.message.reply_text(text='У вас стандартный (белый) задний фон.')


async def change_back(update: Update, context: CallbackContext):
    logging.info(f"Got '/back' from {update.message.from_user.username}")
    set_chat_waiting(update.message.chat_id, True)
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    await update.message.reply_text(
        text="Сейчас отправьте мне фотографию, которую Вы хотите иметь в качестве заднего фона на ваших "
             "фотографиях.")


async def empty_back(update: Update, context: CallbackContext) -> None:
    logging.info(f"Got '/empty' from {update.message.from_user.username}")
    set_chat_waiting(update.message.chat_id, True)
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    set_chat_back(update.message.chat_id, "def")
    await update.message.reply_text(
        text="Теперь у Вас задний фон стандартый (белый).")


def main() -> None:
    global bot
    bot = Application.builder().token(token).build()

    bot.add_handler(CommandHandler('start', start))
    bot.add_handler(CommandHandler('info', info))
    bot.add_handler(CommandHandler("create", create))
    bot.add_handler(CommandHandler("back", back))
    bot.add_handler(CommandHandler("change", change_back))
    bot.add_handler(CommandHandler("empty", empty_back))
    bot.add_handler(MessageHandler(filters=filters.TEXT, callback=message_handler))
    bot.add_handler(MessageHandler(filters=filters.PHOTO, callback=photo_handler))

    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    init()
    main()
