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

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
    reply_keyboard = [["Natural","Bothered","Alarm"]]
    create_table_if_not_exists("awake","wake_up_time TEXT")
    insert_data("awake",(current_time,))
    await update.message.reply_text(
        "Hello Sunshine\n\n"
        "Send /cancel to stop talking to me.\n\n"
        "Did you wake up by yourself ?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )
    return WAKE_UP

async def asleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.text
    create_table_if_not_exists("way_I_woke_up","datetime TEXT, type TEXT")
    if user == "Natural" or user == "Bothered" or user == "Alarm":
        insert_data("way_I_woke_up",(current_time,user))
        await update.message.reply_text(
        "When did you fall asleep ?",
        reply_markup=ReplyKeyboardRemove())
        return ASLEEP_TIME
    
    await update.message.reply_text("Unknown answer, try again babe")
    return WAKE_UP

async def sleep_late(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_hour = int(update.message.text)
    answers = {5:"✨",4:"🌿",3:"🐼",2:"👹",1:"⚰️"}
    reply_keyboard = [*[answers.values()]]
    reply_keyboard = [[str(value) for value in answers.values()]]
    context.user_data['answers'] = answers

    create_table_if_not_exists("asleep_time","datetime TEXT, time TEXT, reasons TEXT")
    if user_hour>24:
        await update.message.reply_text("Invalid answer, try again babe")
        return ASLEEP_TIME
    if user_hour not in [20,21,22,23]:
        context.user_data['user_hour'] = user_hour
        await update.message.reply_text("Why ?")
        return LATE_REASONS
    else:
        await update.message.reply_text("Beauty sleep yay.")
        await update.message.reply_text("What's your energy level this morning ?", reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True
        ))
        insert_data("asleep_time",(current_time, user_hour,None))
        return SLEEP_LATE
    
async def late_sleep_reasons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {5:"✨",4:"🌿",3:"🐼",2:"👹",1:"⚰️"}
    reply_keyboard = [*[answers.values()]]
    reply_keyboard = [[str(value) for value in answers.values()]]
    context.user_data['answers'] = answers
    user_hour = context.user_data['user_hour']
    user = update.message.text
    await update.message.reply_text("Noted !")
    await update.message.reply_text("What's your energy level this morning ?", reply_markup=ReplyKeyboardMarkup(
    reply_keyboard, one_time_keyboard=True
    ))
    insert_data("asleep_time",(current_time,user_hour, user))
    return SLEEP_LATE


async def energy_levels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    create_table_if_not_exists("energy_levels","datetime TEXT, level INT")
    answers = context.user_data['answers']
    user = update.message.text
    for key, value in answers.items():
        if user == value:
            level = key
    insert_data("energy_levels",(current_time,level))
    await update.message.reply_text(
        "Okay baby, see you later and have a great day !"
    )

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
        entry_points=[CommandHandler("awake", awake)],
        states={
            WAKE_UP: [MessageHandler(filters.Regex("^(Natural|Bothered|Alarm)$"), asleep_time)],
            ASLEEP_TIME: [MessageHandler(filters.Regex("^([0-9]|1[0-9]|2[0-4])$"), sleep_late)],
            LATE_REASONS: [MessageHandler(filters.TEXT, late_sleep_reasons)],
            SLEEP_LATE: [
                MessageHandler(filters.Regex("^(✨|🌿|🐼|👹|⚰️)$"), energy_levels)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()