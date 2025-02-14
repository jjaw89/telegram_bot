from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from utils.data import roles

async def admins_command(update: Update, context: CallbackContext):
    """
    Handle the /admins command.
    If a number is provided (e.g., /admins 2), show that specific admin role directly.
    If no argument is provided, show the summary of admin roles with numbered buttons.
    """
    args = context.args  # arguments passed with /admins
    role_keys = list(roles.keys())

    if args:  # If there are arguments, try to parse as a role number
        try:
            role_number = int(args[0])
            if 1 <= role_number <= len(role_keys):
                # Fetch the specific role
                current_role = role_keys[role_number - 1]
                current_info = roles[current_role]

                # Format the full role message
                message_text = f"*{current_role}*\n_{current_info['description']}_\n\n"
                if 'admins' in current_info:
                    message_text += "*Admins:*\n"
                    for admin in current_info['admins']:
                        # Already have escaping in the roles data. Just ensure no markdown conflicts
                        message_text += f"• {admin['name']} \\(@{admin['username']}\\)\n"

                await update.message.reply_text(
                    message_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                # Out of range role number
                await update.message.reply_text(
                    f"Invalid role number! Please use a number between 1 and {len(role_keys)}."
                )
        except ValueError:
            # Not a valid integer
            await update.message.reply_text("Please provide a valid role number (e.g., /admins 1).")
    else:
        # No arguments, show the summary with buttons
        message_text = "*__Admin Roles__*\n\n"
        for i, (role, info) in enumerate(roles.items(), start=1):
            message_text += f"{i}\\) *{role}*: _{info['summary']}_\n"

        message_text += "\nSelect a role to learn more\\."

        buttons = [
            InlineKeyboardButton(str(i + 1), callback_data=f"admins:role:{i}")
            for i in range(len(role_keys))
        ]
        keyboard = [buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )

async def admins_callback(update: Update, context: CallbackContext):
    """
    Handle callback queries related to admin roles.
    Callback data format:
      - "admins:role:<index>" to view a specific role
      - "admins:summary:0" to return to the summary
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data.split(":")
    action = data[1]  # "role" or "summary"
    role_keys = list(roles.keys())
    total_roles = len(role_keys)

    if action == "summary":
        # User wants to go back to the summary of all roles
        message_text = "*__Admin Roles__*\n\n"
        for i, (role, info) in enumerate(roles.items(), start=1):
            message_text += f"{i}\\) *{role}*: _{info['summary']}_\n"
        message_text += "\nSelect a role to learn more\\."

        buttons = [
            InlineKeyboardButton(str(i + 1), callback_data=f"admins:role:{i}")
            for i in range(total_roles)
        ]
        keyboard = [buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )

    elif action == "role":
        # The user selected a specific admin role to view details
        current_index = int(data[2])
        current_role = role_keys[current_index]
        current_info = roles[current_role]

        # Format the full role message
        message_text = f"*{current_role}*\n_{current_info['description']}_\n\n"
        if 'admins' in current_info:
            message_text += "*Admins:*\n"
            for admin in current_info['admins']:
                message_text += f"• {admin['name']} \\(@{admin['username']}\\)\n"

        prev_index = (current_index - 1) % total_roles
        next_index = (current_index + 1) % total_roles

        keyboard = [
            [
                InlineKeyboardButton("← Previous", callback_data=f"admins:role:{prev_index}"),
                InlineKeyboardButton("Home", callback_data="admins:summary:0"),
                InlineKeyboardButton("Next →", callback_data=f"admins:role:{next_index}")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
