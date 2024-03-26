# My code : 
# What's not working: the 'specific case' case, comp rebound not added.
import os
from typing import Final
from telegram import ReplyKeyboardMarkup
import psycopg2
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
import json
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

# Load commands from JSON file
with open('telegrambot/singleorders.json') as f:
    commands_data = json.load(f)

# Only respond to messages from my chat_id
def echo(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)    

def create_table_if_not_exists(table_name, columns):
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
    cursor.execute(create_table_query)

# Command handlers
async def handle_simple_commands(update: Update, context: CallbackContext):
    command_received = update.message.text
    user_command = command_received.split('/')[-1]
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for command_data in commands_data['single_orders']['simple']['commands']:
        key_simple = command_data['key']
        create_table_if_not_exists(key_simple, "timestamp TEXT, command TEXT")

    for cmd in commands_data['single_orders']['simple']['commands']:
        key = cmd['key']
        if key == user_command:
            await update.message.reply_text(text=cmd['reply'])
            cursor.execute(f"INSERT INTO {key} (timestamp, command) VALUES (%s, %s)", (current_time, user_command))
            conn.commit()
            return

    await handle_complex_commands(update, context)

async def handle_follow_up_question(cmd, update):
    follow_up_question = cmd.get('follow_up_question')
    if follow_up_question:
        buttons = [[value for value in cmd['buttons'].values()]]
        custom_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        await update.message.reply_text(follow_up_question, reply_markup=custom_markup)  

async def handle_complex_commands(update: Update, context: CallbackContext):
    command_received = update.message.text
    user_command = command_received.split('/')[-1]

    for command_group in commands_data['single_orders']['complex']['commands']:
        for command_type, commands_list in command_group.items():
            rebound_type = command_type
            for command_info in commands_list:
                key_value = command_info['key']
                if rebound_type == 'no_rebound':
                    create_complex_table = f"CREATE TABLE IF NOT EXISTS {key_value} (timestamp TEXT, command TEXT, reason TEXT)"
                elif rebound_type == 'optional_rebound':
                    create_complex_table = f"CREATE TABLE IF NOT EXISTS {key_value} (timestamp TEXT, command TEXT, reason TEXT, details TEXT)"
                elif rebound_type == 'compulsory_rebound':
                    if key_value == 'privatestuff':
                        create_complex_table = f"CREATE TABLE IF NOT EXISTS {key_value} (timestamp TEXT, command TEXT, tex TEXT, col TEXT)"
                    elif key_value == 'stress':
                        create_complex_table = f"CREATE TABLE IF NOT EXISTS {key_value} (timestamp TEXT, command TEXT, feeling TEXT, reason TEXT)"
                cursor.execute(create_complex_table)

                # Checking if the user command matches the current key_complex
                if user_command == key_value:
                    for cmd in command_group.get(rebound_type, []):
                        if cmd['key'] == user_command:
                            await handle_follow_up_question(cmd, update)
                            return

    if not command_received:
        await update.message.reply_text("Command not found.")  

async def handle_complex_responses(update: Update, context: CallbackContext):
    user_response = update.message.text
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for command_info in commands_data['single_orders']['complex']['commands']:
        for command_group in command_info.values():
            for command in command_group:
                key = command['key']
                buttons = command.get('buttons', {})
                follow_up_replies = command.get('follow_up_replies', {})

                for button_key, button_value in buttons.items():
                    if user_response == button_value:
                        if button_key == '0':
                            second_follow_up_question = command.get('2ndfollow_up_question')

                            context.user_data['second_follow_up_question'] = second_follow_up_question
                            context.user_data['key'] = key
                            context.user_data['reason'] = 'amy'
                            
                            await handle_rebound_responses(update, context)
                            return
                        else:
                            follow_up_reply = follow_up_replies.get(button_key,"Noted!")
                            await update.message.reply_text(follow_up_reply)
                            # Log the command in the database
                            cursor.execute(f"INSERT INTO {key} (timestamp, command, reason, details) VALUES (%s, %s, %s, %s)",
                                       (current_time, key, user_response, None))
                            conn.commit()
                            return

    await update.message.reply_text("Sorry, I couldn't process your response.")

async def handle_rebound_responses(update: Update, context: CallbackContext):
    key = context.user_data.get('key')
    reason = context.user_data.get('reason')
    second_follow_up_question = context.user_data.get('second_follow_up_question')
    print(key)
    print(reason)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    reply = 'test'
    # if rebound_response:
    if key == 'privatestuff':
            await update.message.reply_text(second_follow_up_question)
            rebound_response = update.message.text 
            cursor.execute(f"INSERT INTO {key} (timestamp, command, text, col) VALUES (%s, %s, %s, %s)",
                   (current_time, key, reason, rebound_response))
            conn.commit()
            await update.message.reply_text(reply)
            return
        
    elif key == 'stress':
            await update.message.reply_text(second_follow_up_question)
            rebound_response = update.message.text 
            cursor.execute(f"INSERT INTO {key} (timestamp, command, feeling, reason) VALUES (%s, %s, %s, %s)",
                   (current_time, key, reason, rebound_response))
            conn.commit()
            await update.message.reply_text('truc')
            return 
    else:
            await update.message.reply_text(second_follow_up_question)
            rebound_response = update.message.text 
            print(rebound_response)
            cursor.execute(f"INSERT INTO {key} (timestamp, command, reason, details) VALUES (%s, %s, %s, %s)",
                   (current_time, key, reason, rebound_response))
            conn.commit()
            await update.message.reply_text('testouille')
            return

#  Handle unknown messages:
def handle_response(text:str) -> str:
    return 'I am sorry, I do not understand.'
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group' and BOT_USERNAME in text:
        new_text = text.replace(BOT_USERNAME, '').strip()
        response = handle_response(new_text)
    else:
        response = handle_response(text)

    print('Bot', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    simple_command_handler = MessageHandler(filters.COMMAND, handle_simple_commands)
    app.add_handler(simple_command_handler)

    complex_command_handler = MessageHandler(filters.COMMAND, handle_complex_commands)
    app.add_handler(complex_command_handler)

    complex_response_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complex_responses)
    app.add_handler(complex_response_handler)

    complex_command_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rebound_responses)
    app.add_handler(complex_command_handler)

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    # Errors
    app.add_error_handler(error)

    #Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)