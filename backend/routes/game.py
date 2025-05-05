# backend/routes/game.py

from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid, math

from backend.database import db
from backend.models import GameStart, GameAction

router = APIRouter()

FEE_PERCENT = 0.10     # комиссия тайника 10%
MIN_HIDE_PCT = 0.30    # минимум 30% от текущей суммы
MAX_HIDES = 2          # максимум спряток

@router.post("/start")
async def start_game(game: GameStart):
    user = await db.users.find_one({"user_id": game.user_id})
    if not user or user.get("balance", 0) < game.stake:
        raise HTTPException(400, "Недостаточно средств или пользователь не найден")
    await db.users.update_one(
        {"user_id": game.user_id},
        {"$inc": {"balance": -game.stake}}
    )
    game_id = str(uuid.uuid4())
    await db.games.insert_one({
        "game_id":        game_id,
        "user_id":        game.user_id,
        "stake":          game.stake,
        "multiplier":     1.0,
        "current_amount": game.stake,
        "hidden_amount":  0.0,
        "risk_level":     0.0,
        "hides_used":     0,
        "started_at":     datetime.utcnow(),
        "ended_at":       None,
        "status":         "active"
    })
    return {"game_id": game_id}


@router.get("/status/{game_id}")
async def game_status(game_id: str):
    game = await db.games.find_one({"game_id": game_id})
    if not game:
        raise HTTPException(404, "Игра не найдена")
    if game["status"] != "active":
        return {
            "game_id":       game_id,
            "multiplier":    game["multiplier"],
            "current_amount": game["current_amount"],
            "hidden_amount": game["hidden_amount"],
            "risk_level":    game["risk_level"],
            "status":        game["status"]
        }

    # вычисляем прошедшее время
    elapsed = (datetime.utcnow() - game["started_at"]).seconds
    # простой рост множителя +2% в секунду
    multiplier = 1 + 0.02 * elapsed
    current = game["stake"] * multiplier
    # риск: старт 2% + 3% за каждую секунду после 1-й
    risk = max(0, min(100, 2 + 3 * max(0, elapsed - 1)))

    # сохраняем в БД
    await db.games.update_one(
        {"game_id": game_id},
        {"$set": {
            "multiplier":     multiplier,
            "current_amount": current,
            "risk_level":     risk
        }}
    )

    return {
        "game_id":        game_id,
        "multiplier":     round(multiplier, 4),
        "current_amount": round(current, 2),
        "hidden_amount":  round(game["hidden_amount"], 2),
        "risk_level":     round(risk, 1),
        "status":         game["status"]
    }


@router.post("/hide")
async def hide_amount(action: GameAction):
    game = await db.games.find_one({"game_id": action.game_id, "status": "active"})
    if not game:
        raise HTTPException(404, "Игра не найдена или уже завершена")
    if game["hides_used"] >= MAX_HIDES:
        raise HTTPException(400, "Достигнуто максимальное число спряток")
    if action.amount is None:
        raise HTTPException(400, "Не указана сумма спрятки")

    curr = game["current_amount"]
    min_allowed = math.ceil(curr * MIN_HIDE_PCT)
    max_allowed = curr / 2
    if action.amount < min_allowed or action.amount > max_allowed:
        raise HTTPException(
            400,
            f"Спрятать можно от {min_allowed} до {int(max_allowed)} коинов"
        )

    fee = action.amount * FEE_PERCENT
    net = action.amount - fee

    # обновляем игру
    await db.games.update_one(
        {"game_id": action.game_id},
        {"$inc": {
            "hidden_amount":  net,
            "current_amount": -action.amount,
            "hides_used":     1
        }}
    )
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "hidden": round(net, 2),
        "fee":    round(fee, 2),
        "hides_used": game["hides_used"] + 1
    }


@router.post("/cashout")
async def cashout_game(action: GameAction):
    game = await db.games.find_one({"game_id": action.game_id, "status": "active"})
    if not game:
        raise HTTPException(404, "Игра не найдена или уже завершена")

    total = game["current_amount"] + game["hidden_amount"]
    # отдаём игроку
    await db.users.update_one(
        {"user_id": game["user_id"]},
        {"$inc": {"balance": total}}
    )
    # завершаем сессию
    await db.games.update_one(
        {"game_id": action.game_id},
        {"$set": {"status": "won", "ended_at": datetime.utcnow()}}
    )
    return {"game_id": action.game_id, "payout": round(total, 2)}
