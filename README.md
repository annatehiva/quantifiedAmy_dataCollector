# Telegram Bot Project: Quantified Self
This project is a Telegram bot that facilitates habit tracking through predefined commands and responses stored in JSON to simplify the addition or modifications of commands. User's replies are collected and stored in a POstgreSQL-managed database.
#Quantified self: the practice of using technology to track and analyze personal data, such as health, behavior, and habits, to gain insights and improve one's well-being.
Note: original commits cannot be accessed here due to privacy reasons.

## Installation
1. Create a Telegram Bot: https://core.telegram.org/bots/tutorial and ensure you have a PostgreSQL database set up.
2. Clone this repository to your local machine.
3. Install the required dependencies by running:
   pip install -r requirements.txt
4. Set up your environment variables with a '.env' file.
5. Run the bot by executing the 'telegram_bot.py' script.

## Usage
Once the bot is running, users can interact with it through Telegram. Users can modify the JSON file to suit their requirements.
Only messages from the specified user will trigger responses from the bot.
The bot responds to commands defined in the 'singleorders.json' file, with various types of commands:
  - simple: a command that creates an entry into a specific table (ex: /stretch -> table: timestamp/stretch)
  - no rebound: a command that triggers a question and retrieves the user's reply (ex: /headache, "lack of sleep" -> table: timestamp/headache/lack of sleep)
  - rebound: a command that triggers two questions and retrieves replies (ex: /stress, "highly stressed", "work reasons" -> table: timestamp/stress/highly stressed/work reasons)

## Future Improvements
- Data visualization: Enhance the bot's capabilities with data visualization features.
- Tests.

For questions or feedback, please feel free to contact: gitfb.reenter889@passmail.net.
