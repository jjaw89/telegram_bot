import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import config
from handlers.rules import get_rules_handlers
from handlers.admins import admins_command, admins_callback
from handlers.links import links_command
from handlers.events import get_handlers as get_event_handlers
from event_admin.eventadmin import get_eventadmin_handlers

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
        "/rules - Show the group rules and navigate through them.\n"
        "/admins - Show the group admin rolls.\n"
        "/links - Show some useful links.\n"
        "/newevent - Create a new event (admin only in private chat)."
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

def main():
    token = config.token
    app = Application.builder().token(token).build()

    # Add basic handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    # app.add_handler(CommandHandler("rules", rules_command))
    # app.add_handler(CallbackQueryHandler(rules_callback, pattern='^rules:'))
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(CallbackQueryHandler(admins_callback, pattern='^admins:'))
    app.add_handler(CommandHandler("links", links_command))
    
    # Add a debug command handler (optional)
    app.add_handler(CommandHandler("debug", debug_command))

    # Add rules handlers:
    for h in get_rules_handlers():
        app.add_handler(h)

    # Add event_admin handlers:
    for h in get_eventadmin_handlers():
        app.add_handler(h)

    # Start polling after all handlers are registered
    app.run_polling()

if __name__ == "__main__":
    main()
