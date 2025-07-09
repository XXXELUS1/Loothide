from telegram import Update
from telegram.ext import ContextTypes
import httpx
from backend.config import TELEGRAM_TOKEN, BACKEND_URL, WEBAPP_URL

async def balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{BACKEND_URL}/user/balance/{user_id}")
    if res.status_code != 200:
        return await update.message.reply_text("❗ Ошибка получения баланса")
    balance = res.json()["balance"]
    await update.message.reply_text(f"💰 Ваш баланс: {balance:.2f} коинов")
