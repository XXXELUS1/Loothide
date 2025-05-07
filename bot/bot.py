import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler

from config import TELEGRAM_TOKEN, BACKEND_URL, WEBAPP_URL
from handlers.start   import start
from handlers.balance import balance
from handlers.id      import whoami
from handlers.play    import play

logging.basicConfig(level=logging.INFO)
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start",   start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("id",      whoami))
app.add_handler(CommandHandler("play",    play))

if __name__ == "__main__":
    app.run_polling(drop_pending_updates=True)
