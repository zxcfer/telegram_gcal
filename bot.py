from unittest.mock import call
from flask import jsonify
import requests
import os
import json
from decouple import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update


# API_KEY = config('API_KEY')
serverdomain = config('DOMAIN')
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
TOKEN = config('TOKEN')
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

session = requests.Session()
session.verify = False

def start(update, context):
    session = requests.Session()
    session.verify = False
    
    print(session.get("https://jsonplaceholder.typicode.com/todos/1").json())
    update.message.reply_text('Hello welcome to google calender bot')

def gcalauth(update, context):
    username = update['message']['chat']['username']
    chatid = update['message']['chat']['id']

    authlink = f"{serverdomain}/authorize?username={username}&chatid={chatid}"
    update.message.reply_text(f'Please visit {authlink} to authorize your Google calender')


def schedule(update, context):
    print("SCHEDULE")
    username = update['message']['chat']['username']
    msg = update['message']['text']
    text = msg.replace('/sc', '')
    context.user_data['message'] = text
    context.user_data['user'] = username

    url = f"{serverdomain}/getuserinfo"
    payload = json.dumps({
        "username": username
    })
    headers = {
        'Content-Type': 'application/json'
    }

    print("Response Will be here", url, headers)
    
    session = requests.Session()
    session.verify = False
    
    # response = session.get(url, headers=headers, data=payload).json()
    response = session.get(url, headers=headers, data=payload, timeout=5).json()
    print("Response", response)
    
    
    if response['data'] == None:

        update.message.reply_text('use the /auth to authorize your google calender before using this command')
    else:
        url = f"{serverdomain}/getcals"
        payload = json.dumps({
            "username": username
        })
        headers = {
            'Content-Type': 'application/json'
        }

        print("Response Will be here to get user cal", url, payload, headers)
        session = requests.Session()
        session.verify = False
    
        response = session.get(url, headers=headers, data=payload, timeout=5).json()

        keyboard = []
        print("="*100)
        # print("This respose is from the calendar: ",jsonify(response))
        print("="*100)
        for i in response['items']:
            print(i['id'],"---------",i['summary'])
            if i['accessRole'] == 'owner':
                keyboard.append([InlineKeyboardButton(i['summary'], callback_data=i['id'])])
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text('Select a calendar to add:', reply_markup=reply_markup)

        
def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    username = context.user_data['user']
    text = context.user_data['message']
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    print("\n\n\nThe  big Query:", query)
    # query.edit_message_text(text=f"Selected option: {query.data} ")

    url = f"{serverdomain}/setcalender"
    payload = json.dumps({
        "username": username,
        "message": text,
        'calendarId': query.data
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = session.get(url, headers=headers, data=payload, timeout=10).json()
    print('Passed')
    htmlLink = response['htmllink']
    # print("response else", response.text)
    query.edit_message_text(text=f'Event scheduled successfully {htmlLink}')

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
    dp.add_handler(CommandHandler("auth", gcalauth))
    dp.add_handler(CommandHandler("sc", schedule))
    dp.add_handler(CommandHandler("schedule", schedule))
    dp.add_handler(CallbackQueryHandler(button))

    # log all errors
    # dp.add_error_handler(error)

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
