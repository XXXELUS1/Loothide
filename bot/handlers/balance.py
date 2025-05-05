# bot/handlers/balance.py

import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from config import API_BASE

async def balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    async with aiohttp.ClientSession() as sess:
        resp = await sess.get(f"{API_BASE}/user/balance/{user_id}")
        # если нет пользователя — создаём и просим повторить
        if resp.status == 404:
            # автоматически регистрируем
            await sess.post(f"{API_BASE}/user/create/{user_id}")
            return await update.message.reply_text(
                "✅ Вы были зарегистрированы!\n"
                "Теперь снова нажмите /balance."
            )
        if resp.status != 200:
            return await update.message.reply_text(
                "❗️ Ошибка получения баланса. Попробуй позже."
            )
        data = await resp.json()

    await update.message.reply_text(
        f"💰 Ваш баланс: {data['balance']:.2f} коинов"
    )
