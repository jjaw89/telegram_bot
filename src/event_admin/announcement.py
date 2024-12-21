from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageEntity
)
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
import re

from .data_manager import save_events

# States
MAIN_MENU, NEW_EVENT_NAME, NEW_EVENT_START_ASK, NEW_EVENT_START_INPUT, \
NEW_EVENT_END_ASK, NEW_EVENT_END_INPUT, NEW_EVENT_CAPACITY_ASK, NEW_EVENT_CAPACITY_INPUT, \
NEW_EVENT_CONFIRM, NEW_EVENT_EDIT, NEW_EVENT_DISCARD_CONFIRM, MY_EVENTS, EVENT_MENU, \
ADD_ANNOUNCEMENT_TEXT, ADD_ANNOUNCEMENT_SHOW_SPOTS, ADD_ANNOUNCEMENT_SHOW_ATTENDING, ADD_ANNOUNCEMENT_PREVIEW,\
ADD_ANNOUNCEMENT_POST_CONFIRM = range(18)
# Callback data
YES = "yes"
NO = "no"
POST_ANNOUNCEMENT = "post_announcement"
SAVE_ANNOUNCEMENT = "save_announcement"
EDIT_ANNOUNCEMENT = "edit_announcement"
DISCARD_ANNOUNCEMENT = "discard_announcement"
POST_CONFIRM_YES = "post_confirm_yes"
POST_CONFIRM_NO = "post_confirm_no"

# Callback data patterns
BACK_TO_MAIN_MENU = "back_to_main_menu"
BACK_TO_MY_EVENTS = "back_to_my_events"

# Event menu actions (we'll define some basic ones; you can expand as needed)
SHOW_EVENT_INFO = "show_event_info"
ADD_ANNOUNCEMENT = "add_announcement"
PREVIEW_ANNOUNCEMENT = "preview_announcement"
POST_ANNOUNCEMENT = "post_announcement"
VIEW_ATTENDEES = "view_attendees"
MESSAGE_ATTENDEES = "message_attendees"
EDIT_EVENT = "edit_event"
DISCARD_EVENT = "discard_event"


async def start_add_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await update.effective_chat.send_message("What do you want your announcement to say?")
    return ADD_ANNOUNCEMENT_TEXT

async def announcement_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the text input for announcement."""
    text = update.message.text.strip()
    context.user_data["announcement_text"] = text
    # Check if the event has capacity
    event_id = context.user_data.get("selected_event_id")
    event = _find_event(context, event_id)
    if event is None:
        await update.effective_chat.send_message("Event not found.")
        return await show_event_menu(update, context, event_id)
    
    if event.get("capacity"):
        # Ask about showing spots remaining
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=YES), InlineKeyboardButton("No", callback_data=NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.effective_chat.send_message("Do you want to display the number of spots remaining?", reply_markup=keyboard)
        return ADD_ANNOUNCEMENT_SHOW_SPOTS
    else:
        # No capacity, ask about showing number of attendees
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=YES), InlineKeyboardButton("No", callback_data=NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.effective_chat.send_message("Do you want to display the number of attendees?", reply_markup=keyboard)
        return ADD_ANNOUNCEMENT_SHOW_ATTENDING

async def announcement_show_spots_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle yes/no for showing spots remaining."""
    query = update.callback_query
    await query.answer()
    data = query.data
    context.user_data["announcement_show_spots"] = (data == YES)

    # Now show preview
    return await show_announcement_preview(query, context)

