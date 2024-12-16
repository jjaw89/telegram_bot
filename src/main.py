import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import config
from handlers.rules import rules_command, rules_callback
from handlers.admins import admins_command, admins_callback
from handlers.links import links_command
# You can add other handlers (like /start, /help) as they are created.
# For now, we will just implement a simple /help and /start to verify the bot works.
# Also implement /stars as requested.

# Enable logging to help debug
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
        "/links - Show some useful links."
    )
    await update.message.reply_text(help_text)


def main():
    token = config.token
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", rules_command))
    app.add_handler(CallbackQueryHandler(rules_callback, pattern='^rules:'))
    
    # Add the new /admins command and its callback
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(CallbackQueryHandler(admins_callback, pattern='^admins:'))
    
    app.add_handler(CommandHandler("links", links_command))
    app.run_polling()

if __name__ == "__main__":
    main()