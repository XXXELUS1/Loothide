# bot/bot.py
import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from config import TELEGRAM_TOKEN, API_BASE
from handlers.start   import start
from handlers.balance import balance
from handlers.id      import whoami

# Логируем в консоль
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)

# Убираем лишний слэш, если он есть
API_BASE = API_BASE.rstrip("/")

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /play — шлёт кнопку, которая откроет Web App.
    """
    kb = InlineKeyboardMarkup([[ 
        InlineKeyboardButton(
            text="🕹️ Открыть игру",
            web_app=WebAppInfo(url=f"{API_BASE}/webapp/index.html")
        )
    ]])
    await update.message.reply_text(
        "Нажмите на кнопку, чтобы запустить Web App-версию игры:",
        reply_markup=kb
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Регистрируем остальные команды
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("play",    play))      # <-- включаем эту строку
    app.add_handler(CommandHandler("id",      whoami))

    # Запуск polling
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
