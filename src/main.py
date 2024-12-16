"""
A telegram bot for Victoria Pups.
"""

import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

from handlers.admins import admins_command, go_back_to_admins_callback, role_callback
from handlers.rules import rules_command, rule_callback, go_back_to_rules_callback
from handlers.links import links_command 

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )
    
    
# In main() function, register the callback for go_back_to_rules
def main() -> None:
    """Start the bot."""
    application = Application.builder().token("8140908530:AAHPjCEVjOQzyrZ6D4rlQiszgKYgTRTa3U8").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rules", rules_command))
    application.add_handler(CommandHandler("links", links_command))
    application.add_handler(CommandHandler("admins", admins_command))

    application.add_handler(CallbackQueryHandler(role_callback, pattern="^role_"))
    application.add_handler(CallbackQueryHandler(go_back_to_admins_callback, pattern="^go_back_admins"))
    application.add_handler(CallbackQueryHandler(rule_callback, pattern="^rule_"))
    application.add_handler(CallbackQueryHandler(go_back_to_rules_callback, pattern="^go_back_rules"))

    application.run_polling()

if __name__ == "__main__":
    main()