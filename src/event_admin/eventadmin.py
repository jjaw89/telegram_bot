from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
# from telegram.ext import (
#     CallbackContext, CommandHandler, MessageHandler, CallbackQueryHandler, filters
# )
from telegram.constants import ParseMode
from config import config


async def eventadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message asking the event admin what they want to do."""
    user_id = update.effective_user.id
    
    # Check that the user has permission to call the command
    if user_id not in config.event_admins:
        await update.message.reply_text("You are not an event admin.")
        return
    
    # Check that the user is in a private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Please message me in a private chat.")
        return
    
    keyboard = [
        [InlineKeyboardButton("Announce an event", callback_data="eventadmin:1")],
        [InlineKeyboardButton("Poll the group", callback_data="eventadmin:2")],
        [InlineKeyboardButton("Edit an event", callback_data="eventadmin:3")],
        [InlineKeyboardButton("Message attendees", callback_data="eventadmin:4")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("What would you like to do?", reply_markup=reply_markup)
    
async def eventadmin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback to prevent timeout
    
    data = query.data.split(":")
    for i in range(1,5):
        if query.split(":")[1] == f"{i}":
            await update.message.reply_text(f"You have selected option {i}")
    
        
def get_eventadmin_handlers():
    return [
        CommandHandler("eventadmin", eventadmin_command),
        CallbackQueryHandler(eventadmin_callback, pattern='^eventadmin:'),
        # CommandHandler("newevent", newevent_command),
        # CommandHandler("postpoll", postpoll_command),
        # CommandHandler("discard", discard_command),
        # CommandHandler("eventadmin", eventadmin_command),
        # MessageHandler(filters.TEXT & ~filters.COMMAND, combined_message_handler),
        # CallbackQueryHandler(poll_callback, pattern='^poll:'),
        # CallbackQueryHandler(eventadmin_callback, pattern='^eventadmin:'),
        # CallbackQueryHandler(eventopt_callback, pattern='^eventopt:'),
        # CallbackQueryHandler(msgopt_callback, pattern='^msgopt:')
    ]