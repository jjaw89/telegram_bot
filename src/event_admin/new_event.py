import re
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

from .data_manager import save_events, load_events
from .data_manager import is_event_admin

# States (example, these should match your __init__.py state definitions)
MAIN_MENU, NEW_EVENT_NAME, NEW_EVENT_START_ASK, NEW_EVENT_START_INPUT, \
NEW_EVENT_END_ASK, NEW_EVENT_END_INPUT, NEW_EVENT_CAPACITY_ASK, NEW_EVENT_CAPACITY_INPUT, \
NEW_EVENT_CONFIRM, NEW_EVENT_EDIT, NEW_EVENT_DISCARD_CONFIRM = range(11)

# Callback data
CANCEL_NEW_EVENT = "cancel_new_event"
HAS_START_YES = "has_start_yes"
HAS_START_NO = "has_start_no"
HAS_END_YES = "has_end_yes"
HAS_END_NO = "has_end_no"
HAS_CAPACITY_YES = "has_capacity_yes"
HAS_CAPACITY_NO = "has_capacity_no"
SAVE_EVENT = "save_event"
EDIT_EVENT = "edit_event"
DISCARD_EVENT = "discard_event"
DISCARD_YES = "discard_yes"
DISCARD_NO = "discard_no"
EDIT_NAME = "edit_name"
EDIT_START = "edit_start"
EDIT_END = "edit_end"
EDIT_CAPACITY = "edit_capacity"
BACK_TO_MAIN_MENU = "back_to_main_menu"

DATE_REGEX = r'^\d{2}:\d{2}\s\d{2}\/\d{2}\/\d{4}$'  # Simplistic validation: HH:MM DD/MM/YY
# You may add more robust validation later

