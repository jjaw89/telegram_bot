from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.ext import ContextTypes
from .data_manager import is_event_admin
# States enumeration from __init__.py:
# States
MAIN_MENU, NEW_EVENT_NAME, NEW_EVENT_START_ASK, NEW_EVENT_START_INPUT, \
NEW_EVENT_END_ASK, NEW_EVENT_END_INPUT, NEW_EVENT_CAPACITY_ASK, NEW_EVENT_CAPACITY_INPUT, \
NEW_EVENT_CONFIRM, NEW_EVENT_EDIT, NEW_EVENT_DISCARD_CONFIRM, MY_EVENTS, EVENT_MENU, \
ADD_ANNOUNCEMENT_TEXT, ADD_ANNOUNCEMENT_SHOW_SPOTS, ADD_ANNOUNCEMENT_SHOW_ATTENDING, ADD_ANNOUNCEMENT_PREVIEW,\
ADD_ANNOUNCEMENT_POST_CONFIRM = range(18)

async def start_eventadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_event_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("New Event", callback_data="new_event")],
        [InlineKeyboardButton("My Events", callback_data="my_events")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if update.message:
        await update.message.reply_text("Please select an option:", reply_markup=keyboard)
    else:
        # callback_query scenario
        await update.callback_query.edit_message_text("Please select an option:", reply_markup=keyboard)

    return MAIN_MENU

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "new_event":
        from .new_event import ask_event_name
        return await ask_event_name(update, context)
    elif data == "my_events":
        # Implement show_my_events in my_events.py
        from .my_events import show_my_events
        return await show_my_events(update, context)
    elif data == "close":
        await query.edit_message_text("Okay, bye.")
        return ConversationHandler.END
    else:
        await query.edit_message_text("Unknown command.")
        return 0  # MAIN_MENU
