from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler
from config import config

# We'll store state data in memory for now. Later we can store in a database.
# For Step 1, we just ask for event name. We'll add more complexity later.
# We'll need a conversation handler eventually, but let's just start simple.

# Dictionary to track which user is currently creating an event and what step they're on
event_creation_states = {}  
# Structure: event_creation_states[user_id] = {'step': 'waiting_for_name'}

async def newevent_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if user is an event admin
    if user_id not in config.event_admins:
        await update.message.reply_text("You are not authorized to create an event.")
        return

    # Check if in private chat
    if update.effective_chat.type != 'private':
        await update.message.reply_text("Please message me in a private chat to create an event.")
        return

    # If authorized and in private chat
    event_creation_states[user_id] = {'step': 'waiting_for_name'}
    await update.message.reply_text("Please send me the event name.")

# We'll add a message handler to capture the event name in Step 2.
# For now, just implement and test `/newevent` command.

def get_handlers():
    return [
        CommandHandler("newevent", newevent_command),
        # We'll add more handlers (MessageHandler) later in Step 2
    ]
