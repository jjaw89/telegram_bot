import json
from typing import Dict, Any, Optional
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
from config import config


# States (example enumeration)
MAIN_MENU, NEW_EVENT_NAME, NEW_EVENT_START, NEW_EVENT_END, NEW_EVENT_CAPACITY, EVENT_CONFIRM, \
MY_EVENTS, EVENT_MENU, EVENT_EDIT, ANNOUNCEMENT_CREATE, ANNOUNCEMENT_PREVIEW, \
ANNOUNCEMENT_EDIT, RSVP_MESSAGE_EDIT, WAITLIST_MESSAGE_EDIT, MESSAGE_ATTENDEES, \
VIEW_ATTENDEES, EVENT_INFO = range(17)

# We will have patterns or callback_data keys like:
CALLBACK_NEW_EVENT = "new_event"
CALLBACK_MY_EVENTS = "my_events"
CALLBACK_BACK = "back"
CALLBACK_SAVE_EVENT = "save_event"
CALLBACK_EDIT_EVENT = "edit_event"
CALLBACK_DISCARD_EVENT = "discard_event"
CALLBACK_ADD_ANNOUNCEMENT = "add_announcement"
CALLBACK_PREVIEW_ANNOUNCEMENT = "preview_announcement"
CALLBACK_POST_ANNOUNCEMENT = "post_announcement"
CALLBACK_SHOW_EVENT_INFO = "show_event_info"
CALLBACK_VIEW_ATTENDEES = "view_attendees"
CALLBACK_MESSAGE_ATTENDEES = "message_attendees"
CALLBACK_RSVP_MESSAGE = "rsvp_message"
CALLBACK_WAITLIST_MESSAGE = "waitlist_message"

DATA_FILE = "events_data.json"

events = {}

# ------------------ Persistence Functions ------------------
def load_data() -> Dict[str, Any]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"events": []}

