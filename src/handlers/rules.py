from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

from utils.data import rules

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with rules summary and buttons."""
    message_text = "*__Victoria Pups Key Rules__*\n\n"
    
    # Add each rule and summary to the main message
    for rule, info in rules.items():
        message_text += f"*• {rule}*: _{info['summary']}_\n"
    
    message_text += '\nSelect a rule to learn more\\.'
    # Create buttons for each rule
    keyboard = [
        [InlineKeyboardButton(rule, callback_data=f"rule_{rule}")]
        for rule in rules
    ]

    # Add an additional button for the Founding Document link
    keyboard.append([InlineKeyboardButton("Founding Document (Full Rules)", url="https://telegra.ph/Victoria-Pups-relevant-links-05-08")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message_text, parse_mode="MarkdownV2", reply_markup=reply_markup)

async def rule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the selection of a rule and display the full rule description."""
    query = update.callback_query
    await query.answer()

    data = query.data
    rule_name = data.split("_", 1)[1]
    rule_info = rules.get(rule_name)

    if rule_info:
        # Format the detailed rule description
        message_text = f"*{rule_name}:*\n_{rule_info['description']}_\n"

        # Add a "Go Back" button to return to the main list
        keyboard = [[InlineKeyboardButton("Go Back", callback_data="go_back_rules")]]

        await query.edit_message_text(
            text=message_text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(text="Rule not found\\.")
        
async def go_back_to_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Go Back' action to return to the main rules list in the same message."""
    query = update.callback_query
    await query.answer()

    # Re-create the message with the list of rules
    message_text = "*__Victoria Pups Key Rules__*\n\n"
    
    for rule, info in rules.items():
        message_text += f"*• {rule}*: _{info['summary']}_\n"
    
    message_text += '\nSelect a rule to learn more\\.'
    # Create buttons with rule names
    keyboard = [
        [InlineKeyboardButton(rule, callback_data=f"rule_{rule}")]
        for rule in rules
    ]

    # Add a button for the Founding Document link
    keyboard.append([InlineKeyboardButton("Founding Document (Full Rules)", url="https://telegra.ph/Victoria-Pups-relevant-links-05-08")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=message_text,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup
    )