async def announcement_show_attending_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle yes/no for showing number of attendees."""
    query = update.callback_query
    await query.answer()
    data = query.data
    context.user_data["announcement_show_attending"] = (data == YES)

    # Now show preview
    return await show_announcement_preview(query, context)

async def show_announcement_preview(query_or_update, context: ContextTypes.DEFAULT_TYPE, edited=False):
    """Show the preview of the announcement."""
    event_id = context.user_data.get("selected_event_id")
    event = _find_event(context, event_id)
    if event is None:
        if hasattr(query_or_update, "edit_message_text"):
            await query_or_update.edit_message_text("Event not found.")
        else:
            await query_or_update.message.reply_text("Event not found.")
        return await show_event_menu(query_or_update, context, event_id)

    ann_text = context.user_data["announcement_text"]
    show_spots = context.user_data.get("announcement_show_spots", False)
    show_attending = context.user_data.get("announcement_show_attending", False)

    # Construct preview text
    preview_text = ann_text + "\n\n"
    attendees_count = len(event.get("attendees", []))
    if event.get("capacity"):
        if show_spots:
            spots_remaining = event["capacity"] - attendees_count
            preview_text += f"Spots remaining: {spots_remaining}\n"
        if show_attending:
            # If capacity is set and user also chose show_attending (unlikely, but let's support it)
            preview_text += f"Number attending: {attendees_count}\n"
    else:
        # No capacity
        if show_attending:
            preview_text += f"Number attending: {attendees_count}\n"

    bot_username = context.bot.username
    preview_text += f"\n_In order to RSVP you must first message @{bot_username}._\n"

    # RSVP button (just for preview)
    preview_text += "[RSVP] (this button does nothing in preview)"

    buttons = [
        [InlineKeyboardButton("Post Announcement", callback_data=POST_ANNOUNCEMENT)],
        [InlineKeyboardButton("Save", callback_data=SAVE_ANNOUNCEMENT),
         InlineKeyboardButton("Edit", callback_data=EDIT_ANNOUNCEMENT)],
        [InlineKeyboardButton("Discard", callback_data=DISCARD_ANNOUNCEMENT)]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we came from callback_query:
    if hasattr(query_or_update, "edit_message_text"):
        await query_or_update.edit_message_text(preview_text, reply_markup=keyboard, parse_mode='Markdown')
    else:
        await query_or_update.message.reply_text(preview_text, reply_markup=keyboard, parse_mode='Markdown')

    return ADD_ANNOUNCEMENT_PREVIEW

async def announcement_preview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses in the announcement preview."""
    query = update.callback_query
    await query.answer()
    data = query.data

    event_id = context.user_data.get("selected_event_id")

    if data == POST_ANNOUNCEMENT:
        # Confirm posting
        await query.edit_message_text(f"Are you sure you want to post this announcement?")
        buttons = [
            [InlineKeyboardButton("Yes", callback_data=POST_CONFIRM_YES), InlineKeyboardButton("No", callback_data=POST_CONFIRM_NO)]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_reply_markup(keyboard)
        return ADD_ANNOUNCEMENT_POST_CONFIRM

    elif data == SAVE_ANNOUNCEMENT:
        # Save announcement without posting
        return await save_announcement(context, query, event_id, posted=False)

    elif data == EDIT_ANNOUNCEMENT:
        # Go back to step 1: ask text again
        await query.edit_message_text("What do you want your announcement to say?")
        return ADD_ANNOUNCEMENT_TEXT

    elif data == DISCARD_ANNOUNCEMENT:
        # Discard and return to event menu
        _clear_announcement_data(context)
        await query.edit_message_text("Announcement discarded.")
        return await show_event_menu(update, context, event_id)

async def announcement_post_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation of posting announcement."""
    query = update.callback_query
    await query.answer()
    data = query.data
    event_id = context.user_data.get("selected_event_id")

    if data == POST_CONFIRM_YES:
        # Post the announcement in the announcement channel
        await post_announcement(context, query, event_id)
        return await show_event_menu(update, context, event_id)
    else:
        # No, go back to preview
        return await show_announcement_preview(query, context, edited=True)

async def post_announcement(context: ContextTypes.DEFAULT_TYPE, query, event_id: int):
    """Post the announcement to the announcement channel and save message_id."""
    event = _find_event(context, event_id)
    if event is None:
        await query.edit_message_text("Event not found.")
        return

    ann_text = context.user_data["announcement_text"]
    show_spots = context.user_data.get("announcement_show_spots", False)
    show_attending = context.user_data.get("announcement_show_attending", False)
    attendees_count = len(event.get("attendees", []))

    # Construct the final announcement text
    final_text = ann_text + "\n\n"
    if event.get("capacity"):
        if show_spots:
            spots_remaining = event["capacity"] - attendees_count
            final_text += f"Spots remaining: {spots_remaining}\n"
        if show_attending:
            final_text += f"Number attending: {attendees_count}\n"
    else:
        if show_attending:
            final_text += f"Number attending: {attendees_count}\n"

    bot_username = context.bot.username
    final_text += f"\n_In order to RSVP you must first message @{bot_username}._\n"

    # Add RSVP button
    # Actual RSVP button that user clicks to RSVP
    # For now, we just mention it. Later, you might add InlineKeyboardButton that triggers RSVP logic.
    rsvp_button = [[InlineKeyboardButton("RSVP", callback_data=f"rsvp_{event_id}")]]
    rsvp_keyboard = InlineKeyboardMarkup(rsvp_button)

    from config.config import chat_ids  # assuming config contains announcement chat info
    ann_chat_id = chat_ids["announcements"]

    msg = await context.bot.send_message(
        chat_id=ann_chat_id,
        text=final_text,
        parse_mode='Markdown',
        reply_markup=rsvp_keyboard
    )

    # Save announcement info to event
    event["announcement_text"] = ann_text
    event["announcement_show_spots"] = show_spots
    event["announcement_show_attending"] = show_attending
    event["announcement_message_id"] = msg.message_id
    save_events(context)

    _clear_announcement_data(context)

    await query.edit_message_text("Announcement posted.")

async def save_announcement(context: ContextTypes.DEFAULT_TYPE, query, event_id: int, posted=False):
    """Save the announcement without posting."""
    event = _find_event(context, event_id)
    if event is None:
        await query.edit_message_text("Event not found.")
        return ADD_ANNOUNCEMENT_PREVIEW

    ann_text = context.user_data["announcement_text"]
    show_spots = context.user_data.get("announcement_show_spots", False)
    show_attending = context.user_data.get("announcement_show_attending", False)

    event["announcement_text"] = ann_text
    event["announcement_show_spots"] = show_spots
    event["announcement_show_attending"] = show_attending
    # No announcement_message_id since not posted
    save_events(context)
    _clear_announcement_data(context)

    await query.edit_message_text("Announcement saved (not posted).")
    return await show_event_menu(query, context, event_id)

async def show_event_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Show the event menu for a specific event."""
    event = None
    for e in context.bot_data.get("events", []):
        if e["id"] == event_id:
            event = e
            break

    if not event:
        if update.callback_query:
            await update.callback_query.edit_message_text("Event not found.")
        else:
            await update.message.reply_text("Event not found.")
        # Go back to MY_EVENTS since event is missing
        return MY_EVENTS

    # Display basic info
    text = (
        f"Name: {event['name']}\n"
        f"Start: {event.get('start','None')}\n"
        f"End: {event.get('end','None')}\n"
        f"Capacity: {event.get('capacity','None')}\n"
    )

    # Build the event menu buttons depending on event state.
    # For now, let's just add placeholders. Later you can add logic if announcement is posted etc.
    buttons = [
        [InlineKeyboardButton("Event Info", callback_data=SHOW_EVENT_INFO)]
    ]

    # If no announcement key, assume none created
    if "announcement_text" not in event:
        buttons.append([InlineKeyboardButton("Add Announcement", callback_data=ADD_ANNOUNCEMENT)])
    else:
        # Announcement created. Check if posted:
        if "announcement_message_id" in event:
            # Announcement posted
            buttons.append([InlineKeyboardButton("View Attendees", callback_data=VIEW_ATTENDEES)])
            buttons.append([InlineKeyboardButton("Message Attendees", callback_data=MESSAGE_ATTENDEES)])
            # Optionally "Edit Announcement"
            buttons.append([InlineKeyboardButton("Edit Announcement", callback_data="edit_announcement")])
        else:
            # Announcement not posted yet
            buttons.append([InlineKeyboardButton("Preview Announcement", callback_data=PREVIEW_ANNOUNCEMENT)])
            buttons.append([InlineKeyboardButton("Post Announcement", callback_data=POST_ANNOUNCEMENT)])

    # RSVP Message, Waitlist Message if needed
    # buttons.append([...]) depending on your logic

    # Always:
    buttons.append([InlineKeyboardButton("Edit Event", callback_data=EDIT_EVENT)])
    buttons.append([InlineKeyboardButton("Discard Event", callback_data=DISCARD_EVENT)])
    buttons.append([InlineKeyboardButton("<< Back to My Events", callback_data=BACK_TO_MY_EVENTS)])
    buttons.append([InlineKeyboardButton("Back to Main Menu", callback_data=BACK_TO_MAIN_MENU)])

    keyboard = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

    return EVENT_MENU

def _clear_announcement_data(context: ContextTypes.DEFAULT_TYPE):
    """Remove temporary announcement data from user_data."""
    context.user_data.pop("announcement_text", None)
    context.user_data.pop("announcement_show_spots", None)
    context.user_data.pop("announcement_show_attending", None)

def _find_event(context: ContextTypes.DEFAULT_TYPE, event_id: int):
    events = context.bot_data.get("events", [])
    for e in events:
        if e["id"] == event_id:
            return e
    return None
