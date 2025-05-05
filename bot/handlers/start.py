# bot/handlers/start.py

import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from config import API_BASE

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    # берём либо username, либо first_name
    username = user.username or user.first_name or f"user{user_id}"

    # пробуем создать пользователя
    async with aiohttp.ClientSession() as sess:
        resp = await sess.post(
            f"{API_BASE}/user/create/{user_id}",
            params={"username": username}
        )
        # 400 — значит уже есть, игнорируем
    await update.message.reply_text(
        "👋 Добро пожаловать в LootHide!\n"
        "Доступные команды:\n"
        "/balance — проверить баланс\n"
        "/play    — начать игру"
    )
