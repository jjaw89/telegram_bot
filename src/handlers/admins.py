from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

from utils.data import roles

async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a list of roles with summaries and buttons."""
    message_text = "*__Admin Roles__*\n\n"
    
    # Add each role and summary to the main message
    for role, info in roles.items():
        message_text += f"*• {role}*: _{info['summary']}_\n"

    # Create buttons with role names
    keyboard = [
        [InlineKeyboardButton(role, callback_data=f"role_{role}")]
        for role in roles
    ]

    message_text +=  "\nSelect a roll to learn more\\."
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message_text, parse_mode="MarkdownV2", reply_markup=reply_markup)

async def role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the selection of a role and display the full role description and admins."""
    query = update.callback_query
    await query.answer()

    data = query.data
    role_name = data.split("_", 1)[1]
    role_info = roles.get(role_name)

    if role_info:
        # Format the detailed role description and list of admins
        message_text = f"*{role_name}*\n_{role_info['description']}_\n\n*Admins:*"
        
        # Append each admin's name and username
        for admin in role_info['admins']:
            admin_name = admin['name']
            admin_username = admin['username']
            message_text += f"\n• [{admin_name}](https://t.me/{admin_username})"
        
        # Add a "Go Back" button to return to the main list
        keyboard = [[InlineKeyboardButton("Go Back", callback_data="go_back_admins")]]

        await query.edit_message_text(
            text=message_text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(text="Role not found.")

async def go_back_to_admins_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Go Back' action to return to the main roles list in the same message."""
    query = update.callback_query
    await query.answer()

    # Re-create the message with the list of roles
    message_text = "*__Admin Roles__*\n\n"
    
    # Add each role and summary to the main message
    for role, info in roles.items():
        message_text += f"*• {role}*: _{info['summary']}_\n"

    # Create buttons with role names
    keyboard = [
        [InlineKeyboardButton(role, callback_data=f"role_{role}")]
        for role in roles
    ]

    message_text +=  "\nSelect a roll to learn more\\."
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=message_text,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup
    )