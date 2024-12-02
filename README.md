# Telegram Bot

This is a simple Telegram bot that logs users' details (name, username, and user ID) to a specific logger group whenever a user starts the bot. It also provides a `/getgroup` command to fetch group links.

## Features:
- Logs user details (name, username, user ID) to a logger group when the bot is started.
- Provides a `/getgroup` command to get a group link.

## Requirements:
- Python 3.9+
- Install dependencies with: `pip install -r requirements.txt`

## Setup:
1. Replace `YOUR_BOT_TOKEN` with your bot token from BotFather in `bot.py`.
2. Replace `@your_logger_group_or_chat_id` with your logger group's chat ID or username.
3. Run the bot with: `python bot.py`
4. For deployment, use Heroku or Docker.

## Heroku Deployment:
1. Push the code to a new repository.
2. Deploy using `heroku create` and `git push heroku main`.

## Docker Deployment:
1. Build the Docker image: `docker build -t telegram-bot .`
2. Run the container: `docker run -p 80:80 telegram-bot`

3. MADE BY SANKI XD 
