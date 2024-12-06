import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import os
from pymongo import MongoClient
from datetime import datetime
import random

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace this with your bot's token from BotFather
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"

# MongoDB URL
MONGO_URL = "YOUR_MONGODB"

# Replace this with your logger group chat ID (it should be negative for groups)
LOGGER_GROUP_CHAT_ID = "YOUR_LOGGER_ID"

# Replace with your support channel link and owner's Telegram ID
OWNER_SUPPORT_CHANNEL = "YOUR_SUPPORT_GC_OR_CHNL"
OWNER_TELEGRAM_ID = "OWNER_ID"

# MongoDB Client and Database
client = MongoClient(MONGO_URL)
db = client['bot_database']
users_collection = db['users']
private_groups_collection = db['private_groups']
public_groups_collection = db['public_groups']  # New collection for public groups
requests_collection = db['requests']  # To store user requests

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

    # Attractive welcome message with a photo
    welcome_text = (
        "*🎉 Welcome to Our Bot, {user_name}! 🎉*\n\n"
        "Hello, *{user_name}* 👋\n\n"
        "If you want to promote your group then /req <msg> <link> and send.\n\n"
        "🔹 Click below to access support or contact the owner directly!\n\n"
    ).format(user_name=update.message.from_user.first_name)

    # Send welcome message with a single photo
    photo_url = "https://graph.org/file/6c0db28a848ed4dacae56-93b1bc1873b2494eb2.jpg"  # Replace with actual photo URL
    await update.message.reply_photo(photo=photo_url, caption=welcome_text, parse_mode='Markdown')

    # Create an inline keyboard with links to support and the owner
    keyboard = [
        [InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ", url=OWNER_SUPPORT_CHANNEL)],
        [InlineKeyboardButton("Oᴡɴᴇʀ", url=f"tg://user?id={OWNER_TELEGRAM_ID}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the inline keyboard message
    await update.message.reply_text('Tap below to get support or contact the owner:', reply_markup=reply_markup)

    # Log the user who started the bot
    user_name = update.message.from_user.first_name
    user_username = update.message.from_user.username
    user_id = update.message.from_user.id
    log_message = (
        f"◈𝐍𝐀𝐌𝐄 {user_name}\n\n"
        f"(◈𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄: @{user_username if user_username else 'No Username'},\n\n"
        f"◈𝐈𝐃: {user_id}) ʜᴀs sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ"
    )
    if not os.environ.get("IS_VPS"):
        await context.bot.send_message(chat_id=LOGGER_GROUP_CHAT_ID, text=log_message)

    # Increment user count in MongoDB
    increment_user_count(user_id)

async def help_command(update: Update, context: CallbackContext) -> None:
    """Shows available commands to the user."""
    help_text = (
        "*Available Commands:*\n\n"
        "*User Commands:*\n"
        "1. /start - Start the bot\n"
        "2. /getpvt - Get random private group links\n"
        "3. /req <message> <link> - Send a request with your message and link to the owner\n\n"
    )

    keyboard = [
        [InlineKeyboardButton("🛠 Contact Support", url=OWNER_SUPPORT_CHANNEL)],
        [InlineKeyboardButton("💬 Message Owner", url=f"tg://user?id={OWNER_TELEGRAM_ID}")],
        [InlineKeyboardButton("Back", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send help message with commands and inline keyboard
    await update.message.reply_text(help_text, reply_markup=reply_markup)

    # If the user clicks "Back," return to the previous state or main options
    if update.callback_query and update.callback_query.data == "back":
        await update.callback_query.answer()
        # You can add logic to return to the initial bot options or menu here.

async def req(update: Update, context: CallbackContext) -> None:
    """User command to send a request message with their link to the owner."""
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    user_username = update.message.from_user.username

    if len(context.args) < 2:
        await update.message.reply_text("Please provide a message and a link. Usage: /req <message> <link>")
        return

    user_message = " ".join(context.args[:-1])  # Combine all arguments except the last one as message
    user_link = context.args[-1]  # Last argument as link

    # Save the request to MongoDB
    requests_collection.insert_one({"user_id": user_id, "message": user_message, "link": user_link})

    # Forward the request to the owner
    owner_message = (
        f"◈ 𝐔𝐬𝐞𝐫 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 ◈\n\n"
        f"◈ Name: {user_name}\n"
        f"◈ Username: @{user_username if user_username else 'No Username'}\n"
        f"◈ ID: {user_id}\n\n"
        f"◈ Message: {user_message}\n"
        f"◈ Link: {user_link}"
    )

    try:
        await context.bot.send_message(chat_id=OWNER_TELEGRAM_ID, text=owner_message)
        await update.message.reply_text("Your request has been sent to the owner successfully.")
    except Exception as e:
        logger.error(f"Error sending message to owner: {e}")
        await update.message.reply_text("There was an error sending your request to the owner. Please try again later.")

async def for_command(update: Update, context: CallbackContext) -> None:
    """Owner-only command to forward a user's message to the specified user."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Please provide the user ID and the message to forward. Usage: /for <user_id> <message>")
        return

    user_id = int(context.args[0])
    owner_message = " ".join(context.args[1:])

    try:
        await context.bot.send_message(user_id, owner_message)
        await update.message.reply_text(f"Message successfully forwarded to user {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"Error forwarding message: {e}")

from urllib.parse import urlparse

def is_valid_url(url):
    """Check if a given URL is valid."""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

# Dictionary to store the last execution time for users
user_last_getpvt_time = {}

async def getpvt(update: Update, context: CallbackContext) -> None:
    """Fetches random private group links with a 10-second delay for repeated use."""
    user_id = update.message.from_user.id
    current_time = datetime.now()

    # Check if the user has used the command before
    if user_id in user_last_getpvt_time:
        last_used_time = user_last_getpvt_time[user_id]
        time_diff = (current_time - last_used_time).total_seconds()

        # If the command is used within 10 seconds, send a delay message
        if time_diff < 10:
            await update.message.reply_text(
                f"⚠️ Please wait {10 - int(time_diff)} seconds before using this command again."
            )
            return

    # Update the last used time for the user
    user_last_getpvt_time[user_id] = current_time

    # Fetch all private group links from the database
    group_links = private_groups_collection.find()
    group_links_list = list(group_links)

    # Filter out invalid links
    valid_links = [link for link in group_links_list if is_valid_url(link.get('link', ''))]

    if len(valid_links) > 0:
        # Ensure we only sample the number of links available
        sample_size = min(10, len(valid_links))
        random_links = random.sample(valid_links, sample_size)

        # Dynamically create the keyboard based on the number of links
        keyboard = []
        for i in range(0, len(random_links), 5):  # Create rows with 5 buttons each
            row = [
                InlineKeyboardButton(f"Gᴄ{i + j + 1}", url=random_links[i + j]['link'])
                for j in range(min(5, len(random_links) - i))
            ]
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Tʜɪs ɪs Tʜᴇ 𝟷𝟶 ʀᴀɴᴅᴏᴍ ɢʀᴏᴜᴘ ʟɪɴᴋs\n\n"
            "Nᴏᴛᴇ ᴀғᴛᴇʀ 𝟷𝟶 sᴇᴄ ᴛʜᴇɴ ᴜsᴇ /getpvt ᴄᴏᴍᴍᴀɴᴅ\n\n"
            "Bᴇᴄᴀᴜsᴇ ᴏғ Tᴇᴀᴍ Sᴀɴᴋɪ ᴘᴏʟɪᴄʏ",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Nᴏ ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ ʟɪɴᴋs ᴀᴠᴀɪʟᴀʙʟᴇ ʏᴇᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ"
        )


async def getpublic(update: Update, context: CallbackContext) -> None:
    """Fetches random public group links with a 10-second delay for repeated use."""
    user_id = update.message.from_user.id
    current_time = datetime.now()

    # Check if the user has used the command before
    if user_id in user_last_getpublic_time:
        last_used_time = user_last_getpublic_time[user_id]
        time_diff = (current_time - last_used_time).total_seconds()

        # If the command is used within 10 seconds, send a delay message
        if time_diff < 10:
            await update.message.reply_text(
                f"⚠️ Please wait {10 - int(time_diff)} seconds before using this command again."
            )
            return

    # Update the last used time for the user
    user_last_getpublic_time[user_id] = current_time

    # Fetch all public group links from the database
    group_links = public_groups_collection.find()
    group_links_list = list(group_links)

    # Filter out invalid links
    valid_links = [link for link in group_links_list if is_valid_url(link.get('link', ''))]

    if len(valid_links) > 0:
        # Ensure we only sample the number of links available
        sample_size = min(10, len(valid_links))
        random_links = random.sample(valid_links, sample_size)

        # Dynamically create the keyboard based on the number of links
        keyboard = []
        for i in range(0, len(random_links), 5):  # Create rows with 5 buttons each
            row = [
                InlineKeyboardButton(f"Puʙʟɪᴄ Gᴄ{i + j + 1}", url=random_links[i + j]['link'])
                for j in range(min(5, len(random_links) - i))
            ]
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Tʜɪs ɪs Tʜᴇ 𝟷𝟶 ʀᴀɴᴅᴏᴍ ᴘᴜʙʟɪᴄ ɢʀᴏᴜᴘ ʟɪɴᴋs\n\n"
            "Nᴏᴛᴇ ᴀғᴛᴇʀ 𝟷𝟶 sᴇᴄ ᴛʜᴇɴ ᴜsᴇ /getpublic ᴄᴏᴍᴍᴀɴᴅ\n\n"
            "Bᴇᴄᴀᴜsᴇ ᴏғ Tᴇᴀᴍ Sᴀɴᴋɪ ᴘᴏʟɪᴄʏ",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Nᴏ ᴘᴜʙʟɪᴄ ɢʀᴏᴜᴘ ʟɪɴᴋs ᴀᴠᴀɪʟᴀʙʟᴇ ʏᴇᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ"
        )

async def broadcast(update: Update, context: CallbackContext) -> None:
    """Owner-only command to send a broadcast message to all users."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    # Check if the message contains the text to broadcast
    if not context.args:
        await update.message.reply_text("Please provide the message to broadcast.")
        return

    message = " ".join(context.args)

    # Variables to track success and blocked users
    total_users = 0
    successful_sends = 0
    blocked_users = 0

    # Send broadcast message to all users
    all_users = users_collection.find()
    for user in all_users:
        total_users += 1
        try:
            await context.bot.send_message(user['user_id'], message)
            successful_sends += 1
        except Exception as e:
            # Log the error and assume the user has blocked the bot
            blocked_users += 1
            logger.error(f"Error sending message to {user['user_id']}: {e}")

    # Send a summary message to the owner
    await update.message.reply_text(
        f"Broadcast complete!\n\n"
        f"Total users: {total_users}\n"
        f"Successfully sent: {successful_sends}\n"
        f"Blocked or failed: {blocked_users}"
    )


async def blckdel(update: Update, context: CallbackContext) -> None:
    """Owner-only command to delete users who have blocked the bot."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    # Track the number of blocked users removed
    removed_count = 0

    # Iterate through all users and check if the bot is blocked
    all_users = users_collection.find()
    for user in all_users:
        try:
            # Test if the bot can send a message
            await context.bot.send_chat_action(user['user_id'], "typing")
        except Exception as e:
            # Assume the user has blocked the bot and delete from database
            users_collection.delete_one({'user_id': user['user_id']})
            removed_count += 1
            logger.info(f"Removed blocked user: {user['user_id']} due to {e}")

    # Notify the owner of the cleanup
    await update.message.reply_text(
        f"Cleanup complete!\n\n"
        f"Removed {removed_count} users who had blocked the bot."
    )

async def stats(update: Update, context: CallbackContext) -> None:
    """Owner-only command to view bot statistics."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    # Get user count from MongoDB
    user_count = users_collection.count_documents({})

    # Get the number of requests in the database
    request_count = requests_collection.count_documents({})

    # Get the number of private groups in the database
    group_count = private_groups_collection.count_documents({})

    # Get the number of public groups in the database
    group_countpl = public_groups_collection.count_documents({})

    # Get uptime of the bot
    uptime = get_uptime()

    # Prepare the statistics message
    stats_message = (
        "*Bot Statistics:*\n\n"
        f"◈ Total number of users: {user_count}\n"
        f"◈ Total number of requests: {request_count}\n"
        f"◈ Total number of private groups: {group_count}\n"
        f"◈ Total number of public groups: {group_countpl}\n"
        f"◈ Uptime: {uptime}\n\n"
        "*Keep up the great work! 🚀* [Team Sanki](https://t.me/matalbi_duniya)"
    )
    # Send the statistics message
    await update.message.reply_text(stats_message)
  # Add private group link (Owner-only command)
async def addgc(update: Update, context: CallbackContext) -> None:
    """Owner-only command to add a private group link."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the private group link. Usage: /addgc <group_link>")
        return

    group_link = context.args[0]

    # Insert the private group link into MongoDB
    try:
        private_groups_collection.insert_one({"link": group_link})
        await update.message.reply_text(f"Private group link added: {group_link}")
    except Exception as e:
        await update.message.reply_text(f"Failed to add the group link. Error: {e}")


async def delgc(update: Update, context: CallbackContext) -> None:
    """Owner-only command to delete a private group link."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the private group link to delete. Usage: /delgc <group_link>")
        return

    group_link = context.args[0]

    # Delete the private group link from MongoDB
    try:
        result = private_groups_collection.delete_one({"link": group_link})
        if result.deleted_count > 0:
            await update.message.reply_text(f"Private group link deleted: {group_link}")
        else:
            await update.message.reply_text("The provided group link was not found.")
    except Exception as e:
        await update.message.reply_text(f"Failed to delete the group link. Error: {e}")


async def addpl(update: Update, context: CallbackContext) -> None:
    """Owner-only command to add a public group link."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the public group link. Usage: /addpl <group_link>")
        return

    group_link = context.args[0]

    # Insert the public group link into MongoDB
    try:
        public_groups_collection.insert_one({"link": group_link})
        await update.message.reply_text(f"Public group link added: {group_link}")
    except Exception as e:
        await update.message.reply_text(f"Failed to add the group link. Error: {e}")


async def delpl(update: Update, context: CallbackContext) -> None:
    """Owner-only command to delete a public group link."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the public group link to delete. Usage: /delpl <group_link>")
        return

    group_link = context.args[0]

    # Delete the public group link from MongoDB
    try:
        result = public_groups_collection.delete_one({"link": group_link})
        if result.deleted_count > 0:
            await update.message.reply_text(f"Public group link deleted: {group_link}")
        else:
            await update.message.reply_text("The provided group link was not found.")
    except Exception as e:
        await update.message.reply_text(f"Failed to delete the group link. Error: {e}")
    async def shift(update: Update, context: CallbackContext) -> None:
    """Owner-only command to shift links between public and private group collections."""
    if update.message.from_user.id != int(OWNER_TELEGRAM_ID):
        await update.message.reply_text("This command is restricted to the owner only.")
        return

    # Find all links in both collections
    private_group_links = private_groups_collection.find()
    public_group_links = public_groups_collection.find()

    # Counters for shifted links
    shifted_to_private = 0
    shifted_to_public = 0

    # Loop through private group links and check if any public links are incorrectly placed there
    for link in private_group_links:
        if is_valid_url(link.get('link', '')):
            # Check if the link should be in the public group collection
            if not is_valid_public_group(link['link']):
                try:
                    # Move the link to the public group collection
                    public_groups_collection.insert_one({"link": link['link']})
                    private_groups_collection.delete_one({"link": link['link']})
                    shifted_to_public += 1
                except Exception as e:
                    await update.message.reply_text(f"Error while shifting link: {e}")

    # Loop through public group links and check if any private links are incorrectly placed there
    for link in public_group_links:
        if is_valid_url(link.get('link', '')):
            # Check if the link should be in the private group collection
            if not is_valid_private_group(link['link']):
                try:
                    # Move the link to the private group collection
                    private_groups_collection.insert_one({"link": link['link']})
                    public_groups_collection.delete_one({"link": link['link']})
                    shifted_to_private += 1
                except Exception as e:
                    await update.message.reply_text(f"Error while shifting link: {e}")

    # Final message after shifting links
    if shifted_to_private > 0 or shifted_to_public > 0:
        await update.message.reply_text(f"Shifting complete!\n"
                                       f"Total links shifted to private collection: {shifted_to_private}\n"
                                       f"Total links shifted to public collection: {shifted_to_public}")
    else:
        await update.message.reply_text("No links needed shifting. Both collections are correct.")
  
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register the command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("req", req))
    application.add_handler(CommandHandler("getpvt", getpvt))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("for", for_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("addgc", addgc))
    application.add_handler(CommandHandler("addpublic", addpublic))
    application.add_handler(CommandHandler("getpublic", getpublic))
    application.add_handler(CommandHandler("delpl", delpl))
    application.add_handler(CommandHandler("delgc", delgc))
    application.add_handler(CommandHandler("shift", shift))

    # Run the bot
    application.run_polling()
  
if __name__ == '__main__':
    main()
