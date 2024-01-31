from typing import Final
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext


TOKEN = '6858171735:AAEALynfPgnsrvC3QB1an8fqVEiy342_Np4'
BOT_USERNAME: Final = '@thisisyourdailyreminder_bot'
my_chat_id = 1242746236

# Connect to SQLite database
conn = sqlite3.connect('feelings.db')
cursor = conn.cursor()

# Only respond to messages from my chat_id
def echo(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id == my_chat_id:
        update.message.reply_text(update.message.text)
        
# commands
async def start_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! How do you feel today?")
    
# Define message handler to store the feeling in the database
async def store_feeling(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    feeling_text = update.message.text

    # Insert data into the database
    cursor.execute("CREATE TABLE IF NOT EXISTS feelings (user_id TEXT, feeling_text TEXT)")
    cursor.execute("INSERT INTO feelings (user_id, feeling_text) VALUES (?, ?)", (user_id, feeling_text))
    conn.commit()

    await update.message.reply_text('Your feeling has been stored successfully!')


async def help_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('How may I help you ?')
    

async def custom_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command.')

#  Responses

def handle_response(text:str) -> str:
    processed: str = text.lower()
    if 'hello' in processed: 
        return 'Hi there!'
    if 'how are you' in processed:
        return 'I am good thank you! What about you ?'
    if 'fine' in processed: 
        return 'Good to hear!'
    if 'bye' in processed:
        return 'Bye bye, see you soon'
    
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

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, store_feeling))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))



    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    #Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)

