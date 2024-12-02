import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace this with your bot's token from BotFather
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"

# Replace this with your logger group chat ID (it should be negative for groups)
LOGGER_GROUP_CHAT_ID = "@your_logger_group_or_chat_id"  # Example: @loggroupname or chat_id

def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message when the bot is started and logs to the logger group."""
    
    # Send welcome message to the user
    update.message.reply_text('Hello! Send me your group chat ID to get the latest link.')

    # Get user details
    user_name = update.message.from_user.first_name  # User's first name
    user_username = update.message.from_user.username  # User's username
    user_id = update.message.from_user.id  # User's ID

    # Prepare the log message
    log_message = f"User {user_name} (Username: @{user_username if user_username else 'No Username'}, ID: {user_id}) has started the bot."
    
    # Send the log message to the logger group
    context.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text=log_message)

def get_group_link(update: Update, context: CallbackContext) -> None:
    """Fetches the group link based on chat ID."""
    chat_id = update.message.text.strip()
    group_link = f"https://t.me/{chat_id}"  # Placeholder for the actual group link logic
    update.message.reply_text(f"The latest link for your group: {group_link}")

def help_command(update: Update, context: CallbackContext) -> None:
    """Shows available commands to the user."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot\n"
        "/getgroup <chat_id> - Get the link for your group\n"
        "/help - Show this help message"
    )
    update.message.reply_text(help_text)

def main():
    """Start the bot."""
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("getgroup", get_group_link))
    dispatcher.add_handler(CommandHandler("help", help_command))  # Added help command

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
