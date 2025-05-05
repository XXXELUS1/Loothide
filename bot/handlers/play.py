# bot/handlers/play.py

import aiohttp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from config import API_BASE

# Состояния диалога
ASK_STAKE, IN_GAME = range(2)

# Параметры
MIN_HIDE_PCT = 0.30   # минимум 30% от текущей суммы спрятки

def build_game_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📦 Спрятать", callback_data="hide"),
        InlineKeyboardButton("🏃 Забрать",  callback_data="cashout"),
    ]])

async def play_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 1: попросить пользователя ввести ставку."""
    await update.message.reply_text(
        "Введите вашу ставку (количество коинов):",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_STAKE

async def play_receive_stake(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 2: получить ставку, вызвать /game/start и запустить периодический статус."""
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("Ставка должна быть положительным числом. Попробуйте ещё раз:")
        return ASK_STAKE

    stake = float(text)
    user_id = update.effective_user.id

    # 1) Старт игры на бекенде
    async with aiohttp.ClientSession() as sess:
        resp = await sess.post(f"{API_BASE}/game/start", json={"user_id": user_id, "stake": stake})
        if resp.status != 200:
            err = await resp.json()
            await update.message.reply_text(f"Ошибка при старте игры: {err.get('detail') or err}")
            return ConversationHandler.END
        data = await resp.json()

    game_id = data["game_id"]
    ctx.user_data["game_id"] = game_id

    # 2) Первичное сообщение
    msg = await update.message.reply_text(
        f"Игра запущена! 🔰\nGame ID: {game_id}\n⏳ Ожидаем статус..."
    )
    chat_id = update.effective_chat.id
    msg_id  = msg.message_id

    # 3) Периодическое обновление статуса через JobQueue
    async def _job_callback(context: ContextTypes.DEFAULT_TYPE):
        await _update_status_inner(context, chat_id, msg_id, game_id)

    job = ctx.application.job_queue.run_repeating(
        _job_callback,
        interval=1.0,
        first=1.0
    )
    ctx.user_data["status_job"] = job

    return IN_GAME

async def _update_status_inner(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    msg_id: int,
    game_id: str
):
    """Внутренняя функция для обновления статуса без передачи context через context.job."""
    async with aiohttp.ClientSession() as sess:
        resp = await sess.get(f"{API_BASE}/game/status/{game_id}")
        data = await resp.json()

    # Если игра завершена
    if data["status"] != "active":
        if job := context.job:
            job.schedule_removal()
        total = data.get("current_amount", 0) + data.get("hidden_amount", 0)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"🏁 Игра завершена!\nВаш выигрыш: {total:.2f} коинов"
        )
        return

    # Иначе обновляем текущее сообщение
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=(
            f"⏳ Идёт игра\n"
            f"Множитель: x{data['multiplier']:.2f}\n"
            f"На руках: {data['current_amount']:.2f}\n"
            f"В тайнике: {data['hidden_amount']:.2f}\n"
            f"Риск: {data['risk_level']}%\n\n"
            "Выберите действие:"
        ),
        reply_markup=build_game_keyboard()
    )

async def hide_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия «Спрятать»."""
    query = update.callback_query
    await query.answer()
    game_id = ctx.user_data.get("game_id")
    if not game_id:
        return await query.edit_message_text("Ошибка: неизвестный раунд.")

    # Узнаём текущую сумму
    async with aiohttp.ClientSession() as sess:
        st = await sess.get(f"{API_BASE}/game/status/{game_id}")
        status = await st.json()
        curr = status.get("current_amount", 0)
        amount = curr * MIN_HIDE_PCT

        hide_resp = await sess.post(
            f"{API_BASE}/game/hide",
            json={"game_id": game_id, "amount": amount}
        )
        if hide_resp.status != 200:
            err = await hide_resp.json()
            return await query.edit_message_text(f"Ошибка спрятки: {err}")
        result = await hide_resp.json()

    await query.edit_message_text(
        f"✅ Спрятано: {result['hidden']:.2f} коинов\n"
        f"💸 Комиссия: {result['fee']:.2f} коинов\n\n"
        "Игра продолжается…",
        reply_markup=build_game_keyboard()
    )

async def cashout_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия «Забрать»."""
    query = update.callback_query
    await query.answer()
    game_id = ctx.user_data.get("game_id")
    if not game_id:
        return await query.edit_message_text("Ошибка: неизвестный раунд.")

    async with aiohttp.ClientSession() as sess:
        resp = await sess.post(
            f"{API_BASE}/game/cashout",
            json={"game_id": game_id}
        )
        data = await resp.json()

    # Останавливаем задачу
    if job := ctx.user_data.get("status_job"):
        job.schedule_removal()

    total = data.get("payout", 0)
    await query.edit_message_text(
        f"🏆 Вы забрали: {total:.2f} коинов\n"
        "Спасибо за игру!"
    )
    return ConversationHandler.END

async def cancel_play(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Команда /cancel прерывает игру."""
    if job := ctx.user_data.get("status_job"):
        job.schedule_removal()
    await update.message.reply_text("Игра отменена.")
    return ConversationHandler.END
