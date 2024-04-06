from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext
)
import os
from typing import Final
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
BOT_USERNAME: Final = os.getenv('Bot')
my_chat_id = os.getenv('my_chat_id')

DB_CONFIG = {
    'dbname': os.getenv('PG_DBNAME'),
    'user': os.getenv('PG_USER'),
    'password': os.getenv('PG_PASSWORD'),
    'host': os.getenv('PG_HOST'),
    'port': os.getenv('PG_PORT')
}
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Only reply to messages from my chat_id
def echo(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)    

# Database gestion
def create_table_if_not_exists(table_name, data):
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({data})"
    cursor.execute(create_table_query)
    conn.commit()
def insert_data(table_name, data):
    insert_query = f"INSERT INTO {table_name} VALUES %s"
    cursor.execute(insert_query, (data,))
    conn.commit()


ASLEEP, DAY_RATING, PRODUCTIVITY_RATING, MEALS_QUANTITY, VITAMINS, JOURNALING = range(6)


async def asleep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {5:"5️⃣",4:"4️⃣",3:"3️⃣",2:"2️⃣",1:"1️⃣"}
    reply_keyboard = [*[answers.values()]]
    reply_keyboard = [[str(value) for value in answers.values()]]
    context.user_data['answers'] = answers
    context.user_data['reply_keyboard'] = reply_keyboard
    await update.message.reply_text(
        "Hey Sunshine\n\n"
        "Send /cancel to stop talking to me.\n\n"
        "How was your day?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        )
    )
    return ASLEEP

async def day_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = context.user_data['reply_keyboard']
    answers = context.user_data['answers']
    user = update.message.text
    for key, value in answers.items():
        if user == value:
            rating = key
    create_table_if_not_exists("day_rating","rating TEXT")
    insert_data("day_rating",(rating,))
    await update.message.reply_text("How productive have you been today?", reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True
    ))
    return DAY_RATING

async def productivity_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = context.user_data['reply_keyboard']
    answers = context.user_data['answers']
    user = update.message.text
    for key, value in answers.items():
        if user == value:
            rating = key
    create_table_if_not_exists("productivity_rating","rating TEXT")
    insert_data("productivity_rating",(rating,))
    await update.message.reply_text("How many meals did you have today?", reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True
    ))
    return PRODUCTIVITY_RATING

async def meals_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    vitamins_keyboard = [["Yes", "No"]]
    answers = context.user_data['answers']
    user = update.message.text
    for key, value in answers.items():
        if user == value:
            meal = key
    create_table_if_not_exists("meals_quantity","rating TEXT")
    insert_data("meals_quantity",(meal,))
    await update.message.reply_text("Did you take your vitamins today?", reply_markup=ReplyKeyboardMarkup(
        vitamins_keyboard, one_time_keyboard=True
    ))
    print("exit")
    return MEALS_QUANTITY


async def vitamins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.text
    create_table_if_not_exists("vitamins","rating TEXT")
    insert_data("vitamins",(user,))
    await update.message.reply_text("Tell me about your day")

    return VITAMINS

async def journaling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.text
    create_table_if_not_exists("journaling","journal TEXT")
    insert_data("journaling",(user,))
    await update.message.reply_text("Okay baby, time to sleep")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.text
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("asleep", asleep)],
        states={
            ASLEEP: [MessageHandler(filters.Regex("^(5️⃣|4️⃣|3️⃣|2️⃣|1️⃣)$"), day_rating)],
            DAY_RATING: [MessageHandler(filters.Regex("^(5️⃣|4️⃣|3️⃣|2️⃣|1️⃣)$"), productivity_rating)],
            PRODUCTIVITY_RATING: [MessageHandler(filters.Regex("^(5️⃣|4️⃣|3️⃣|2️⃣|1️⃣)$"), meals_quantity)],
            MEALS_QUANTITY: [MessageHandler(filters.Regex("^(Yes|No)$"), vitamins)],
            VITAMINS: [MessageHandler(filters.TEXT, journaling)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()