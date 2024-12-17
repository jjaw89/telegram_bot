from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode
from config import config

# Known users who have DMed the bot
known_users = set()

# Dictionary of events keyed by (event_name, event_date)
# This replaces the old per-user state
events = {}
# For event creation, we still need a per-admin state
admin_states = {}
# admin_states[user_id] = {
#   'step': ...,
#   'event_name': ...,
#   'event_date': ...,
#   'poll_text': ...,
#   'poll_yes': ...,
#   'poll_maybe': ...,
#   'poll_no': ...
# }

async def newevent_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("You are not authorized to create an event.")
        return
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Please message me in a private chat to create an event.")
        return

    admin_states[user_id] = {'step': 'waiting_for_name'}
    await update.message.reply_text("Please send me the event name.")

async def combined_message_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # If the user is messaging in private chat, mark them known
    if update.effective_chat.type == 'private':
        known_users.add(user_id)

    if user_id not in admin_states:
        # Not creating an event currently, ignore or handle user votes in private chat if needed
        return

    step = admin_states[user_id]['step']

    if step == 'waiting_for_name':
        event_name = update.message.text.strip()
        admin_states[user_id]['event_name'] = event_name
        admin_states[user_id]['step'] = 'waiting_for_date'
        await update.message.reply_text("Got it! Now please send me the date of the event (e.g. YYYY-MM-DD).")

    elif step == 'waiting_for_date':
        event_date = update.message.text.strip()
        admin_states[user_id]['event_date'] = event_date
        admin_states[user_id]['step'] = 'waiting_for_poll_text'
        await update.message.reply_text("Great! Now please send me the text that will appear before the poll.")

    elif step == 'waiting_for_poll_text':
        poll_text = update.message.text.strip()
        admin_states[user_id]['poll_text'] = poll_text
        admin_states[user_id]['step'] = 'waiting_for_poll_options'
        await update.message.reply_text(
            "Please send me the poll options in the format:\nYes Option; Maybe Option; No Option"
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

        event_name = admin_states[user_id]['event_name']
        event_date = admin_states[user_id]['event_date']

        # Create the event in the global events dict
        events[(event_name, event_date)] = {
            'poll_text': admin_states[user_id]['poll_text'],
            'poll_yes': admin_states[user_id]['poll_yes'],
            'poll_maybe': admin_states[user_id]['poll_maybe'],
            'poll_no': admin_states[user_id]['poll_no'],
            'responses': {
                'yes': set(),
                'maybe': set(),
                'no': set()
            },
            'message_id': None
        }

        await update.message.reply_text(
            f"Event Name: {event_name}\n"
            f"Event Date: {event_date}\n"
            f"Poll Text: {admin_states[user_id]['poll_text']}\n"
            f"Yes: {admin_states[user_id]['poll_yes']}\n"
            f"Maybe: {admin_states[user_id]['poll_maybe']}\n"
            f"No: {admin_states[user_id]['poll_no']}\n\n"
            "If this looks good, type /postpoll <event_name> <event_date> to post the poll."
        )

        admin_states[user_id]['step'] = 'ready_to_post'

async def postpoll_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("You are not authorized.")
        return

    # Join all args into a single string
    args_str = ' '.join(context.args)
    # Check if there's a comma
    if ',' not in args_str:
        await update.message.reply_text("Please provide event_name and event_date separated by a comma.\nExample: /postpoll My Big Event,2024-12-25")
        return

    # Split on the first comma
    event_name, event_date = args_str.split(',', 1)
    event_name = event_name.strip()
    event_date = event_date.strip()

    key = (event_name, event_date)

    if key not in events:
        await update.message.reply_text("No such event.")
        return

    event = events[key]
    if event['message_id'] is not None:
        await update.message.reply_text("Poll already posted.")
        return

    yes_option = event['poll_yes']
    maybe_option = event['poll_maybe']
    no_option = event['poll_no']

    keyboard = [
        [
            InlineKeyboardButton(yes_option, callback_data=f"poll:yes:{event_name}:{event_date}"),
            InlineKeyboardButton(maybe_option, callback_data=f"poll:maybe:{event_name}:{event_date}"),
            InlineKeyboardButton(no_option, callback_data=f"poll:no:{event_name}:{event_date}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = f"*{event_name}*\n{event_date}\n\n{event['poll_text']}"
    msg = await context.bot.send_message(
        chat_id=config.group_chat_id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

    event['message_id'] = msg.message_id
    await update.message.reply_text("Poll posted to the group!")

    # If you maintain admin_states per user, you can clear it here if desired.
    if user_id in admin_states:
        del admin_states[user_id]


async def poll_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    # Format: poll:<choice>:<event_name>:<event_date>
    data = query.data.split(':')
    if len(data) != 4:
        await query.answer("Invalid data.")
        return

    choice = data[1]  # yes, maybe, no
    event_name = data[2]
    event_date = data[3]

    key = (event_name, event_date)
    if key not in events:
        await query.answer("Event not found.")
        return

    event = events[key]

    # Check if user is known
    if user_id not in known_users:
        await query.answer("Please DM me first before voting.")
        return

    # User can vote or change vote
    # Remove user from all response sets first
    for ch in ['yes', 'maybe', 'no']:
        event['responses'][ch].discard(user_id)
    # Add to chosen set
    event['responses'][choice].add(user_id)

    await query.answer("Vote recorded!")

async def showresults_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("Not authorized.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /showresults <event_name> <event_date>")
        return

    event_name = args[0]
    event_date = args[1]
    key = (event_name, event_date)

    if key not in events:
        await update.message.reply_text("No such event.")
        return

    event = events[key]
    yes_count = len(event['responses']['yes'])
    maybe_count = len(event['responses']['maybe'])
    no_count = len(event['responses']['no'])

    result_text = (
        f"Results for {event_name} on {event_date}:\n"
        f"{event['poll_yes']}: {yes_count}\n"
        f"{event['poll_maybe']}: {maybe_count}\n"
        f"{event['poll_no']}: {no_count}\n"
    )
    await update.message.reply_text(result_text)

async def deleteevent_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("Not authorized.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /deleteevent <event_name> <event_date>")
        return

    event_name = args[0]
    event_date = args[1]
    key = (event_name, event_date)
    if key in events:
        del events[key]
        await update.message.reply_text("Event deleted.")
    else:
        await update.message.reply_text("No such event.")

async def eventadmin_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in config.event_admins:
        await update.message.reply_text("Not authorized.")
        return

    # List all active events
    if not events:
        await update.message.reply_text("No active events.")
        return

    text = "Active Events:\n"
    for (ename, edate) in events.keys():
        text += f"- {ename} ({edate})\n"

    # In the future, we can create inline keyboards to select events
    await update.message.reply_text(text)


def get_handlers():
    return [
        CommandHandler("newevent", newevent_command),
        CommandHandler("postpoll", postpoll_command),
        CommandHandler("showresults", showresults_command),
        CommandHandler("deleteevent", deleteevent_command),
        CommandHandler("eventadmin", eventadmin_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, combined_message_handler),
        CallbackQueryHandler(poll_callback, pattern='^poll:')
    ]