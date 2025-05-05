# bot/bot.py

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from config import TELEGRAM_TOKEN
from handlers.start import start
from handlers.balance import balance
from handlers.play import (
    ASK_STAKE, IN_GAME,
    play_start, play_receive_stake,
    hide_callback, cashout_callback,
    cancel_play
)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))

    play_conv = ConversationHandler(
        entry_points=[CommandHandler("play", play_start)],
        states={
            ASK_STAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, play_receive_stake)],
            IN_GAME: [
                CallbackQueryHandler(hide_callback, pattern="^hide$"),
                CallbackQueryHandler(cashout_callback, pattern="^cashout$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_play)],
        per_user=True, per_chat=True, allow_reentry=True
    )
    app.add_handler(play_conv)

    app.run_polling()

if __name__ == "__main__":
    main()
