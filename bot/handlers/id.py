from telegram import Update
from telegram.ext import ContextTypes

async def whoami(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Ваш Telegram ID: {uid}")
