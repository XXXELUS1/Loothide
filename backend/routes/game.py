import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import db
from backend.utils.crash import crash_point

router = APIRouter()

SERVER_SEED = os.getenv("SERVER_SEED")
COMMISSION  = float(os.getenv("COMMISSION", "0.10"))


class StartReq(BaseModel):
    user_id: int
    stake: float

class StartResp(BaseModel):
    game_id: str
    crash_point: float

class StatusResp(BaseModel):
    game_id: str
    status: str              # active / cashed_out / crashed
    crash_point: float
    current_amount: float
    hidden_amount: float

class ActionReq(BaseModel):
    game_id: str
    amount: Optional[float]  # for hide or cashout

class HideResp(BaseModel):
    hidden: float
    fee: float

class CashoutResp(BaseModel):
    payout: float


@router.post("/start", response_model=StartResp)
async def game_start(req: StartReq):
    # Проверяем, есть ли пользователь
    user = await db.users.find_one({"user_id": req.user_id})
    if not user:
        raise HTTPException(404, "User not found")
    if user["balance"] < req.stake:
        raise HTTPException(400, "Insufficient balance")

    # Создаём game_id и генерируем crash_point
    game_id = uuid.uuid4().hex
    cp = crash_point(SERVER_SEED, str(req.user_id), game_id)

    # Сохраняем раунд
    await db.games.insert_one({
        "_id":            game_id,
        "user_id":        req.user_id,
        "stake":          req.stake,
        "crash_point":    cp,
        "current_amount": req.stake,
        "hidden_amount":  0.0,
        "status":         "active",
        "created_at":     datetime.utcnow(),
    })

    # Списываем ставку с баланса
    await db.users.update_one(
        {"user_id": req.user_id},
        {"$inc": {"balance": -req.stake}}
    )

    return StartResp(game_id=game_id, crash_point=cp)


@router.get("/status/{game_id}", response_model=StatusResp)
async def game_status(game_id: str):
    g = await db.games.find_one({"_id": game_id})
    if not g:
        raise HTTPException(404, "Game not found")
    return StatusResp(
        game_id=game_id,
        status=g["status"],
        crash_point=g["crash_point"],
        current_amount=g["current_amount"],
        hidden_amount=g["hidden_amount"]
    )


@router.post("/hide", response_model=HideResp)
async def game_hide(req: ActionReq):
    g = await db.games.find_one({"_id": req.game_id})
    if not g or g["status"] != "active":
        raise HTTPException(400, "Invalid game")

    amount = req.amount or 0.0
    fee    = round(amount * COMMISSION, 4)
    hidden = round(amount - fee, 4)

    await db.games.update_one(
        {"_id": req.game_id},
        {"$inc": {
            "current_amount": -amount,
            "hidden_amount":  hidden
        }}
    )
    return HideResp(hidden=hidden, fee=fee)


@router.post("/cashout", response_model=CashoutResp)
async def game_cashout(req: ActionReq):
    g = await db.games.find_one({"_id": req.game_id})
    if not g or g["status"] != "active":
        raise HTTPException(400, "Invalid game")

    # если фронт передал amount — выплачиваем onhand+hidden, иначе всю текущую сумму
    onhand = req.amount if req.amount is not None else g["current_amount"]
    payout = round(onhand * (1 - COMMISSION) + g["hidden_amount"], 4)

    # Начисляем на баланс
    await db.users.update_one(
        {"user_id": g["user_id"]},
        {"$inc": {"balance": payout}}
    )
    # Помечаем раунд завершённым
    await db.games.update_one(
        {"_id": req.game_id},
        {"$set": {"status": "cashed_out", "payout": payout}}
    )
    return CashoutResp(payout=payout)