async def ask_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the user for the event name."""
    context.user_data["new_event"] = {}
    buttons = [[InlineKeyboardButton("Cancel new event", callback_data=CANCEL_NEW_EVENT)]]
    keyboard = InlineKeyboardMarkup(buttons)

    # Since we're coming from a callback query (selected "New Event"),
    # update.message is None. Use effective_chat to send a new message.
    await update.effective_chat.send_message("What is the name of the event?", reply_markup=keyboard)
    return NEW_EVENT_NAME


async def new_event_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event name input."""
    event_name = update.message.text.strip()

    # Check duplicates
    for e in context.bot_data.get("events", []):
        if e["name"].lower() == event_name.lower():
            await update.message.reply_text("An event with that name already exists. Please choose a different name.")
            return NEW_EVENT_NAME

    context.user_data["new_event"]["name"] = event_name
    # Ask if event has a start date/time
    buttons = [
        [InlineKeyboardButton("Yes", callback_data=HAS_START_YES), InlineKeyboardButton("No", callback_data=HAS_START_NO)]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Does the event have a start date/time?", reply_markup=keyboard)
    return NEW_EVENT_START_ASK

async def start_ask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle yes/no for start date."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == HAS_START_YES:
        await query.edit_message_text("When does the event start? Please use a 24-hour clock, format: HH:MM DD/MM/YYYY")
        return NEW_EVENT_START_INPUT
    else:
        # No start date
        context.user_data["new_event"]["start"] = None
        # Ask for end date
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=HAS_END_YES), InlineKeyboardButton("No", callback_data=HAS_END_NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Does the event have an end date/time?", reply_markup=keyboard)
        return NEW_EVENT_END_ASK

async def start_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start date input."""
    text = update.message.text.strip()
    if not re.match(DATE_REGEX, text):
        await update.message.reply_text("Invalid date format. Please use HH:MM DD/MM/YYYY")
        return NEW_EVENT_START_INPUT

    context.user_data["new_event"]["start"] = text
    # Ask for end date
    buttons = [
        [InlineKeyboardButton("Yes", callback_data=HAS_END_YES), InlineKeyboardButton("No", callback_data=HAS_END_NO)]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Does the event have an end date/time?", reply_markup=keyboard)
    return NEW_EVENT_END_ASK

async def end_ask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle yes/no for end date."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == HAS_END_YES:
        await query.edit_message_text("When does the event end? Please use a 24-hour clock, format: HH:MM DD/MM/YYYY")
        return NEW_EVENT_END_INPUT
    else:
        # No end date
        context.user_data["new_event"]["end"] = None
        # Ask capacity
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=HAS_CAPACITY_YES), InlineKeyboardButton("No", callback_data=HAS_CAPACITY_NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Does the event have a limited capacity?", reply_markup=keyboard)
        return NEW_EVENT_CAPACITY_ASK

async def end_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle end date input."""
    text = update.message.text.strip()
    if not re.match(DATE_REGEX, text):
        await update.message.reply_text("Invalid date format. Please use HH:MM DD/MM/YYYY")
        return NEW_EVENT_END_INPUT

    context.user_data["new_event"]["end"] = text
    # Ask capacity
    buttons = [
        [InlineKeyboardButton("Yes", callback_data=HAS_CAPACITY_YES), InlineKeyboardButton("No", callback_data=HAS_CAPACITY_NO)]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Does the event have a limited capacity?", reply_markup=keyboard)
    return NEW_EVENT_CAPACITY_ASK

async def capacity_ask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle yes/no for capacity."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == HAS_CAPACITY_YES:
        await query.edit_message_text("What is the capacity of the event? (Enter a positive integer)")
        return NEW_EVENT_CAPACITY_INPUT
    else:
        # No capacity
        context.user_data["new_event"]["capacity"] = None
        # Show summary
        return await show_event_summary(query, context)

async def capacity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle capacity input."""
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("Invalid capacity. Please enter a positive integer.")
        return NEW_EVENT_CAPACITY_INPUT

    context.user_data["new_event"]["capacity"] = int(text)
    # Show summary
    await show_event_summary(update, context, message_type="message")
    return NEW_EVENT_CONFIRM

async def show_event_summary(update_or_query, context: ContextTypes.DEFAULT_TYPE, message_type="query"):
    """Show the final summary of the event before saving."""
    event = context.user_data["new_event"]
    name = event["name"]
    start = event.get("start", "None")
    end = event.get("end", "None")
    capacity = event.get("capacity", "None")

    text = (f"Here is your event:\n"
            f"Name: {name}\n"
            f"Start: {start}\n"
            f"End: {end}\n"
            f"Capacity: {capacity}")

    buttons = [
        [InlineKeyboardButton("Save Event", callback_data=SAVE_EVENT),
         InlineKeyboardButton("Edit Event", callback_data=EDIT_EVENT)],
        [InlineKeyboardButton("Discard Event", callback_data=DISCARD_EVENT)],
        [InlineKeyboardButton("<< Back to Main Menu", callback_data=BACK_TO_MAIN_MENU)]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if message_type == "query":
        await update_or_query.edit_message_text(text, reply_markup=keyboard)
    else:
        # It's a message (from capacity input)
        await update_or_query.message.reply_text(text, reply_markup=keyboard)

    return NEW_EVENT_CONFIRM

async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the callback from the final summary screen."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == SAVE_EVENT:
        return await save_new_event(query, context)
    elif data == EDIT_EVENT:
        return await show_edit_menu(query, context)
    elif data == DISCARD_EVENT:
        return await discard_event_confirm(query, context)
    elif data == BACK_TO_MAIN_MENU:
        # Back to main menu logic (assumes a function show_main_menu is defined)
        from .main_menu import show_main_menu
        return await show_main_menu(update, context)
    else:
        await query.edit_message_text("Unknown action.")
        return NEW_EVENT_CONFIRM

async def save_new_event(query, context: ContextTypes.DEFAULT_TYPE):
    """Save the newly created event."""
    event = context.user_data["new_event"]
    # Assign an ID, store in bot_data
    events = context.bot_data.get("events", [])
    new_id = max([e["id"] for e in events], default=0) + 1
    event_data = {
        "id": new_id,
        "name": event["name"],
        "start": event["start"],
        "end": event["end"],
        "capacity": event["capacity"],
        "attendees": [],
        "waitlist": []
    }
    events.append(event_data)
    context.bot_data["events"] = events
    save_events(context)

    await query.edit_message_text("Event saved.")

    # Clear the new_event from user_data
    context.user_data.pop("new_event", None)

    # Now go to the event’s main menu
    # Assume we have a function show_event_menu(event_id) in another file
    from .my_events import show_event_menu
    return await show_event_menu(query, context, event_data["id"])

async def show_edit_menu(query, context: ContextTypes.DEFAULT_TYPE):
    """Show the edit menu."""
    buttons = [
        [InlineKeyboardButton("Name", callback_data=EDIT_NAME)],
        [InlineKeyboardButton("Start", callback_data=EDIT_START)],
        [InlineKeyboardButton("End", callback_data=EDIT_END)],
        [InlineKeyboardButton("Capacity", callback_data=EDIT_CAPACITY)],
        [InlineKeyboardButton("<< Back", callback_data="edit_back")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text("What would you like to edit?", reply_markup=keyboard)
    return NEW_EVENT_EDIT

async def edit_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit menu callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == EDIT_NAME:
        await query.edit_message_text("Enter a new name for the event:")
        return NEW_EVENT_NAME
    elif data == EDIT_START:
        # Reset start
        context.user_data["new_event"]["start"] = None
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=HAS_START_YES), InlineKeyboardButton("No", callback_data=HAS_START_NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Does the event have a start date/time?", reply_markup=keyboard)
        return NEW_EVENT_START_ASK
    elif data == EDIT_END:
        context.user_data["new_event"]["end"] = None
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=HAS_END_YES), InlineKeyboardButton("No", callback_data=HAS_END_NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Does the event have an end date/time?", reply_markup=keyboard)
        return NEW_EVENT_END_ASK
    elif data == EDIT_CAPACITY:
        context.user_data["new_event"]["capacity"] = None
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=HAS_CAPACITY_YES), InlineKeyboardButton("No", callback_data=HAS_CAPACITY_NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Does the event have a limited capacity?", reply_markup=keyboard)
        return NEW_EVENT_CAPACITY_ASK
    elif data == "edit_back":
        # Back to summary
        return await show_event_summary(query, context)
    else:
        await query.edit_message_text("Unknown action.")
        return NEW_EVENT_EDIT

async def discard_event_confirm(query, context: ContextTypes.DEFAULT_TYPE):
    """Ask for confirmation before discarding."""
    buttons = [
        [InlineKeyboardButton("Yes", callback_data=DISCARD_YES), InlineKeyboardButton("No", callback_data=DISCARD_NO)]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text("Are you sure?", reply_markup=keyboard)
    return NEW_EVENT_DISCARD_CONFIRM

async def discard_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle discard confirmation."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == DISCARD_YES:
        # Discard and return to main menu
        context.user_data.pop("new_event", None)
        await query.edit_message_text("Event discarded.")
        from .main_menu import show_main_menu
        return await show_main_menu(update, context)
    else:
        # No discard, back to summary
        return await show_event_summary(query, context)

async def cancel_new_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel event from the name prompt."""
    query = update.callback_query
    await query.answer()
    if query.data == CANCEL_NEW_EVENT:
        context.user_data.pop("new_event", None)
        await query.edit_message_text("Event creation cancelled.")
        from .main_menu import show_main_menu
        return await show_main_menu(update, context)
    return NEW_EVENT_NAME


# Handler registration example (in __init__.py or similar):
# Assuming you have states defined:
#
# conv_handler = ConversationHandler(
#     entry_points=[CommandHandler("eventadmin", start_eventadmin)],
#     states={
#         NEW_EVENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_event_name_input),
#                          CallbackQueryHandler(cancel_new_event_callback, pattern='^cancel_new_event$')],
#         NEW_EVENT_START_ASK: [CallbackQueryHandler(start_ask_callback, pattern='^(has_start_yes|has_start_no)$')],
#         NEW_EVENT_START_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_date_input)],
#         NEW_EVENT_END_ASK: [CallbackQueryHandler(end_ask_callback, pattern='^(has_end_yes|has_end_no)$')],
#         NEW_EVENT_END_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_date_input)],
#         NEW_EVENT_CAPACITY_ASK: [CallbackQueryHandler(capacity_ask_callback, pattern='^(has_capacity_yes|has_capacity_no)$')],
#         NEW_EVENT_CAPACITY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, capacity_input)],
#         NEW_EVENT_CONFIRM: [CallbackQueryHandler(confirm_callback, pattern='^(save_event|edit_event|discard_event|back_to_main_menu)$')],
#         NEW_EVENT_EDIT: [CallbackQueryHandler(edit_event_callback, pattern='^(edit_name|edit_start|edit_end|edit_capacity|edit_back)$'),
#                          MessageHandler(filters.TEXT & ~filters.COMMAND, new_event_name_input)], # For name editing
#         NEW_EVENT_DISCARD_CONFIRM: [CallbackQueryHandler(discard_confirm_callback, pattern='^(discard_yes|discard_no)$')],
#     },
#     fallbacks=[CommandHandler("stop", stop_command)],
#     allow_reentry=True
# )
