import logging
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
import os
from pymongo import MongoClient

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace this with your bot's token from BotFather
TELEGRAM_TOKEN = "7894936433:AAGB6DUCC13t_a9I5YaBTk_3-xpuiH5mNiU"

# MongoDB URL
MONGO_URL = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # e.g., mongodb://localhost:27017/

# Replace this with your logger group chat ID (it should be negative for groups)
LOGGER_GROUP_CHAT_ID = "-1002100433415"  # Example: @loggroupname or chat_id

# Replace with your support channel link and owner's Telegram ID
OWNER_SUPPORT_CHANNEL = "https://t.me/matalbi_duniya"
OWNER_TELEGRAM_ID = "7877197608"  # Example: "123456789" or "@username"

# GitHub repository details
GITHUB_REPO_DIR = '/path/to/your/bot/repo'  # Path to the bot's repo directory on the server
GITHUB_REPO_URL = 'https://github.com/Teamsanki/GROUP_LINK.git'

# MongoDB Client and Database
client = MongoClient(MONGO_URL)
db = client['bot_database']
users_collection = db['users']

# Function to increment the user count in MongoDB
def increment_user_count(user_id):
    users_collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

# Function to get the total number of unique users
def get_user_count():
    return users_collection.count_documents({})

async def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message when the bot is started, logs to the logger group, and sends an inline keyboard with the support channel and owner's Telegram ID."""
    
    # Send welcome message to the user
    welcome_text = 'Hello! Welcome to the bot. If you need any help, you can contact our support team or reach out to the owner.'
    await update.message.reply_text(welcome_text)

    # Create an inline keyboard with a link to the owner's support channel and owner's Telegram ID
    keyboard = [
        [InlineKeyboardButton("Contact Support", url=OWNER_SUPPORT_CHANNEL)],
        [InlineKeyboardButton("Message Owner", url=f"tg://user?id={OWNER_TELEGRAM_ID}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the inline keyboard
    await update.message.reply_text('Click below to get support or message the owner:', reply_markup=reply_markup)

    # Get user details
    user_name = update.message.from_user.first_name  # User's first name
    user_username = update.message.from_user.username  # User's username
    user_id = update.message.from_user.id  # User's ID

    # Prepare the log message
    log_message = f"User {user_name} (Username: @{user_username if user_username else 'No Username'}, ID: {user_id}) has started the bot."
    
    # Send the log message to the logger group
    await context.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text=log_message)

    # Increment the user count in MongoDB
    increment_user_count(user_id)

async def get_group_link(update: Update, context: CallbackContext) -> None:
    """Fetches the group link based on the chat ID provided by the user."""
    if not context.args:
        await update.message.reply_text("Please provide a valid public group ID. Usage: /getgroup <chat_id>")
        return

    chat_id = context.args[0]  # Get the first argument (group ID)
    
    try:
        # Get the chat details using the provided chat ID
        chat = await context.bot.get_chat(chat_id)

        # Check if the chat is a public group by verifying if it has an invite link
        if chat.type in ['supergroup', 'group'] and chat.invite_link:
            # This is a public group, send the invite link
            group_link = chat.invite_link
            await update.message.reply_text(f"The latest link for your public group: {group_link}")
        else:
            # This is not a public group, send a message to the user
            await update.message.reply_text("This bot only supports public group links. Private chats and private groups are not supported.")
    
    except Exception as e:
        await update.message.reply_text(f"Error fetching the group link: {str(e)}")

async def update_bot(update: Update, context: CallbackContext) -> None:
    """Pull the latest changes from the GitHub repository and restart the bot."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("Sorry, you don't have permission to update the bot.")
        return

    # Send a message saying the bot is updating
    await update.message.reply_text("Updating the bot to the latest version from the GitHub repository...")

    try:
        # Log the update action
        await context.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text="Bot is updating from GitHub...")

        # Pull the latest changes from the GitHub repository
        subprocess.run(['git', '-C', GITHUB_REPO_DIR, 'pull'], check=True)

        # Restart the bot by running the same Python script
        subprocess.run(['python3', 'bot.py'], check=True)  # This will restart the bot
        
        await update.message.reply_text("Bot has been updated and restarted successfully!")
    except Exception as e:
        await update.message.reply_text(f"Error during update: {str(e)}")

async def stats(update: Update, context: CallbackContext) -> None:
    """Show the total number of users who have started the bot."""
    total_users = get_user_count()
    await update.message.reply_text(f"Total number of users who have started the bot: {total_users}")

async def help_command(update: Update, context: CallbackContext) -> None:
    """Shows available commands to the user."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot\n"
        "/getgroup <chat_id> - Get the link for your public group\n"
        "/update - Update and restart the bot (Owner Only)\n"
        "/stats - View the total number of users who have started the bot\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

def main():
    """Start the bot."""
    # Use the new Application class to replace the old Updater class
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getgroup", get_group_link))  # Command for getting the group link
    application.add_handler(CommandHandler("update", update_bot))  # Command for updating the bot
    application.add_handler(CommandHandler("stats", stats))  # Command for stats
    application.add_handler(CommandHandler("help", help_command))  # Command for showing help

    # Log when the bot starts on the server
    logger.info("Bot has started.")
    
    # Send message to logger group when the bot starts
    application.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text="Bot has started successfully on the server!")

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
