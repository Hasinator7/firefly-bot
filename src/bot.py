#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards.
"""
import logging
import os
from pathlib import Path
from functools import wraps

from firefly import Firefly
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardRemove)
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          PicklePersistence, Updater)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

FIREFLY_URL, FIREFLY_TOKEN, DEFAULT_WITHDRAW_ACCOUNT, NOT_AUTHORISED = range(4)

USERFILE = 'user_id.txt'
FIRST_USER = None


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = get_user_id(update)
        if not check_user(update):
            update.message.reply_text("Unauthorized access denied for {}.\n Only {} is authorized".format(user_id, FIRST_USER))
            return
        return func(update, context, *args, **kwargs)
    return wrapped

@restricted
def start(update, context):
    user_id = update.message.from_user.id
    update.message.reply_text(f"You are user {user_id} and authorised.\nPlease enter your Firefly III URL")
    return FIREFLY_URL
    

@restricted
def get_firefly_token(update, context):
    firefly_url = update.message.text.rstrip("//") # Remove trailing slash if exists
    context.user_data["firefly_url"] = firefly_url 
    update.message.reply_text("""
    Please enter your Firefly III User Token
    \nYou can generate it from the OAuth section here - {}/profile""".format(firefly_url))
    return DEFAULT_WITHDRAW_ACCOUNT

@restricted
def get_default_account(update, context):
    token = update.message.text
    firefly = Firefly(hostname=context.user_data.get(
        "firefly_url"), auth_token=token)
    accounts = firefly.get_accounts(account_type="asset").get("data")

    accounts_keyboard = []
    for account in accounts:
        account_name = account.get("attributes").get("name")
        accounts_keyboard.append([InlineKeyboardButton(
            account_name, callback_data=account.get("id"))])

    reply_markup = InlineKeyboardMarkup(accounts_keyboard)

    context.user_data["firefly_token"] = update.message.text
    update.message.reply_text(
        "Please choose the default Source account:", reply_markup=reply_markup)
    return DEFAULT_WITHDRAW_ACCOUNT

@restricted
def store_default_account(update, context):
    query = update.callback_query
    default_account_id = query.data
    context.user_data["firefly_default_account"] = default_account_id
    query.edit_message_text("Setup Complete. Happy Spending!(?)")
    return ConversationHandler.END

@restricted
def spend(update, context):

    def safe_list_get(l, idx):
        try:
            return l[idx]
        except IndexError:
            return None

    message = update.message.text
    if "," not in message:
        message_data = message.split(" ")
    else:
        message_data = message.split(",")

    message_data = [value.strip() for value in message_data]

    if len(message_data) < 2:
        update.message.reply_text(
            "Just type in an expense with a description. Like this - '5 Starbucks`")
        return

    amount = safe_list_get(message_data, 0)
    description = safe_list_get(message_data, 1)
    category = safe_list_get(message_data, 2)
    budget = safe_list_get(message_data, 3)
    source_account = safe_list_get(message_data, 4)
    destination_account = safe_list_get(message_data, 5)

    firefly = get_firefly(context)
    if not source_account:
        source_account = context.user_data["firefly_default_account"]

    response = firefly.create_transaction(amount, description,
                                          source_account, destination_account, category, budget)
    if response.status_code == 422:
        update.message.reply_text(response.get("message"))
    elif response.status_code == 200:
        try:
            id = response.json().get("data").get("id")
            firefly_url = context.user_data.get("firefly_url")
            update.message.reply_markdown(
                "[Expense logged successfully]({0}/transactions/show/{1})".format(
                    firefly_url, id
                ))
        except:
            update.message.reply_text("Please check input values")
    else:
        update.message.reply_text("Something went wrong, check logs")

@restricted
def about(update, context):
    firefly = get_firefly(context)
    about = firefly.get_about_user()
    update.message.reply_text("```{}```".format(about))


def get_firefly(context):
    return Firefly(hostname=context.user_data.get("firefly_url"), auth_token=context.user_data.get("firefly_token"))

@restricted
def help(update, context):
    if not context.user_data.get("firefly_default_account"):
        update.message.reply_text("Type /start to initiate the setup process.")
    else:
        update.message.reply_markdown("""
All you need to do is send a message to the bot with the following format -
`Amount, Description, Category, Budget, Source account, Destination account`

Only the first two values are needed. The rest are optional. The description value is used for destination account as well. 

A simple one - 
        `5, Starbucks`

One with all the fields being used -
        `5, Mocha with an extra shot for Steve, Coffee, Food Budget, UCO Bank, Starbucks`

You can skip specific fields by leaving them empty (except the first two) - 
        `5, Starbucks, , Food Budget, UCO Bank`
""")

def get_user_id(update):
    if update.message is not None:
        return update.message.chat.id
    return FIRST_USER # If no message, assume the right user got far enough

@restricted
def cancel(update, context):
    update.message.reply_text("Cancelled")
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning("Update '%s' caused error '%s'", update, context.error)

def check_user(update):
    global FIRST_USER
    userid = get_user_id(update)
    if FIRST_USER==None:
        FIRST_USER = userid
        with open(os.path.join(os.getenv("CONFIG_PATH", ""), USERFILE),'w') as outfile:
            outfile.write(str(userid))
        return True
    elif FIRST_USER==userid:
        return True
    return False



def main():
    global FIRST_USER
    data_dir = os.getenv("CONFIG_PATH", "")
    if not data_dir:
        data_dir = Path.joinpath(Path.home(), ".config", "firefly-bot")
        data_dir.mkdir(parents=True, exist_ok=True)
    else:
        data_dir = Path(data_dir)
    path_to_userfile = os.path.join(data_dir, USERFILE)
    if os.path.exists(path_to_userfile):
        with open(path_to_userfile, 'r') as infile:
            userid = infile.read()
        if userid != '':
            FIRST_USER = int(userid)
    bot_persistence = PicklePersistence(filename=str(data_dir/"bot-data"))
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    updater = Updater(bot_token,
                      persistence=bot_persistence, use_context=True)

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIREFLY_URL: [MessageHandler(Filters.text, get_firefly_token)],
            DEFAULT_WITHDRAW_ACCOUNT: [MessageHandler(Filters.text, get_default_account),
                                       CallbackQueryHandler(store_default_account, pattern="^[0-9]*$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CommandHandler("about", about))
    updater.dispatcher.add_handler(MessageHandler(
        filters=Filters.regex("^[0-9]+"), callback=spend))
    updater.dispatcher.add_error_handler(error)
    updater.dispatcher.add_handler(conversation_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == "__main__":
    main()
