from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from .main_menu import start_eventadmin, main_menu_callback
from .new_event import (
    new_event_name_input,
    cancel_new_event_callback,
    start_ask_callback,
    start_date_input,
    end_ask_callback,
    end_date_input,
    capacity_ask_callback,
    capacity_input,
    confirm_callback,
    edit_event_callback,
    discard_confirm_callback
)
from .my_events import (
    my_events_callback,
    event_menu_callback,
    discard_event_callback,
    show_event_menu
)
from .announcement import (
    start_add_announcement,
    announcement_text_input,
    announcement_show_spots_callback,
    announcement_show_attending_callback,
    announcement_preview_callback,
    announcement_post_confirm_callback
)

# States
MAIN_MENU, NEW_EVENT_NAME, NEW_EVENT_START_ASK, NEW_EVENT_START_INPUT, \
NEW_EVENT_END_ASK, NEW_EVENT_END_INPUT, NEW_EVENT_CAPACITY_ASK, NEW_EVENT_CAPACITY_INPUT, \
NEW_EVENT_CONFIRM, NEW_EVENT_EDIT, NEW_EVENT_DISCARD_CONFIRM, MY_EVENTS, EVENT_MENU, \
ADD_ANNOUNCEMENT_TEXT, ADD_ANNOUNCEMENT_SHOW_SPOTS, ADD_ANNOUNCEMENT_SHOW_ATTENDING, ADD_ANNOUNCEMENT_PREVIEW,\
ADD_ANNOUNCEMENT_POST_CONFIRM = range(18)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop command."""
    await update.message.reply_text("Okay, bye.")
    return ConversationHandler.END

def get_eventadmin_handlers():
    # Build a ConversationHandler that uses main_menu.py and other files
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("eventadmin", start_eventadmin)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_callback)],
            NEW_EVENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_event_name_input),
                             CallbackQueryHandler(cancel_new_event_callback, pattern='^cancel_new_event$')],
            NEW_EVENT_START_ASK: [CallbackQueryHandler(start_ask_callback, pattern='^(has_start_yes|has_start_no)$')],
            NEW_EVENT_START_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_date_input)],
            NEW_EVENT_END_ASK: [CallbackQueryHandler(end_ask_callback, pattern='^(has_end_yes|has_end_no)$')],
            NEW_EVENT_END_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_date_input)],
            NEW_EVENT_CAPACITY_ASK: [CallbackQueryHandler(capacity_ask_callback, pattern='^(has_capacity_yes|has_capacity_no)$')],
            NEW_EVENT_CAPACITY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, capacity_input)],
            NEW_EVENT_CONFIRM: [CallbackQueryHandler(confirm_callback, pattern='^(save_event|edit_event|discard_event|back_to_main_menu)$')],
            NEW_EVENT_EDIT: [CallbackQueryHandler(edit_event_callback, pattern='^(edit_name|edit_start|edit_end|edit_capacity|edit_back)$'),
                             MessageHandler(filters.TEXT & ~filters.COMMAND, new_event_name_input)], # For name editing
            NEW_EVENT_DISCARD_CONFIRM: [CallbackQueryHandler(discard_confirm_callback, pattern='^(discard_yes|discard_no)$')],
        
            MY_EVENTS: [CallbackQueryHandler(my_events_callback, pattern='^(select_event_|back_to_main_menu$)')],
            EVENT_MENU: [
                CallbackQueryHandler(event_menu_callback, pattern='^(show_event_info|add_announcement|preview_announcement|post_announcement|view_attendees|message_attendees|edit_event|discard_event|back_to_my_events|back_to_main_menu)$'),
                CallbackQueryHandler(discard_event_callback, pattern='^discard_yes_\\d+$'),
                CallbackQueryHandler(event_menu_callback, pattern='^back_to_event_menu$'),
            ],
            ADD_ANNOUNCEMENT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, announcement_text_input)],
            ADD_ANNOUNCEMENT_SHOW_SPOTS: [CallbackQueryHandler(announcement_show_spots_callback, pattern='^(yes|no)$')],
            ADD_ANNOUNCEMENT_SHOW_ATTENDING: [CallbackQueryHandler(announcement_show_attending_callback, pattern='^(yes|no)$')],
            ADD_ANNOUNCEMENT_PREVIEW: [CallbackQueryHandler(announcement_preview_callback, pattern='^(post_announcement|save_announcement|edit_announcement|discard_announcement)$')],
            ADD_ANNOUNCEMENT_POST_CONFIRM: [CallbackQueryHandler(announcement_post_confirm_callback, pattern='^(post_confirm_yes|post_confirm_no)$')],
            },
        fallbacks=[CommandHandler("stop", stop_command)],
        allow_reentry=True
    )
    return conv_handler
