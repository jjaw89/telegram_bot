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

# For messaging attendees
admin_messaging_states = {}
# admin_messaging_states[user_id] = {
#   'event_id': int,
#   'selected': set(['yes','maybe','no']),
#   'step': 'choose_recipients' | 'waiting_for_message'
# }

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
        await update.message.reply_text("Please message me in a private chat.")
        return

    if user_id in admin_states and admin_states[user_id].get('step') == 'ready_to_post':
        await update.message.reply_text("You already have an event ready to post. Please /postpoll or /discard it first.")
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

    # Check if admin is currently messaging attendees
    if user_id in admin_messaging_states:
        if admin_messaging_states[user_id]['step'] == 'waiting_for_message':
            # This message is the DM text
            message_text = update.message.text.strip()
            event_id = admin_messaging_states[user_id]['event_id']
            if event_id not in events:
                await update.message.reply_text("Event not found, unable to send message.")
                del admin_messaging_states[user_id]
                return

            ev = events[event_id]
            selected = admin_messaging_states[user_id]['selected']

            # Collect user_ids
            user_ids = set()
            for cat in selected:
                user_ids |= ev['responses'][cat]

            # Send DMs
            unreachable = []
            for uid in user_ids:
                try:
                    text_esc = escape_markdown_v2(message_text)
                    await context.bot.send_message(chat_id=uid, text=text_esc, parse_mode=ParseMode.MARKDOWN_V2)
                except Exception:
                    # If user blocked the bot or something else failed, note it
                    unreachable.append(uid)

            summary = f"Message sent to {len(user_ids)-len(unreachable)} users."
            if unreachable:
                summary += f"\nCould not reach {len(unreachable)} users."

            await update.message.reply_text(summary)
            del admin_messaging_states[user_id]
            return

    # If we get here, check if user is in event creation mode
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
        await update.message.reply_text("Send the poll options as: Yes Option; Maybe Option; No Option")

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

    # Escape for markdown
    event_name_esc = escape_markdown_v2(event_name)
    event_date_esc = escape_markdown_v2(event_date)
    poll_text_esc = escape_markdown_v2(poll_text)
    yes_esc = escape_markdown_v2(yes_option)
    maybe_esc = escape_markdown_v2(maybe_option)
    no_esc = escape_markdown_v2(no_option)

    keyboard = [
        [
            InlineKeyboardButton(yes_esc, callback_data=f"poll:yes:{event_id}"),
            InlineKeyboardButton(maybe_esc, callback_data=f"poll:maybe:{event_id}"),
            InlineKeyboardButton(no_esc, callback_data=f"poll:no:{event_id}")
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
        ],
        [
            InlineKeyboardButton("Message Attendees", callback_data=f"eventopt:message:{event_id}")
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

    elif action == 'message':
        # Start messaging workflow
        user_id = query.from_user.id
        if user_id not in config.event_admins:
            await query.answer("Not authorized.")
            return

        admin_messaging_states[user_id] = {
            'event_id': event_id,
            'selected': set(),
            'step': 'choose_recipients'
        }

        await query.answer()
        await show_messaging_menu(query, user_id)


async def show_messaging_menu(query, user_id):
    # Show checkboxes for yes/maybe/no
    # We'll show them as toggle buttons
    state = admin_messaging_states[user_id]
    selected = state['selected']

    yes_label = "✔ Yes" if "yes" in selected else "Yes"
    maybe_label = "✔ Maybe" if "maybe" in selected else "Maybe"
    no_label = "✔ No" if "no" in selected else "No"

    keyboard = [
        [InlineKeyboardButton(yes_label, callback_data="msgopt:toggle:yes")],
        [InlineKeyboardButton(maybe_label, callback_data="msgopt:toggle:maybe")],
        [InlineKeyboardButton(no_label, callback_data="msgopt:toggle:no")],
        [InlineKeyboardButton("Confirm", callback_data="msgopt:confirm")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select which groups to message:", reply_markup=reply_markup)


async def msgopt_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(':')
    if len(data) < 2:
        await query.answer("Invalid data.")
        return

    user_id = query.from_user.id
    if user_id not in admin_messaging_states:
        await query.answer("No messaging in progress.")
        return

    state = admin_messaging_states[user_id]
    if state['step'] != 'choose_recipients':
        await query.answer("Not choosing recipients currently.")
        return

    action = data[1]
    if action == 'toggle':
        cat = data[2]
        if cat in state['selected']:
            state['selected'].remove(cat)
        else:
            state['selected'].add(cat)
        await query.answer("Toggled.")
        await show_messaging_menu(query, user_id)

    elif action == 'confirm':
        # Move to waiting_for_message if at least one selected
        if not state['selected']:
            await query.answer("Select at least one group.")
            return
        # Ask admin to send the message
        state['step'] = 'waiting_for_message'
        await query.edit_message_text("Please send me the message text to send to the selected attendees (in private).")
        await query.answer()

def get_handlers():
    return [
        CommandHandler("newevent", newevent_command),
        CommandHandler("postpoll", postpoll_command),
        CommandHandler("discard", discard_command),
        CommandHandler("eventadmin", eventadmin_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, combined_message_handler),
        CallbackQueryHandler(poll_callback, pattern='^poll:'),
        CallbackQueryHandler(eventadmin_callback, pattern='^eventadmin:'),
        CallbackQueryHandler(eventopt_callback, pattern='^eventopt:'),
        CallbackQueryHandler(msgopt_callback, pattern='^msgopt:')
    ]
