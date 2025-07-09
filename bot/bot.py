# bot.py

import os
import logging
import httpx
from urllib.parse import quote_plus

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ——————— Загрузка .env ———————
load_dotenv()
BOT_TOKEN    = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL  = os.getenv("BACKEND_URL", "").rstrip("/")
WEBAPP_URL   = os.getenv("WEBAPP_URL", "").rstrip("/")
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")

# ——————— Логгер ———————
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ——————— HTTP-клиент ———————
http_client = httpx.AsyncClient(timeout=5.0)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    user_id = tg_user.id
    name    = tg_user.first_name or tg_user.username or "Игрок"

    # 1) Парсим referrer из deep-link
    referrer_id = None
    if context.args:
        try:
            rid = int(context.args[0])
            if rid != user_id:
                referrer_id = rid
        except ValueError:
            pass

    # 2) Регистрируем нового или приветствуем старого
    payload = {"user_id": user_id}
    if referrer_id:
        payload["referrer_id"] = referrer_id

    try:
        resp = await http_client.post(f"{BACKEND_URL}/user/create", json=payload)
    except Exception as e:
        logger.error("Ошибка сети при /user/create: %s", e)
        return await update.message.reply_text("❗️ Сетевая ошибка при регистрации, повторите позже.")

    if resp.status_code == 200:
        text = f"👋 Привет, {name}! Вы зарегистрированы."
        # уведомляем реферера, если он есть
        if referrer_id:
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        f"🎉 По вашей ссылке зарегистрировался(лась) новый игрок:\n"
                        f"{name} (ID {user_id})"
                    )
                )
            except Exception:
                pass
    elif resp.status_code == 400 and "already exists" in resp.text.lower():
        text = f"🔄 С возвращением, {name}!"
    else:
        logger.warning("Непредвиденный /user/create: %s %s", resp.status_code, resp.text)
        return await update.message.reply_text("❗️ Ошибка регистрации, повторите позже.")

    # 3) Баланс
    bal = 0.0
    try:
        r2 = await http_client.get(f"{BACKEND_URL}/user/balance/{user_id}")
        if r2.status_code == 200:
            bal = r2.json().get("balance", 0.0)
    except Exception:
        pass

    text += f"\n💰 Баланс: {bal:.2f}$"
    text += (
        "\n\n📲 /play — открыть игру"
        "\n🔗 /referral — получить ссылку"
        "\n👥 /myref — список ваших рефералов"
        "\n💳 /balance — узнать баланс"
    )
    await update.message.reply_text(text)


async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={quote_plus(str(user_id))}"
    await update.message.reply_text("🔗 Ваша реферальная ссылка:\n" + link)


async def myref_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        resp = await http_client.get(f"{BACKEND_URL}/user/referrals/{user_id}")
    except Exception as e:
        logger.error("Ошибка сети при /user/referrals: %s", e)
        return await update.message.reply_text("❗️ Не удалось получить рефералов, попробуйте позже.")
    if resp.status_code != 200:
        return await update.message.reply_text("❗️ Ошибка сервера при запросе рефералов.")
    data = resp.json()
    lines = [f"🏆 Всего приглашено: {data.get('total_referrals',0)}"]
    for r in data.get("referrals", []):
        joined = r.get("joined_at","")[:10]
        lines.append(f"• ID {r.get('user_id')}  (joined {joined})")
    await update.message.reply_text("\n".join(lines))


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        resp = await http_client.get(f"{BACKEND_URL}/user/balance/{user_id}")
    except Exception as e:
        logger.error("Ошибка сети при /user/balance: %s", e)
        return await update.message.reply_text("❗️ Не удалось получить баланс, повторите позже.")
    if resp.status_code != 200:
        return await update.message.reply_text("❗️ Ошибка сервера при запросе баланса.")
    bal = resp.json().get("balance", 0.0)
    await update.message.reply_text(f"💳 Ваш баланс: {bal:.2f}$")


async def play_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # отправляем кнопку Web App
    kb = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="▶️ Играть в Crash",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    await update.message.reply_text(
        "Нажмите, чтобы открыть игру в Web App:", 
        reply_markup=kb
    )


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start",    start_handler))
    app.add_handler(CommandHandler("referral", referral_handler))
    app.add_handler(CommandHandler("myref",    myref_handler))
    app.add_handler(CommandHandler("balance",  balance_handler))
    app.add_handler(CommandHandler("play",     play_handler))

    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling()
