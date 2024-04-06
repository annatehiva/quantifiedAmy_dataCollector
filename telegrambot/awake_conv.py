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


WAKE_UP, ASLEEP_TIME, LATE_REASONS, SLEEP_LATE = range(4)


async def awake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Yes","No"]]

    await update.message.reply_text(
        "Hello Sunshine"
        "Send /cancel to stop talking to me.\n\n"
        "Did you wake up by yourself ?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Yes or No?"
        ),
    )
    
    return WAKE_UP


async def asleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text(
        "When did you fall asleep ?",
        reply_markup=ReplyKeyboardRemove()
    )

    return ASLEEP_TIME


async def sleep_late(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["✨","🌿","🐼","👹","⚰️"]]
    try:
        user_sleep_time = int(update.message.from_user)
        user_hour = user_sleep_time % 24
        if user_hour < 0:
            user_hour += 24
        if user_hour < 8 or user_hour == 0:
            await update.message.reply_text("Beauty sleep yay.")
            await update.message.reply_text("What's your energy level this morning ?")
            reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        )
            return SLEEP_LATE
        elif user_hour >= 8:
            await update.message.reply_text("Why ?")
            return LATE_REASONS
    except ValueError:
        await update.message.reply_text("Please enter a correct number.")


async def late_sleep_reasons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["✨","🌿","🐼","👹","⚰️"]]
    user = update.message.from_user
    await update.message.reply_text("Noted !")
    await update.message.reply_text("What's your energy level this morning ?")
    reply_markup=ReplyKeyboardMarkup(
    reply_keyboard, one_time_keyboard=True
        )
    return SLEEP_LATE


async def energy_levels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    if user == "✨" or user == "🌿":
        await update.message.reply_text("Great !")
    if user == "🐼" or user == "👹" or user == "⚰️":
        await update.message.reply_text("Oh no !")

    await update.message.reply_text(
        "Okay baby, see you later and have a great day !"
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("/awake", awake)],
        states={
            WAKE_UP: [MessageHandler(filters.Regex("^(Yes|No)$"), asleep_time)],
            ASLEEP_TIME: [MessageHandler(filters.TEXT, sleep_late)],
            LATE_REASONS: [MessageHandler(filters.TEXT, sleep_late)],
            SLEEP_LATE: [
                MessageHandler(filters.TEXT, energy_levels)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()