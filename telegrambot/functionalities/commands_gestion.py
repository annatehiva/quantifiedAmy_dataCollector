import os
from typing import Final
from telegram import ReplyKeyboardMarkup
import psycopg2
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackContext
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

# Only reply to messages from my chat_id
def reply_to_me_only(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)    

# Time variables
now = datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
week = now.strftime("%V")
day = now.strftime("%d")
hour = now.strftime("%H")
minute = now.strftime("%M")
yearmonth = now.strftime("%Y%m")
yearweek = now.strftime("%Y%V")
if month in ['01', '02', '03']:
    quarter = 1
elif month in ['04', '05', '06']:
    quarter = 2
elif month in ['07', '08', '09']:
    quarter = 3
else:
    quarter = 4
all_values = (yearmonth, yearweek, year, quarter, month, week, day, hour, minute)

#JSON variables
simple_commands = data["single_orders"]["commands"]["simple"]
no_rebound_commands = data["single_orders"]["commands"]["no_rebound"]
rebound_commands = data["single_orders"]["commands"]['rebound']


# Database gestion
def create_table_if_not_exists(table_name, data):
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, yearmonth INT, yearweek INT, year SMALLINT, quarter SMALLINT, month SMALLINT, week SMALLINT, day SMALLINT, hour SMALLINT, minute SMALLINT, {data})"
    cursor.execute(create_table_query)
    conn.commit()
def insert_data(table_name, data):
    if not isinstance(data, tuple): #convert to a tuple if it's not already
        data = (data,)
    data = all_values + data #all_values and data are compatible as they're both tuples
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'") #query to check number of columns
    columns = [row[0] for row in cursor.fetchall() if row[0] != 'id'] #select all columns except the "id" one
    placeholders = ', '.join(['%s'] * len(columns)) #create placeholders for all columns except "id"
    insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})" 
    cursor.execute(insert_query, data)
    conn.commit()


def find_key(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

# hub to process user's commands
async def hub_command(update: Update, context: ContextTypes) -> int:
    command_received = update.message.text
    user_command = command_received[1:]    
    for  simple in simple_commands:
        if user_command == simple['key']: #if user's command = simple -> END
            context.user_data['command'] = None
            create_table_if_not_exists(user_command, "command TEXT")
            insert_data(user_command, (user_command))
            await update.message.reply_text(simple['reply'])
            return
    for no_rebound in no_rebound_commands:
        if user_command == no_rebound['key']: #if user's command = no_rebound -> redirection
            context.user_data['command'] = no_rebound
            context.user_data['state'] = 'no_rebound'
            create_table_if_not_exists(user_command, "command TEXT, reason TEXT")
            await pannel_command(update,context)
            return
    for rebound in rebound_commands:
        if user_command == rebound['key']: #if user's command = rebound -> redirection
            context.user_data['command'] = rebound
            context.user_data['state'] = 'rebound'
            create_table_if_not_exists(user_command, "command TEXT, answer1 TEXT, answer2 TEXT")
            await pannel_command(update,context)
            return
    await update.message.reply_text('Unknown command')

# if no_rebound/rebound: send follow_up_question + custom Keyboard
async def pannel_command(update: Update, context: ContextTypes, ) -> int:
    rebound = context.user_data['command']
    button_values = list(rebound['buttons'].values())
    buttons = [button_values]
    markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(rebound['follow_up_question'],reply_markup=markup)

# manage state of conversation
async def handle_button_click(update: Update, context: ContextTypes) -> None:
    user_response = update.message.text
    if not context.user_data.get("state"):
        await update.message.reply_text('Sorry, this message cannot be processed.')
    response = context.user_data['command']
    state = context.user_data['state']
    if not response:
        return 

    if state == 'final': # insert rebound command into db
        key = context.user_data['key']
        answer1 = context.user_data['answer1']
        insert_data(key, (key, answer1, user_response))
        await update.message.reply_text(response['reply'])
        context.user_data['command'] = None
        context.user_data['state'] = None
        return
    if state == 'no_rebound':        
        await no_rebound_command(update, context)   
        return
    if state == 'rebound':
        await rebound_command(update, context)

    if context.user_data['state'] == None :
        await update.message.reply_text('nope')

# manages automatic or custom reply
async def no_rebound_command(update: Update, context: ContextTypes) -> None:
    user_response = update.message.text
    response = context.user_data['command']
    key = context.user_data['command']['key']
    if find_key(response['buttons'], user_response) == None:
        insert_data(key, (key, user_response))
        await update.message.reply_text(response['reply'])
        context.user_data['state'] = None
        return
              
    key_find = find_key(response['buttons'], user_response)
    response = response['follow_up_replies']
    insert_data(key, (key, user_response))
    await update.message.reply_text(response[key_find])
    context.user_data['command'] = None
    context.user_data['state'] = None
    return

async def rebound_command(update: Update, context: ContextTypes) -> None:
    user_response = update.message.text
    response = context.user_data['command']
    key = context.user_data['command']['key']
   
    if response.get('2ndbuttons'):
        button_values = list(response['2ndbuttons'].values())
        buttons = [button_values]
        markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
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

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')



def main() -> None:
    app = Application.builder().token(TOKEN).build()
    print("Bot started")
    
    app.add_handler(MessageHandler(filters.COMMAND, hub_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_button_click))

    app.add_error_handler(error)
   
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()