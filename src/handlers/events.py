from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)
from telegram.constants import ParseMode
from config import config

known_users = set()
admin_states = {}
events = {}
event_id_counter = 1

def escape_markdown_v2(text: str) -> str:
    to_escape = r"_*[]()~`>#+-=|{}.!"
    for ch in to_escape:
        text = text.replace(ch, f"\\{ch}")
    return text

async def newevent_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("You are not authorized to create an event.")
        return
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Please message me in a private chat to create an event.")
        return

    if user_id in admin_states and admin_states[user_id].get('step') == 'ready_to_post':
        await update.message.reply_text("You already have an event ready to post. Please /postpoll or /discard it before creating a new one.")
        return

    admin_states[user_id] = {'step': 'waiting_for_name'}
    await update.message.reply_text("Please send me the event name.")

async def discard_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("You are not authorized.")
        return
    if user_id not in admin_states:
        await update.message.reply_text("No event in progress to discard.")
        return

    del admin_states[user_id]
    await update.message.reply_text("Your in-progress event has been discarded.")

async def combined_message_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if update.effective_chat.type == 'private':
        known_users.add(user_id)

    if user_id not in admin_states:
        return

    step = admin_states[user_id]['step']

    if step == 'waiting_for_name':
        admin_states[user_id]['event_name'] = update.message.text.strip()
        admin_states[user_id]['step'] = 'waiting_for_date'
        await update.message.reply_text("Got it! Now send me the event date (e.g. YYYY-MM-DD).")

    elif step == 'waiting_for_date':
        admin_states[user_id]['event_date'] = update.message.text.strip()
        admin_states[user_id]['step'] = 'waiting_for_poll_text'
        await update.message.reply_text("Great! Now please send me the text that will appear before the poll.")

    elif step == 'waiting_for_poll_text':
        admin_states[user_id]['poll_text'] = update.message.text.strip()
        admin_states[user_id]['step'] = 'waiting_for_poll_options'
        await update.message.reply_text(
            "Send the poll options as: Yes Option; Maybe Option; No Option"
        )

    elif step == 'waiting_for_poll_options':
        text = update.message.text.strip()
        parts = [p.strip() for p in text.split(';')]
        if len(parts) != 3:
            await update.message.reply_text("Please provide three options separated by semicolons.")
            return

        admin_states[user_id]['poll_yes'] = parts[0]
        admin_states[user_id]['poll_maybe'] = parts[1]
        admin_states[user_id]['poll_no'] = parts[2]

        await update.message.reply_text(
            f"Event Name: {admin_states[user_id]['event_name']}\n"
            f"Event Date: {admin_states[user_id]['event_date']}\n"
            f"Poll Text: {admin_states[user_id]['poll_text']}\n"
            f"Yes: {admin_states[user_id]['poll_yes']}\n"
            f"Maybe: {admin_states[user_id]['poll_maybe']}\n"
            f"No: {admin_states[user_id]['poll_no']}\n\n"
            "If this looks good, type /postpoll to post the poll or /discard to cancel."
        )
        admin_states[user_id]['step'] = 'ready_to_post'


