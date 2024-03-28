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
    data = json.load(f)

# Only respond to messages from my chat_id
def echo(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)    

def create_table_if_not_exists(table_name, columns):
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
    cursor.execute(create_table_query)

simple_commands = data["single_orders"]["commands"]["simple"]

no_rebound_commands = data["single_orders"]["commands"]["no_rebound"]

rebound_commands = data["single_orders"]["commands"]['rebound']

def find_key(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

# hub to process user's commands
async def hub_command(update: Update, context: ContextTypes) -> int:
    command_received = update.message.text
    user_command = command_received[1:] 
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')    
    for  simple in simple_commands:
        if user_command == simple['key']: #if user's command = simple -> END
            context.user_data['command'] = None
            create_table_if_not_exists(user_command, "timestamp TEXT, command TEXT")
            cursor.execute(f"INSERT INTO {user_command} (timestamp, command) VALUES (%s, %s)", (current_time, user_command))
            conn.commit()
            await update.message.reply_text(simple['reply'])
            return
    for no_rebound in no_rebound_commands:
        if user_command == no_rebound['key']: #if user's command = no_rebound -> redirection
            context.user_data['command'] = no_rebound
            context.user_data['state'] = 'no_rebound'
            create_table_if_not_exists(user_command, "timestamp TEXT, command TEXT, reason TEXT")
            await pannel_command(update,context)
            return
    for rebound in rebound_commands:
        if user_command == rebound['key']: #if user's command = rebound -> redirection
            context.user_data['command'] = rebound
            context.user_data['state'] = 'rebound'
            create_table_if_not_exists(user_command, "timestamp TEXT, command TEXT, answer1 TEXT, answer2 TEXT")
            await pannel_command(update,context)
            return
    await update.message.reply_text('Unknown command')

async def pannel_command(update: Update, context: ContextTypes, ) -> int:
    rebound = context.user_data['command']
    button_values = list(rebound['buttons'].values())
    buttons = [button_values]
    markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    await update.message.reply_text(rebound['follow_up_question'],reply_markup=markup)

async def handle_button_click(update: Update, context: ContextTypes) -> None:
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_response = update.message.text
    state = context.user_data['state']
    response = context.user_data['command']
    if not response:
        return 
    if state == 'final': #insert rebound command into db
        key = context.user_data['key']
        answer1 = context.user_data['answer1']
        cursor.execute(f"INSERT INTO {key} (timestamp, command, answer1, answer2) VALUES (%s, %s, %s, %s)",
            (current_time, key, answer1, user_response))
        conn.commit()
        await update.message.reply_text(response['reply'])
        context.user_data['command'] = None
        return
    if state == 'no_rebound':         
        await no_rebound_command(update, context)   
        return
    elif state == 'rebound':
        await rebound_command(update, context)

    
async def no_rebound_command(update: Update, context: ContextTypes) -> None:
    user_response = update.message.text
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    response = context.user_data['command']
    key = context.user_data['command']['key']
    if find_key(response['buttons'], user_response) == None:
        cursor.execute(f"INSERT INTO {key} (timestamp, command, reason) VALUES (%s, %s, %s)",
            (current_time, key, user_response))
        conn.commit()
        await update.message.reply_text(response['reply'])
        return
              
    key_find = find_key(response['buttons'], user_response)
    response = response['follow_up_replies']
    cursor.execute(f"INSERT INTO {key} (timestamp, command, reason) VALUES (%s, %s, %s)",
        (current_time, key, user_response))
    conn.commit()
    await update.message.reply_text(response[key_find])
    context.user_data['command'] = None
    return

async def rebound_command(update: Update, context: ContextTypes) -> None:
    user_response = update.message.text
    response = context.user_data['command']
    key = context.user_data['command']['key']
   
    if response.get('2ndbuttons'):
        button_values = list(response['2ndbuttons'].values())
        buttons = [button_values]
        markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        await update.message.reply_text(response['2ndfollow_up_question'], reply_markup=markup)
        context.user_data['key'] = key
        context.user_data['answer1'] = user_response
        context.user_data['state'] = "final"
        return

    context.user_data['key'] = key
    context.user_data['answer1'] = user_response
    context.user_data['state'] = "final"
    await update.message.reply_text(response['2ndfollow_up_question'])
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



def main() -> None:
    app = Application.builder().token(TOKEN).build()
    print("Bot started")
    
    app.add_handler(MessageHandler(filters.COMMAND, hub_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_button_click))
    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    # Errors
    app.add_error_handler(error)
   
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()