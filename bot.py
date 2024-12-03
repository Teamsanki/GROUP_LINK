import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
import os
from pymongo import MongoClient
import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
TELEGRAM_TOKEN = "7894936433:AAGB6DUCC13t_a9I5YaBTk_3-xpuiH5mNiU"

# MongoDB URL
MONGO_URL = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Logger Group Chat ID
LOGGER_GROUP_CHAT_ID = -1002148651992  # Replace with your logger group chat ID

# Owner Information
OWNER_SUPPORT_CHANNEL = "https://t.me/matalbi_duniya"
OWNER_TELEGRAM_ID = "7877197608"  # Replace with your Telegram ID

# Photo URL for Welcome Message
WELCOME_PHOTO_URL = "https://graph.org/file/6c0db28a848ed4dacae56-93b1bc1873b2494eb2.jpg"  # Replace with your photo URL

# MongoDB Client
client = MongoClient(MONGO_URL)
db = client["bot_database"]
users_collection = db["users"]
groups_collection = db["groups"]

# Function to increment user count
def increment_user_count(user_id):
    users_collection.update_one(
        {"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
    )

# Function to get user count
def get_user_count():
    return users_collection.count_documents({})

# Function to add group link
def add_group_link(link):
    groups_collection.insert_one({"link": link})

# Function to get all group links
def get_all_group_links():
    return [group["link"] for group in groups_collection.find()]

# Function to reset all group links
def reset_group_links():
    groups_collection.delete_many({})


# Start Command
async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with a photo and log the user's info."""
    user = update.message.from_user
    user_id = user.id
    user_name = user.first_name or "No Name"
    user_username = user.username or "No Username"

    # Send photo with welcome message
    welcome_text = (
        "✨ **Welcome to the Bot!** ✨\n\n"
        "This bot can help you fetch group links, get user details, and more.\n\n"
        "Use the buttons below to get support or contact the owner for assistance.\n"
        "To explore the bot's features, use the inline buttons or type /help."
    )
    keyboard = [
        [InlineKeyboardButton("Contact Support", url=OWNER_SUPPORT_CHANNEL)],
        [InlineKeyboardButton("Message Owner", url=f"tg://user?id={OWNER_TELEGRAM_ID}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_photo(
        photo=WELCOME_PHOTO_URL,
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

    # Log the user starting the bot
    log_message = (
        f"**Bot Started!**\n\n"
        f"**Name**: {user_name}\n"
        f"**Username**: @{user_username if user_username != 'No Username' else 'N/A'}\n"
        f"**User ID**: `{user_id}`"
    )
    await context.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text=log_message)

    # Increment user count
    increment_user_count(user_id)


# Add Group Command (Owner Only)
async def addgc(update: Update, context: CallbackContext) -> None:
    """Add group links (Owner Only)."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a group link to add.")
        return

    link = context.args[0]
    add_group_link(link)
    await update.message.reply_text(f"Group link '{link}' has been added.")


# Reset Groups Command (Owner Only)
async def reset(update: Update, context: CallbackContext) -> None:
    """Reset all group links (Owner Only)."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    reset_group_links()
    await update.message.reply_text("All group links have been reset.")


# Get Private Groups Command
async def getpvt(update: Update, context: CallbackContext) -> None:
    """Get the list of private group links."""
    links = get_all_group_links()
    if not links:
        await update.message.reply_text("Be patient. Latest link is coming soon!")
    else:
        await update.message.reply_text(
            "Here are the available group links:\n" + "\n".join(links)
        )


# Stats Command
async def stats(update: Update, context: CallbackContext) -> None:
    """Show the total number of users who have started the bot."""
    total_users = get_user_count()
    await update.message.reply_text(f"Total users who started the bot: {total_users}")


# Help Command
async def help_command(update: Update, context: CallbackContext) -> None:
    """Send the help message with inline buttons."""
    help_text = "Here are the available commands. Click on any button to learn more:"
    keyboard = [
        [
            InlineKeyboardButton("/getpvt", callback_data="getpvt"),
            InlineKeyboardButton("/stats", callback_data="stats"),
        ],
        [
            InlineKeyboardButton("/userinfo", callback_data="userinfo"),
            InlineKeyboardButton("/help", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, reply_markup=reply_markup)


# Inline Button Callback Handler
async def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()

    # Show details about the command when button is clicked
    data = query.data
    if data == "getpvt":
        await query.message.reply_text(
            "Use /getpvt to get the latest group links shared by the owner."
        )
    elif data == "stats":
        await query.message.reply_text(
            "Use /stats to see the total number of users who started the bot."
        )
    elif data == "userinfo":
        await query.message.reply_text(
            "Use /userinfo <user_id> to get detailed information about a user."
        )
    elif data == "help":
        await query.message.reply_text("This is the help command.")


# User Info Command
async def userinfo(update: Update, context: CallbackContext) -> None:
    """Fetch user information."""
    if not context.args:
        await update.message.reply_text("Please provide a user ID. Usage: /userinfo <id>")
        return

    user_id = context.args[0]
    try:
        user = await context.bot.get_chat(user_id)
        text = (
            f"**User Info**\n\n"
            f"**Name**: {user.full_name}\n"
            f"**Username**: @{user.username if user.username else 'N/A'}\n"
            f"**User ID**: `{user.id}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
        if user.photo:
            photo = user.photo.big_file_id
            await context.bot.send_photo(update.message.chat_id, photo=photo)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


# Main Function
def main():
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addgc", addgc))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("getpvt", getpvt))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("userinfo", userinfo))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Run the bot
    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
