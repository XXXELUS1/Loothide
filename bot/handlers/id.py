# bot/handlers/id.py
from telegram import Update
from telegram.ext import ContextTypes

async def whoami(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Ваш Telegram user_id: `{user.id}`\n"
        f"username: @{user.username or '–'}\n"
        f"first_name: {user.first_name}",
        parse_mode="MarkdownV2"
    )
