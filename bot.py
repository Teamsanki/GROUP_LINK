import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackContext
import os
from pymongo import MongoClient
from datetime import datetime

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace this with your bot's token from BotFather
TELEGRAM_TOKEN = "your_bot_token"

# MongoDB URL
MONGO_URL = "mongodb://localhost:27017/"  # MongoDB connection string

# Replace this with your logger group chat ID (it should be negative for groups)
LOGGER_GROUP_CHAT_ID = "-1002100433415"  # Example: @loggroupname or chat_id

# Replace with your support channel link and owner's Telegram ID
OWNER_SUPPORT_CHANNEL = "https://t.me/matalbi_duniya"
OWNER_TELEGRAM_ID = "7877197608"  # Example: "123456789" or "@username"

# MongoDB Client and Database
client = MongoClient(MONGO_URL)
db = client['bot_database']
users_collection = db['users']
private_groups_collection = db['private_groups']

# Bot start time (used for uptime calculation)
bot_start_time = datetime.now()

# Function to increment the user count in MongoDB
def increment_user_count(user_id):
    users_collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

# Function to calculate uptime
def get_uptime():
    delta = datetime.now() - bot_start_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

async def start(update: Update, context: CallbackContext) -> None:
    """Sends an attractive welcome message with a photo when the bot is started, and logs to the logger group."""
    welcome_text = (
        "*🎉 Welcome to Our Bot, {user_name}! 🎉*\n\n"
        "Hello, *{user_name}* 👋\n\n"
        "Thank you for starting the bot! We're here to help you.\n\n"
        "🔹 Click below to access support or contact the owner directly!\n\n"
        "*Enjoy your experience! 🚀*"
    ).format(user_name=update.message.from_user.first_name)

    # Send welcome message with photo and Markdown formatting
    photo_url = "https://graph.org/file/6c0db28a848ed4dacae56-93b1bc1873b2494eb2.jpg"  # Replace with actual photo URL
    media = InputMediaPhoto(media=photo_url, caption=welcome_text, parse_mode='Markdown')
    await update.message.reply_media_group([media])

    # Create an inline keyboard with a link to the owner's support channel and owner's Telegram ID
    keyboard = [
        [InlineKeyboardButton("🛠 Contact Support", url=OWNER_SUPPORT_CHANNEL)],
        [InlineKeyboardButton("💬 Message Owner", url=f"tg://user?id={OWNER_TELEGRAM_ID}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the inline keyboard
    await update.message.reply_text('Tap below to get support or contact the owner:', reply_markup=reply_markup)

    # Get user details
    user_name = update.message.from_user.first_name  # User's first name
    user_username = update.message.from_user.username  # User's username
    user_id = update.message.from_user.id  # User's ID

    # Prepare the log message
    log_message = f"◈𝐍𝐀𝐌𝐄 {user_name} \n\n(◈𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄: @{user_username if user_username else 'No Username'}, \n\n◈𝐈𝐃: {user_id}) ʜᴀs sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ"
    
    # Log the user who started the bot (but without sending a message to the logger group on VPS startup)
    if not os.environ.get("IS_VPS"):
        await context.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text=log_message)

    # Increment the user count in MongoDB
    increment_user_count(user_id)

async def addgc(update: Update, context: CallbackContext) -> None:
    """Owner-only command to add a private group link."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the private group link. Usage: /addgc <group_link>")
        return

    group_link = context.args[0]
    private_groups_collection.insert_one({"link": group_link})

    await update.message.reply_text(f"Group link added: {group_link}")

async def getpvt(update: Update, context: CallbackContext) -> None:
    """Fetches all private group links (both user-added and owner-added)."""
    group_links = private_groups_collection.find().sort("_id", -1)  # Fetch all group links sorted by most recent

    if group_links.count() > 0:
        links_message = "Here are the latest private group links:\n"
        for idx, link in enumerate(group_links, 1):
            links_message += f"{idx}. {link['link']}\n"
        await update.message.reply_text(links_message)
    else:
        await update.message.reply_text("Be patient! Latest link is coming soon.")

async def reset(update: Update, context: CallbackContext) -> None:
    """Owner-only command to reset (delete) all private group links."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    private_groups_collection.delete_many({})  # Delete all group links

    await update.message.reply_text("All group links have been reset.")

async def help_command(update: Update, context: CallbackContext) -> None:
    """Shows available commands to the user, excluding owner-only commands."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot\n"
        "/getpvt - Get the latest private group links\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

async def ping(update: Update, context: CallbackContext) -> None:
    """Respond with the bot's uptime."""
    uptime = get_uptime()
    await update.message.reply_text(f"Bot Uptime: {uptime}")

def main():
    """Start the bot."""
    # Use the new Application class to replace the old Updater class
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addgc", addgc))  # Command to add a private group link
    application.add_handler(CommandHandler("getpvt", getpvt))  # Command to get private group links
    application.add_handler(CommandHandler("reset", reset))  # Command to reset private group links
    application.add_handler(CommandHandler("help", help_command))  # Command for showing help
    application.add_handler(CommandHandler("ping", ping))  # Command for checking uptime

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
