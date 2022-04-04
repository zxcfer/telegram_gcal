import requests
import os
import json
from decouple import config
token = config('TOKEN')
API_KEY = config('API_KEY')
serverdomain = config('DOMAIN')
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
TOKEN = token
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

session = requests.Session()
session.verify = False

def start(update, context):
    update.message.reply_text('Hello welcome to google calender bot')


def gcalauth(update, context):
    username = update['message']['chat']['username']
    chatid = update['message']['chat']['id']

    authlink = f"{serverdomain}/authorize?username={username}&chatid={chatid}"
    update.message.reply_text(f'visit this url to authorize your google calender {authlink}')


def schedule(update, context):
    print(update)
    username = update['message']['chat']['username']
    msg = update['message']['text']
    text = msg.replace('/sc', '')

    url = f"{serverdomain}/getuserinfo"
    payload = json.dumps({
        "username": username
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = session.get(url, headers=headers, data=payload).json()
    if response['data'] == None:
        update.message.reply_text('use the /gcalauth to authorize your google calender before using this command')
    else:
        url = f"{serverdomain}/setcalender"
        payload = json.dumps({
            "username": username,
            "message": text
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = session.get(url, headers=headers, data=payload).json()
        print(response)
        htmlLink = response['htmllink']
        update.message.reply_text(f'Appointment scheduled successfully, follow this link to check the appointment {htmlLink}')


def error(update, context):
    """Log Errors caused by Updates."""

def mainbot():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(CommandHandler("gcalauth", gcalauth))

    dp.add_handler(CommandHandler("sc", schedule))


    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    # updater.start_webhook(listen="0.0.0.0",
    #                       port=int(PORT),
    #                       url_path=TOKEN)
    # updater.bot.setWebhook('https://localhost' + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    mainbot()
