import logging
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackContext
import os
from pymongo import MongoClient

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)  # Set logging to DEBUG for troubleshooting
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

# MongoDB Client and Database
client = MongoClient(MONGO_URL)
db = client['bot_database']
users_collection = db['users']
group_links_collection = db['group_links']

# Function to increment the user count in MongoDB
def increment_user_count(user_id):
    users_collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

# Function to get the total number of unique users
def get_user_count():
    return users_collection.count_documents({})

# Function to send attractive welcome message with photo
async def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message when the bot is started, logs to the logger group, and sends an inline keyboard with the support channel and owner's Telegram ID."""
    
    # Send welcome message with photo
    welcome_text = '🎉 Welcome to the bot! 🎉\n\n' \
                   'To get started, click below to contact support or message the owner.'
    photo_url = 'https://your_image_url.com/photo.jpg'  # Replace with your image URL
    await update.message.reply_photo(photo=photo_url, caption=welcome_text)

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
    log_message = f"◈𝐍𝐀𝐌𝐄 {user_name} \n\n(◈𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄: @{user_username if user_username else 'No Username'}, \n\n◈𝐈𝐃: {user_id}) ʜᴀs sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ"
    
    # Send the log message to the logger group
    await context.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text=log_message)

    # Increment the user count in MongoDB
    increment_user_count(user_id)

# Function to show private group links
async def get_pvt_group(update: Update, context: CallbackContext) -> None:
    """Fetches the list of private group links from the MongoDB database."""
    user_id = update.message.from_user.id
    
    # Get group links for the user from MongoDB
    group_links = group_links_collection.find({"user_id": user_id})
    
    if group_links.count() > 0:
        links_text = "Here are your private group links:\n\n"
        for link in group_links:
            links_text += f"{link['group_name']}: {link['link']}\n"
        await update.message.reply_text(links_text)
    else:
        await update.message.reply_text("You don't have any private group links yet.")

# Function to add group link for owner
async def add_group_link(update: Update, context: CallbackContext) -> None:
    """Owner command to add a group link."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide a group name and link.\nUsage: /addgc <group_name> <group_link>")
        return

    group_name = context.args[0]
    group_link = context.args[1]

    # Save the group link to MongoDB
    group_links_collection.insert_one({"user_id": OWNER_TELEGRAM_ID, "group_name": group_name, "link": group_link})
    await update.message.reply_text(f"Group link for {group_name} added successfully!")

# Function to reset group links for owner
async def reset_group_links(update: Update, context: CallbackContext) -> None:
    """Owner command to reset group links."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Delete all the stored group links for the owner
    group_links_collection.delete_many({"user_id": OWNER_TELEGRAM_ID})
    await update.message.reply_text("All your group links have been deleted.")

# Function to get user info
async def user_info(update: Update, context: CallbackContext) -> None:
    """Shows user info when user provides their ID."""
    if not context.args:
        await update.message.reply_text("Please provide a valid user ID.\nUsage: /userinfo <user_id>")
        return
    
    user_id = int(context.args[0])
    user = await context.bot.get_chat_member(user_id, user_id)
    
    user_details = f"User Name: {user.user.first_name}\n"
    user_details += f"Username: @{user.user.username if user.user.username else 'N/A'}\n"
    user_details += f"User ID: {user.user.id}\n"
    user_details += f"Profile Photo: {user.user.get_profile_photos()[-1].file_id if user.user.get_profile_photos() else 'No Photo'}"

    await update.message.reply_text(user_details)

# Function to show bot stats (total number of users)
async def stats(update: Update, context: CallbackContext) -> None:
    """Shows the total number of users who have started the bot."""
    total_users = get_user_count()
    await update.message.reply_text(f"Total number of users who have started the bot: {total_users}")

# Function to handle help command
async def help_command(update: Update, context: CallbackContext) -> None:
    """Shows available commands to the user."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot\n"
        "/getpvt - Get your private group links\n"
        "/addgc - Add a new group link (Owner Only)\n"
        "/reset - Reset all your group links (Owner Only)\n"
        "/stats - View the total number of users who have started the bot\n"
        "/userinfo <user_id> - Get user info by ID\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

def main():
    """Start the bot."""
    # Use the new Application class to replace the old Updater class
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getpvt", get_pvt_group))  # Command for getting private group links
    application.add_handler(CommandHandler("addgc", add_group_link))  # Command for adding group link (Owner only)
    application.add_handler(CommandHandler("reset", reset_group_links))  # Command for resetting group links (Owner only)
    application.add_handler(CommandHandler("stats", stats))  # Command for stats
    application.add_handler(CommandHandler("userinfo", user_info))  # Command for user info
    application.add_handler(CommandHandler("help", help_command))  # Command for showing help

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
