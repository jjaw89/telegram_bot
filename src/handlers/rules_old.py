from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from utils.data import rules

async def rules_command(update: Update, context: CallbackContext):
    """
    Handle the /rules command.
    If no argument is provided, show the summary of rules with navigation buttons.
    If a number is provided, show the specific rule.
    """
    # Check if the user provided a rule number as an argument
    args = context.args  # Contains the list of arguments passed with the command
    rule_keys = list(rules.keys())

    if args:  # If there are arguments, try to parse the rule number
        try:
            rule_number = int(args[0])  # Convert the first argument to an integer
            if 1 <= rule_number <= len(rule_keys):  # Check if the number is within range
                # Fetch the specific rule
                current_rule = rule_keys[rule_number - 1]
                current_info = rules[current_rule]

                # Format the message for the specific rule
                message_text = f"*{current_rule}*\n_{current_info['description']}_"

                # Send the specific rule to the user
                await update.message.reply_text(
                    message_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                # Rule number is out of range
                await update.message.reply_text(
                    f"Invalid rule number! Please use a number between 1 and {len(rule_keys)}."
                )
        except ValueError:
            # Argument isn't a valid number
            await update.message.reply_text("Please provide a valid rule number (e.g., `/rules 1`).")
    else:
        # No argument provided, show the summary as before
        message_text = "*__Victoria Pups Key Rules__*\n\n"
        for i, (rule, info) in enumerate(rules.items(), start=1):
            message_text += f"{i}\\) *{rule}*: _{info['summary']}_\n"

        message_text += "\nSelect a rule to learn more\\."

        # Create a row of buttons for each rule number
        buttons = [
            InlineKeyboardButton(str(i + 1), callback_data=f"rules:rule:{i}")
            for i in range(len(rule_keys))
        ]
        keyboard = [buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the summary message
        await update.message.reply_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )


async def rules_callback(update: Update, context: CallbackContext):
    """
    Handle all callback queries related to rules navigation.
    Callback data format:
      - "rules:rule:<index>" to view a specific rule
      - "rules:summary:0" to return to the summary
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data.split(":")  # e.g. ["rules", "rule", "0"] or ["rules", "summary", "0"]
    action = data[1]  # "rule" or "summary"

    rule_keys = list(rules.keys())
    total_rules = len(rule_keys)

    if action == "summary":
        # User wants to go back to the summary of all rules
        message_text = "*__Victoria Pups Key Rules__*\n\n"
        for i, (rule, info) in enumerate(rules.items(), start=1):
            message_text += f"{i}\\) *{rule}*: _{info['summary']}_\n"

        message_text += "\nSelect a rule to learn more\\."

        # Recreate the buttons 1-6 (or however many rules)
        buttons = []
        for i in range(total_rules):
            buttons.append(InlineKeyboardButton(str(i+1), callback_data=f"rules:rule:{i}"))

        keyboard = [buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )

    elif action == "rule":
        # The user is viewing a specific rule
        current_index = int(data[2])
        current_rule = rule_keys[current_index]
        current_info = rules[current_rule]

        # Format the full rule message
        # For example:
        # *Be Respectful*
        # _Full description here..._
        message_text = f"*{current_rule}*\n_{current_info['description']}_"

        # Navigation buttons: Previous, Summary, Next
        prev_index = (current_index - 1) % total_rules
        next_index = (current_index + 1) % total_rules

        keyboard = [
            [
                InlineKeyboardButton("← Previous", callback_data=f"rules:rule:{prev_index}"),
                InlineKeyboardButton("Home", callback_data="rules:summary:0"),
                InlineKeyboardButton("Next →", callback_data=f"rules:rule:{next_index}")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Edit the same message to show this rule
        await query.edit_message_text(
            message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
