from telegram import Update
from telegram.ext import ContextTypes
import httpx
from config import TELEGRAM_TOKEN, BACKEND_URL, WEBAPP_URL

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id   = update.effective_user.id
    username  = update.effective_user.username or ""
    # Регистрируем пользователя, если нет
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{BACKEND_URL}/user/create/{user_id}",
            params={"username": username}
        )
    text = (
        "👋 Добро пожаловать в LootHide!\n\n"
        "Доступные команды:\n"
        "/balance — проверить баланс\n"
        "/play — начать игру"
    )
    await update.message.reply_text(text)
