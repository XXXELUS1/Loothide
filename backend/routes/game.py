from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid

from database import db
from models import GameStart

router = APIRouter()

@router.post("/start")
async def start_game(game: GameStart):
    # 1) проверяем, есть ли игрок и достаточно ли у него баланса
    user = await db.users.find_one({"user_id": game.user_id})
    if not user or user.get("balance", 0) < game.stake:
        raise HTTPException(400, "Недостаточно средств или игрок не найден")

    # 2) создаём сессию
    game_id = str(uuid.uuid4())
    new_game = {
        "game_id": game_id,
        "user_id": game.user_id,
        "stake": game.stake,
        "multiplier": 1.0,
        "current_amount": game.stake,
        "hidden_amount": 0.0,
        "risk_level": 0.0,
        "started_at": datetime.utcnow(),
        "status": "active"
    }
    await db.games.insert_one(new_game)

    # 3) списываем ставку
    await db.users.update_one(
        {"user_id": game.user_id},
        {"$inc": {"balance": -game.stake}}
    )

    # 4) возвращаем game_id
    return {"game_id": game_id}
