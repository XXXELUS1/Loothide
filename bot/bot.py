from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import TELEGRAM_TOKEN   # <-- локальный import
from handlers.start   import start
from handlers.balance import balance
from handlers.play    import (
    ASK_STAKE, IN_GAME,
    play_start, play_receive_stake,
    hide_callback, cashout_callback,
    cancel_play,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

async def play(update, ctx):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🕹️ Открыть игру",
            web_app=WebAppInfo(url=f"{API_BASE}/webapp/index.html")
        )
    ]])
    await update.message.reply_text(
        "Нажмите на кнопку, чтобы запустить игру:",
        reply_markup=kb
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("balance", balance))

    play_conv = ConversationHandler(
        entry_points=[CommandHandler("play", play_start)],
        states={
            ASK_STAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, play_receive_stake)],
            IN_GAME: [
                CallbackQueryHandler(hide_callback,    pattern="^hide$"),
                CallbackQueryHandler(cashout_callback, pattern="^cashout$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_play)],
        per_user=True,
        per_chat=True,
        name="play_conversation",
        allow_reentry=True,
    )
    app.add_handler(play_conv)
    app.add_handler(CommandHandler("play", play))
    app.run_polling()

if __name__ == "__main__":
    main()
