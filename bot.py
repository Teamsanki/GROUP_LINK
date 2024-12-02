import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace this with your bot's token from BotFather
TELEGRAM_TOKEN = "7894936433:AAGB6DUCC13t_a9I5YaBTk_3-xpuiH5mNiU"

# Replace this with your logger group chat ID (it should be negative for groups)
LOGGER_GROUP_CHAT_ID = "-1002148651992"  # Example: @loggroupname or chat_id

# Replace with your support channel link and owner's Telegram ID
OWNER_SUPPORT_CHANNEL = "https://t.me/matalbi_duniya"
OWNER_TELEGRAM_ID = "7877197608"  # Example: "123456789" or "@username"

def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message when the bot is started, logs to the logger group, and sends an inline keyboard with the support channel and owner's Telegram ID."""
    
    # Send welcome message to the user
    welcome_text = 'Hello! Welcome to the bot. If you need any help, you can contact our support team or reach out to the owner.'
    update.message.reply_text(welcome_text)

    # Create an inline keyboard with a link to the owner's support channel and owner's Telegram ID
    keyboard = [
        [InlineKeyboardButton("Contact Support", url=OWNER_SUPPORT_CHANNEL)],
        [InlineKeyboardButton("Message Owner", url=f"tg://user?id={OWNER_TELEGRAM_ID}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the inline keyboard
    update.message.reply_text('Click below to get support or message the owner:', reply_markup=reply_markup)

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
