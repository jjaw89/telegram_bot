from telegram import Update
from telegram.ext import ContextTypes

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