async def postpoll_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("You are not authorized.")
        return
    if user_id not in admin_states or admin_states[user_id].get('step') != 'ready_to_post':
        await update.message.reply_text("No event is ready to post. Create one with /newevent.")
        return

    global event_id_counter
    event_name = admin_states[user_id]['event_name']
    event_date = admin_states[user_id]['event_date']
    poll_text = admin_states[user_id]['poll_text']
    yes_option = admin_states[user_id]['poll_yes']
    maybe_option = admin_states[user_id]['poll_maybe']
    no_option = admin_states[user_id]['poll_no']

    # Escape all user-provided strings
    event_name_esc = escape_markdown_v2(event_name)
    event_date_esc = escape_markdown_v2(event_date)
    poll_text_esc = escape_markdown_v2(poll_text)
    yes_option_esc = escape_markdown_v2(yes_option)
    maybe_option_esc = escape_markdown_v2(maybe_option)
    no_option_esc = escape_markdown_v2(no_option)

    event_id = event_id_counter
    event_id_counter += 1

    events[event_id] = {
        'event_name': event_name,
        'event_date': event_date,
        'poll_text': poll_text,
        'poll_yes': yes_option,
        'poll_maybe': maybe_option,
        'poll_no': no_option,
        'responses': {'yes': set(), 'maybe': set(), 'no': set()},
        'message_id': None
    }

    keyboard = [
        [
            InlineKeyboardButton(yes_option_esc, callback_data=f"poll:yes:{event_id}"),
            InlineKeyboardButton(maybe_option_esc, callback_data=f"poll:maybe:{event_id}"),
            InlineKeyboardButton(no_option_esc, callback_data=f"poll:no:{event_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = f"*{event_name_esc}*\n{event_date_esc}\n\n{poll_text_esc}"

    msg = await context.bot.send_message(
        chat_id=config.group_chat_id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

    events[event_id]['message_id'] = msg.message_id
    await update.message.reply_text("Poll posted to the group!")

    # Clear admin state
    del admin_states[user_id]


async def poll_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    data = query.data.split(':')
    if len(data) != 3:
        await query.answer("Invalid data.")
        return

    choice = data[1]  
    event_id = int(data[2])

    if event_id not in events:
        await query.answer("Event not found.")
        return

    if user_id not in known_users:
        await query.answer("Please DM me first before voting.")
        return

    event = events[event_id]
    for ch in ['yes', 'maybe', 'no']:
        event['responses'][ch].discard(user_id)
    event['responses'][choice].add(user_id)

    await query.answer("Vote recorded!")


async def eventadmin_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("Not authorized.")
        return

    if not events:
        await update.message.reply_text("No active events.")
        return

    buttons = []
    for eid, ev in events.items():
        display_name = f"{ev['event_name']} ({ev['event_date']})"
        display_name_esc = escape_markdown_v2(display_name)
        buttons.append([InlineKeyboardButton(display_name_esc, callback_data=f"eventadmin:{eid}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Select an event:", reply_markup=reply_markup)


async def eventadmin_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(':')
    if len(data) != 2:
        await query.answer("Invalid data.")
        return

    event_id = int(data[1])
    if event_id not in events:
        await query.answer("Event not found.")
        return

    ev = events[event_id]
    text = f"Event: {ev['event_name']} ({ev['event_date']})\nChoose an option:"
    text_esc = escape_markdown_v2(text)
    keyboard = [
        [
            InlineKeyboardButton("Show Results", callback_data=f"eventopt:showresults:{event_id}"),
            InlineKeyboardButton("Delete Event", callback_data=f"eventopt:delete:{event_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text_esc,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )


async def eventopt_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(':')
    if len(data) != 3:
        await query.answer("Invalid data.")
        return
    action = data[1]
    event_id = int(data[2])

    if event_id not in events:
        await query.answer("Event not found.")
        return

    ev = events[event_id]

    if action == 'showresults':
        yes_count = len(ev['responses']['yes'])
        maybe_count = len(ev['responses']['maybe'])
        no_count = len(ev['responses']['no'])
        result_text = (
            f"Results for {ev['event_name']} ({ev['event_date']}):\n"
            f"{ev['poll_yes']}: {yes_count}\n"
            f"{ev['poll_maybe']}: {maybe_count}\n"
            f"{ev['poll_no']}: {no_count}\n"
        )
        result_text_esc = escape_markdown_v2(result_text)
        await query.answer()
        await query.edit_message_text(result_text_esc, parse_mode=ParseMode.MARKDOWN_V2)

    elif action == 'delete':
        del events[event_id]
        await query.answer("Event deleted.")
        await query.edit_message_text("Event deleted.")

def get_handlers():
    return [
        CommandHandler("newevent", newevent_command),
        CommandHandler("postpoll", postpoll_command),
        CommandHandler("discard", discard_command),
        CommandHandler("eventadmin", eventadmin_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, combined_message_handler),
        CallbackQueryHandler(poll_callback, pattern='^poll:'),
        CallbackQueryHandler(eventadmin_callback, pattern='^eventadmin:'),
        CallbackQueryHandler(eventopt_callback, pattern='^eventopt:')
    ]
