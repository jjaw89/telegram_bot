from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

async def links_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with buttons for useful general links."""
    links_command_message = "*Here are some useful links for the group:*"
    
    keyboard = [
        [InlineKeyboardButton("📄 Founding Document (Full Rules)", url="https://telegra.ph/Victoria-Pups-relevant-links-05-08")],
        [InlineKeyboardButton("📑 List of admins", url="https://drive.google.com/file/d/1GsM_zc_mFOtr7nzL4M_j36EsjN2iPAZX/view?usp=sharing")],
        [InlineKeyboardButton("🔗 Discord", url="https://discord.gg/uDTj727HsS")],
        [InlineKeyboardButton("🌐 Linktree (Other group links)", url="https://linktr.ee/victoriapups")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(links_command_message, parse_mode="MarkdownV2", reply_markup=reply_markup)
