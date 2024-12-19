from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from utils.data import rules
from config.config import chat_ids

def rules_summary():
    """Generate a summary of the rules for posting in the group."""
    message_text = "*__Summary of Key Rules__*\n\n"
    for i, (rule, info) in enumerate(rules.items(), start=1):
        message_text += f"{i}\\) *{rule}*: _{info['summary']}_\n"
    return message_text

def rules_private_reply_markup():
    keyboard = [
        InlineKeyboardButton(str(i), callback_data=f"rules:rule:{i-1}")
        for i in range(1, len(rules) + 1)
    ]
    return InlineKeyboardMarkup([keyboard])

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /rules command."""
    if update.effective_chat.type == "private":
        # Private chat: Show rules with buttons
        message_text = rules_summary()
        message_text += "\nSelect a rule to learn more\\."
        reply_markup = rules_private_reply_markup()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    else:
        # Group or other chat: Send plain summary
        message_text = rules_summary()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks for rules."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback to prevent timeout

    data = query.data.split(":")
    action = data[1]  # "rule" or "summary"

    if action == "summary":
        # Return to summary with buttons
        message_text = rules_summary()
        message_text += "\nSelect a rule to learn more\\."
        reply_markup = rules_private_reply_markup()
        await query.edit_message_text(
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    elif action == "rule":
        # Show a specific rule
        rule_keys = list(rules.keys())
        total_rules = len(rule_keys)

        current_index = int(data[2])
        current_rule = rule_keys[current_index]
        current_info = rules[current_rule]

        message_text = f"*{current_rule}*\n_{current_info['description']}_"

        prev_index = (current_index - 1) % total_rules
        next_index = (current_index + 1) % total_rules

        keyboard = [
            [
                InlineKeyboardButton("← Previous", callback_data=f"rules:rule:{prev_index}"),
                InlineKeyboardButton("Home", callback_data="rules:summary"),
                InlineKeyboardButton("Next →", callback_data=f"rules:rule:{next_index}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )


def rulesadmin_reply_markup():
    keyboard = [
        InlineKeyboardButton(str(i), callback_data=f"rulesadmin:{i-1}")
        for i in range(1, len(rules) + 1)
    ]
    return InlineKeyboardMarkup([keyboard])


async def rulesadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /rulesadmin command."""
    # Ensure the command is used in a private chat
    if update.effective_chat.type != "private":
        return
    
    # Dynamically fetch the group administrators
    group_chat = await context.bot.get_chat(chat_ids["group"])
    group_admins = [admin.user.id for admin in await group_chat.get_administrators()]
    group_name = group_chat.title
    
    # Check if the user is an admin in the group
    user_id = update.effective_user.id
    if user_id not in group_admins:
        await update.message.reply_text(f"You are not an admin of {group_name}.")
        return
    
    # Construct the rules summary with an option to post
    message_text = f"\nSelect a rule to post to {group_name}\\.\n\n"
    message_text += rules_summary()

    reply_markup = rulesadmin_reply_markup()
    
    # Send the message with buttons
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )
        
async def rulesadmin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks for rulesadmin."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback to prevent timeout

    data = query.data.split(":")
    
    # Dynamically fetch the group administrators
    group_chat = await context.bot.get_chat(chat_ids["group"])
    group_name = group_chat.title
    
    # Show a specific rule
    rule_keys = list(rules.keys())

    post_index = int(data[1])
    post_rule = rule_keys[post_index]
    post_info = rules[post_rule]
    
    message_text = f"*{post_rule}*\n_{post_info['description']}_"
    
    await context.bot.send_message(
        chat_id=chat_ids["group"],
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    # Acknowledge the post in the private chat
    await query.edit_message_text(
        text=f"Rule {post_index + 1} \\(*{post_rule}*\\) has been posted to {group_name}\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    
# Handlers for integration
def get_rules_handlers():
    return [
        CommandHandler("rules", rules_command),
        CallbackQueryHandler(rules_callback, pattern="^rules:"),
        CommandHandler("rulesadmin", rulesadmin_command),
        CallbackQueryHandler(rulesadmin_callback, pattern="^rulesadmin:"),
    ]
