# bot/handlers/play.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import ContextTypes
from backend.config import WEBAPP_URL   # <-- сюда импортируем URL из .env

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /play — шлёт одну кнопку, по нажатию которой откроется WebApp.
    """
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🕹️ Открыть игру",
            web_app=WebAppInfo(url=WEBAPP_URL)   # <-- тут ваш WEBAPP_URL без /index.html
        )
    ]])
    await update.message.reply_text(
        "Нажмите на кнопку, чтобы запустить WebApp-версию игры:",
        reply_markup=kb
    )
