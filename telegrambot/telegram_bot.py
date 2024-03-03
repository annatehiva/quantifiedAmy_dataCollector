from typing import Final
from telegram import ReplyKeyboardMarkup
import sqlite3
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import json
from datetime import datetime

TOKEN = 'xxx'
BOT_USERNAME: Final = '@xxx'
my_chat_id = 123456789


# Connect to SQLite database
conn = sqlite3.connect('feelings.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS command_logs (command TEXT, timestamp TEXT)")

# Only respond to messages from my chat_id
def echo(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)

# Load commands from JSON file
with open('telegrambot\singleorders.json') as f:
    commands_data = json.load(f)
      
# HANDLE SIMPLE COMMANDS
async def simple_command(update: Update, context:CallbackContext):
    # variables
    message = update.message.text
    command = message.split('/')[-1]  # Extract command from message
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Check if the command exists in the JSON data
    for cmd in commands_data['single_orders']['simple']['commands']:
        if cmd['key'] == command:
            # Reply with the corresponding message
            await update.message.reply_text(text=cmd['reply'])
            
            # Log the command in the database
            cursor.execute("INSERT INTO command_logs (command, timestamp) VALUES (?, ?)", (command, current_time))
            conn.commit()
            break

# HANDLE COMPLEX COMMANDS
async def complex_command(update: Update, context:CallbackContext):
    # variables
    message = update.message.text
    command = message.split('/')[-1]  # Extract command from message
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Check if the command exists in the JSON data
    for cmd in commands_data['single_orders']['complex']['commands']:
        if cmd['key'] == command:
            # Reply with the corresponding message
            await update.message.reply_text(text=cmd['follow_up_question'])
            follow_up_question = cmd.get('follow_up_question')
            if follow_up_question:
                buttons = [[value for value in cmd['buttons'].values()]]
                custom_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
                await update.message.reply_text(follow_up_question, reply_markup=custom_markup)


                # Retrieve user's reply and add to database
                user_response = update.message.text
                cursor.execute("INSERT INTO command_logs (command, timestamp, reason) VALUES (?, ?, ?)",
                               (command, current_time, user_response))
                conn.commit()

                await update.message.reply_text(text=cmd['reply'])
                break

            




#  Handle unknown messages:
def handle_response(text:str) -> str:
    return 'I am sorry, I do not understand.'
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    

    print('Bot', response)
    await update.message.reply_text(response)
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.COMMAND, simple_command))
    app.add_handler(MessageHandler(filters.COMMAND, complex_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    #Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