def save_data(data: Dict[str, Any]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Example data structure for events:
# data = {
#   "events": [
#       {
#           "id": 1,
#           "name": "My Event",
#           "start": "13:00 25/12/24",
#           "end": "15:00 25/12/24",
#           "capacity": 20,
#           "announcement_text": "...",
#           "announcement_show_spots": True,
#           "announcement_show_attending": False,
#           "announcement_message_id": 12345,
#           "rsvp_message_template": "...",
#           "waitlist_message_template": "...",
#           "attendees": [ { "user_id": ..., "username": "@User1" }, ... ],
#           "waitlist": [ ... ]
#       }
#   ]
# }

# ------------------ Utility Functions ------------------
def is_event_admin(user_id: int) -> bool:
    # Check from config or database
    event_admins = config.event_admins
    return user_id in event_admins

def get_events(context: ContextTypes.DEFAULT_TYPE) -> list:
    return context.bot_data.get("events", [])

def save_events(context: ContextTypes.DEFAULT_TYPE):
    data = {"events": context.bot_data.get("events", [])}
    save_data(data)

def find_event_by_id(context: ContextTypes.DEFAULT_TYPE, event_id: int) -> Optional[Dict]:
    for e in context.bot_data.get("events", []):
        if e["id"] == event_id:
            return e
    return None

def generate_event_id(context: ContextTypes.DEFAULT_TYPE) -> int:
    events = get_events(context)
    if not events:
        return 1
    return max(e["id"] for e in events) + 1

# ------------------ Handlers ------------------

async def start_event_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /eventadmin command."""
    # Check the user is an event admin
    user_id = update.effective_user.id
    if not is_event_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END
    # Check that the user is in a private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Please message me in a private chat.")
        return
    await show_main_menu(update, context)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the main menu."""
    buttons = [
        [InlineKeyboardButton("New Event", callback_data=CALLBACK_NEW_EVENT)],
        [InlineKeyboardButton("My Events", callback_data=CALLBACK_MY_EVENTS)],
        # [InlineKeyboardButton("Event Info", callback_data=CALLBACK_SHOW_EVENT_INFO)], # Only relevant if an event is selected. May omit here.
        [InlineKeyboardButton("Close", callback_data="close")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Please select an option:", reply_markup=keyboard)
    else:
        await update.message.reply_text("Please select an option:", reply_markup=keyboard)

    return MAIN_MENU

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == CALLBACK_NEW_EVENT:
        # Go to new event creation flow
        await query.edit_message_text("What is the name of the event?")
        context.user_data["new_event"] = {}
        return NEW_EVENT_NAME
    elif data == CALLBACK_MY_EVENTS:
        return await show_my_events(update, context)
    elif data == "close":
        await query.edit_message_text("Okay, bye.")
        return ConversationHandler.END
    else:
        # Unknown callback
        await query.edit_message_text("Unknown command.")
        return MAIN_MENU

async def show_my_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = get_events(context)
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(e["name"], callback_data=f"select_event_{e['id']}")])
    buttons.append([InlineKeyboardButton("<< Back", callback_data=CALLBACK_BACK)])
    keyboard = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Here are your events:", reply_markup=keyboard)
    else:
        await update.message.reply_text("Here are your events:", reply_markup=keyboard)
    return MY_EVENTS

async def my_events_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == CALLBACK_BACK:
        return await show_main_menu(update, context)

    if data.startswith("select_event_"):
        event_id = int(data.split("_")[-1])
        context.user_data["selected_event_id"] = event_id
        return await show_event_menu(update, context, event_id)

    # Unknown
    await query.edit_message_text("Unknown action.")
    return MY_EVENTS

async def show_event_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    event = find_event_by_id(context, event_id)
    if not event:
        await update.callback_query.edit_message_text("Event not found.")
        return MY_EVENTS

    text = f"Name: {event['name']}\n"
    text += f"Start: {event.get('start', 'None')}\n"
    text += f"End: {event.get('end', 'None')}\n"
    text += f"Capacity: {event.get('capacity', 'None')}\n"

    # Build event menu based on state
    buttons = [
        [InlineKeyboardButton("Event Info", callback_data=CALLBACK_SHOW_EVENT_INFO)]
    ]
    # Announcement logic
    if "announcement_text" not in event:
        buttons.append([InlineKeyboardButton("Add Announcement", callback_data=CALLBACK_ADD_ANNOUNCEMENT)])
    else:
        # Announcement exists
        if "announcement_message_id" in event:
            # Posted
            buttons.append([InlineKeyboardButton("View Attendees", callback_data=CALLBACK_VIEW_ATTENDEES)])
            buttons.append([InlineKeyboardButton("Message Attendees", callback_data=CALLBACK_MESSAGE_ATTENDEES)])
            buttons.append([InlineKeyboardButton("Edit Announcement", callback_data="edit_announcement")])
        else:
            # Not posted yet
            buttons.append([InlineKeyboardButton("Preview Announcement", callback_data=CALLBACK_PREVIEW_ANNOUNCEMENT)])
            buttons.append([InlineKeyboardButton("Post Announcement", callback_data=CALLBACK_POST_ANNOUNCEMENT)])

    # RSVP Message
    buttons.append([InlineKeyboardButton("RSVP Message", callback_data=CALLBACK_RSVP_MESSAGE)])
    # Waitlist Message if capacity
    if event.get("capacity"):
        buttons.append([InlineKeyboardButton("Waitlist Message", callback_data=CALLBACK_WAITLIST_MESSAGE)])

    # Edit and Discard
    buttons.append([InlineKeyboardButton("Edit Event", callback_data=CALLBACK_EDIT_EVENT)])
    buttons.append([InlineKeyboardButton("Discard Event", callback_data=CALLBACK_DISCARD_EVENT)])
    # Back Buttons
    buttons.append([InlineKeyboardButton("<< Back to My Events", callback_data="back_to_my_events")])
    buttons.append([InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main_menu")])

    keyboard = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

    return EVENT_MENU

async def event_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    event_id = context.user_data.get("selected_event_id")
    if not event_id:
        # No event selected, go back
        return await show_my_events(update, context)

    if data == CALLBACK_SHOW_EVENT_INFO:
        # Show detailed event info
        event = find_event_by_id(context, event_id)
        if not event:
            await query.edit_message_text("Event not found.")
            return EVENT_MENU
        text = "Event Info:\n"
        text += f"Name: {event['name']}\nStart: {event.get('start','None')}\nEnd: {event.get('end','None')}\n"
        text += f"Capacity: {event.get('capacity','None')}\n"
        if "announcement_text" in event:
            text += f"Announcement: {event['announcement_text']}\n"
            posted = "Yes" if "announcement_message_id" in event else "No"
            text += f"Announcement Posted: {posted}\n"
        text += f"Attendees: {len(event.get('attendees',[]))}\n"
        if event.get('capacity'):
            text += f"Waitlist: {len(event.get('waitlist',[]))}\n"
        text += "RSVP Message: " + (event.get('rsvp_message_template',"Default RSVP message")) + "\n"
        if event.get('capacity'):
            text += "Waitlist Message: " + (event.get('waitlist_message_template',"Default Waitlist message")) + "\n"

        buttons = [[InlineKeyboardButton("<< Back", callback_data="event_menu_back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return EVENT_INFO

    elif data == "event_menu_back":
        return await show_event_menu(update, context, event_id)

    elif data == "back_to_my_events":
        return await show_my_events(update, context)
    elif data == "back_to_main_menu":
        return await show_main_menu(update, context)

    # Other callbacks like announcement adding, posting, RSVP message editing etc.
    # would be handled similarly. Due to length constraints, we won't implement all here,
    # but the pattern is the same: ask a question, set state, await response, etc.

    # For unknown or unimplemented actions:
    await query.edit_message_text("This action is not yet implemented.")
    return EVENT_MENU

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop command."""
    await update.message.reply_text("Okay, bye.")
    return ConversationHandler.END

        
def get_eventadmin_handlers():
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("eventadmin", start_event_admin)],
            states={
                MAIN_MENU: [CallbackQueryHandler(main_menu_callback)],
                MY_EVENTS: [CallbackQueryHandler(my_events_callback)],
                EVENT_MENU: [CallbackQueryHandler(event_menu_callback)],
                EVENT_INFO: [CallbackQueryHandler(event_menu_callback)],
                # Add other states and handlers for new event creation, editing, etc.
            },
            fallbacks=[CommandHandler("stop", stop)],
            map_to_parent={},
            allow_reentry=True
        )
        return conv_handler
        
    # application.add_handler(conv_handler)