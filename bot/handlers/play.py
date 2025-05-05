# bot/handlers/play.py

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import aiohttp
from config import API_BASE

# Состояния диалога
ASK_STAKE, IN_GAME = range(2)

async def play_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Первый шаг: бот просит ввести ставку."""
    await update.message.reply_text(
        "Введите, пожалуйста, вашу ставку (количество коинов):",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_STAKE

async def play_receive_stake(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Получили ставку, сохраняем её, создаём игру и выводим game_id."""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Ставка должна быть целым числом. Попробуйте ещё раз:")
        return ASK_STAKE

    stake = int(text)
    user_id = update.effective_user.id

    # Вызов API /game/start
    async with aiohttp.ClientSession() as sess:
        resp = await sess.post(
            f"{API_BASE}/game/start",
            json={"user_id": user_id, "stake": stake}
        )
        if resp.status != 200:
            err = await resp.json()
            await update.message.reply_text(f"Ошибка: {err.get('detail') or err}")
            return ConversationHandler.END

        data = await resp.json()
        game_id = data["game_id"]

    # Сохраняем в user_data
    ctx.user_data["game_id"] = game_id
    ctx.user_data["stake"] = stake

    # Отправляем первое сообщение, его будем обновлять
    msg = await update.message.reply_text(
        f"Игра запущена! game_id = {game_id}\n"
        "Секундомер запущен…\n"
        "Сейчас: multiplier = 1.00, риск = 0.0%",
    )
    ctx.user_data["status_message_id"] = msg.message_id

    # Запускаем JobQueue, чтобы каждую секунду обновлять статус
    job = ctx.job_queue.run_repeating(
        callback=update_status,
        interval=1.0,
        first=1.0,
        context={
            "chat_id": update.effective_chat.id,
            "message_id": msg.message_id,
            "game_id": game_id
        }
    )
    ctx.user_data["status_job"] = job

    return IN_GAME

async def update_status(context: ContextTypes.DEFAULT_TYPE):
    """Job-колбэк: дергаем /game/status и редактируем сообщение."""
    job_data = context.job.context
    chat_id = job_data["chat_id"]
    msg_id  = job_data["message_id"]
    game_id = job_data["game_id"]

    # Запрос статуса
    async with aiohttp.ClientSession() as sess:
        resp = await sess.get(f"{API_BASE}/game/status/{game_id}")
        data = await resp.json()

    # Если игра уже закончена — отменяем job и выходим
    if data["status"] != "active":
        context.job.schedule_removal()
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=(
              f"Игра завершена!\n"
              f"Выигрыш: {data.get('current_amount',0)+data.get('hidden_amount',0):.2f} коинов"
            )
        )
        return

    # Редактируем сообщение с новыми значениями
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=(
          f"Игра в процессе ⏳\n"
          f"Множитель: {data['multiplier']}\n"
          f"На руках: {data['current_amount']:.2f}\n"
          f"В тайнике: {data['hidden_amount']:.2f}\n"
          f"Риск: {data['risk_level']}%\n\n"
          "Нажмите «Спрятать» или «Забрать»"
        ),
        reply_markup=build_game_keyboard()
    )

def build_game_keyboard():
    """Возвращает InlineKeyboardMarkup с двумя кнопками."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = [
        InlineKeyboardButton("📦 Спрятать", callback_data="hide"),
        InlineKeyboardButton("🏃 Забрать", callback_data="cashout"),
    ]
    return InlineKeyboardMarkup([buttons])

async def cancel_play(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Если диалог прерван — останавливаем Job и очищаем."""
    if "status_job" in ctx.user_data:
        ctx.user_data["status_job"].schedule_removal()
    await update.message.reply_text("Игра прервана.")
    return ConversationHandler.END
