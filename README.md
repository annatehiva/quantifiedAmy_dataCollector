# Telegram Bot Project
This project is a Python Telegram bot designed to track life-habits. It handles commands and interactions with users based on predefined commands and responses that get stored into a database.

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
- Scheduled conversations: Implement scheduled interactions with users.
- Data visualization: Enhance the bot's capabilities with data visualization features.
- Tests.

For questions or feedback, please feel free to contact me.

