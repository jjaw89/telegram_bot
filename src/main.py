import json
import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import config
from handlers.rules import get_rules_handlers
from handlers.admins import admins_command, admins_callback
from handlers.links import links_command
from handlers.events import get_handlers as get_event_handlers
from event_admin import get_eventadmin_handlers

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update, context):
    """Respond to /start command with a friendly greeting."""
    await update.message.reply_text("Hello! I am the Victoria Pups Bot. How can I help you today?")

async def help_command(update, context):
    """Respond to /help command with a list of available commands."""
    help_text = (
        "Available commands:\n"
        "/start - Start interacting with the bot.\n"
        "/help - Show this help message.\n"
        "/rules - Post a summary of the rules. If posted in your private chat with the bot you can explore the full rules.\n"
        "/rulesadmin - From your own private chat with the bot you may post a full rule to the group chat.\n"
        "/postrule n - Posts full rule n (1 <= n <= 6).\n"
        "/admins - Show the group admin rolls.\n"
        "/links - Show some useful links.\n"
        "/debug - Print userID and chatID in the terminal."
    )
    await update.message.reply_text(help_text)

async def debug_command(update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    # Print to terminal
    print(f"Debug Info: Chat ID: {chat_id}, User ID: {user_id}")
    # If you don't want to send a message, you can just omit reply_text
    # Or optionally, you can send a small acknowledgment message:
    await update.message.reply_text("Debug info printed to terminal.")

# def main():
#     token = config.token
#     app = Application.builder().token(token).build()

#     # Add basic handlers
#     app.add_handler(CommandHandler("start", start_command))
#     app.add_handler(CommandHandler("help", help_command))
#     # app.add_handler(CommandHandler("rules", rules_command))
#     # app.add_handler(CallbackQueryHandler(rules_callback, pattern='^rules:'))
#     app.add_handler(CommandHandler("admins", admins_command))
#     app.add_handler(CallbackQueryHandler(admins_callback, pattern='^admins:'))
#     app.add_handler(CommandHandler("links", links_command))
    
#     # Add a debug command handler (optional)
#     app.add_handler(CommandHandler("debug", debug_command))

#     # Add rules handlers:
#     for h in get_rules_handlers():
#         app.add_handler(h)


#     app.add_handler(get_eventadmin_handlers())

#     # Start polling after all handlers are registered
#     app.run_polling()

# if __name__ == "__main__":
#     main()

def main():
    # Initialize the application
    token = config.token
    app = Application.builder().token(token).build()

    # Ensure data directory and file exists
    data_dir = os.path.join("data")
    os.makedirs(data_dir, exist_ok=True)
    data_file = os.path.join(data_dir, "events.json")

    if not os.path.exists(data_file):
        # Create empty data file
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({"events": []}, f, ensure_ascii=False, indent=4)

    # Load data into bot_data
    with open(data_file, 'r', encoding='utf-8') as f:
        app.bot_data = json.load(f)  # e.g. {"events": [...]}

    # Basic handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(CallbackQueryHandler(admins_callback, pattern='^admins:'))
    app.add_handler(CommandHandler("links", links_command))
    app.add_handler(CommandHandler("debug", debug_command))

    # Add rules handlers
    for h in get_rules_handlers():
        app.add_handler(h)

    # Add eventadmin handlers (the conversation handler)
    app.add_handler(get_eventadmin_handlers())

    # Start polling after all handlers are registered
    app.run_polling()

if __name__ == "__main__":
    main()