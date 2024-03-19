import os
from typing import Final
from telegram import ReplyKeyboardMarkup
import sqlite3
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
BOT_USERNAME: Final = os.getenv('Bot')
my_chat_id = os.getenv('my_chat_id')

# Connect to SQLite database
conn = sqlite3.connect('feelings.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS command_logs (command TEXT, timestamp TEXT, reason TEXT)")

# Load commands from JSON file
with open('telegrambot/singleorders.json') as f:
    commands_data = json.load(f)


# Only respond to messages from my chat_id
def echo(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)    

# HANDLE COMMANDS
async def handle_commands(update: Update, context:CallbackContext):
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
            return
        
    # for cmd in commands_data['single_orders']['complex']['commands']:
    #     if cmd['key'] == command:
    #         context.user_data['command'] = command
    #         context.user_data['timestamp'] = current_time
    #         # Reply with the corresponding message
    #         follow_up_question = cmd.get('follow_up_question')
    #         if follow_up_question:
    #             buttons = [[value for value in cmd['buttons'].values()]]
    #             custom_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    #             await update.message.reply_text(follow_up_question, reply_markup=custom_markup)


    #             # Retrieve user's reply and add to database
    #             user_response =  context.user_data.get('response')
    #             cursor.execute("INSERT INTO command_logs (command, timestamp, reason) VALUES (?, ?, ?)",
    #                            (command, current_time, user_response))
    #             conn.commit()

    #         return
        
    await update.message.reply_text("Sorry, I couldn't find that command.") 

# async def handle_complex_response(update: Update, context: CallbackContext):
#     # Retrieve the user's response
#     user_response = update.message.text
    
#     # Retrieve command and timestamp from the context
#     command = context.user_data.get('command')
#     timestamp = context.user_data.get('timestamp')
        
#     # Retrieve the follow-up replies from the JSON data
#     follow_up_replies = None
#     for cmd in commands_data['single_orders']['complex']['commands']:
#         if cmd['key'] == command:
#             follow_up_replies = cmd.get('follow_up_replies')
#             break
#         # If follow-up replies are found and the user's response is valid, send the corresponding follow-up reply
#         if follow_up_replies and user_response in follow_up_replies:
#             follow_up_reply = follow_up_replies[user_response]
#             await update.message.reply_text(follow_up_reply)

#     # Store the user's response in the database
#         cursor.execute("INSERT INTO command_logs (command, timestamp, reason) VALUES (?, ?, ?)",
#                        (command, timestamp, user_response))
#         conn.commit()
        
#         # Optionally, you can provide a reply acknowledging the user's response
#         await update.message.reply_text("Your response has been recorded.")
#     else:
#         await update.message.reply_text("Sorry, I couldn't process your response.")

async def handle_complex_response(update: Update, context: CallbackContext):
    # Retrieve the user's response
    user_response = update.message.text
    
    # Retrieve command and timestamp from the context
    command = context.user_data.get('command')
    timestamp = context.user_data.get('timestamp')
        
    # Retrieve the follow-up replies from the JSON data
    follow_up_replies = None
    for cmd in commands_data['single_orders']['complex']['commands']:
        if cmd['key'] == command:
            follow_up_replies = cmd.get('follow_up_replies')
            break
    
    # If follow-up replies are found and the user's response is valid, send the corresponding follow-up reply
    if follow_up_replies and user_response in follow_up_replies:
        follow_up_reply = follow_up_replies[user_response]
        await update.message.reply_text(follow_up_reply)

        # Store the user's response and reason in the database
        reason = follow_up_replies[user_response]
        cursor.execute("INSERT INTO command_logs (command, timestamp, reason) VALUES (?, ?, ?)",
                       (command, timestamp, reason))
        conn.commit()

        
        # Optionally, you can provide a reply acknowledging the user's response
        await update.message.reply_text("Your response has been recorded.")
    else:
        await update.message.reply_text("Sorry, I couldn't process your response.")

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

    # Commands
    app.add_handler(MessageHandler(filters.COMMAND, handle_commands))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complex_response))
    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    # Errors
    app.add_error_handler(error)

    #Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)

