# backend/routes/game.py

import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from backend.utils.crash import crash_point
from backend.database import db   # motor client
from typing import Optional

router = APIRouter()

SERVER_SEED = os.getenv("SERVER_SEED")
HOUSE_EDGE  = float(os.getenv("HOUSE_EDGE", 0.10))


class StartReq(BaseModel):
    user_id: int
    stake: float

class StartResp(BaseModel):
    game_id: str
    crash_point: float

class StatusResp(BaseModel):
    game_id: str
    status: str              # active/won/crashed
    crash_point: float
    current_amount: float
    hidden_amount: float

class ActionReq(BaseModel):
    game_id: str
    amount: Optional[float]  # для hide

class HideResp(BaseModel):
    hidden: float
    fee: float

class CashoutResp(BaseModel):
    payout: float


@router.post("/start", response_model=StartResp)
async def game_start(req: StartReq):
    # проверяем, есть ли пользователь
    user = await db.users.find_one({"user_id": req.user_id})
    if not user:
        raise HTTPException(404, "User not found")

    if user["balance"] < req.stake:
        raise HTTPException(400, "Insufficient balance")

    # создаём game_id
    game_id = uuid.uuid4().hex
    # генерируем crash_point
    crash = crash_point(SERVER_SEED, str(req.user_id), game_id, HOUSE_EDGE)

    # сохраняем раунд
    await db.games.insert_one({
        "_id":            game_id,
        "user_id":        req.user_id,
        "stake":          req.stake,
        "crash_point":    crash,
        "current_amount": req.stake,
        "hidden_amount":  0.0,
        "status":         "active",
        "created_at":     datetime.utcnow(),
    })

    # списываем ставку с баланса пользователя
    await db.users.update_one(
        {"user_id": req.user_id},
        {"$inc": {"balance": -req.stake}}
    )

    return StartResp(game_id=game_id, crash_point=crash)


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
    fee = amount * HOUSE_EDGE
    hidden = amount - fee

    # обновляем внутреннее состояние раунда
    await db.games.update_one(
        {"_id": req.game_id},
        {
            "$inc": {
                "current_amount": -amount,
                "hidden_amount":  hidden
            }
        }
    )
    return HideResp(hidden=hidden, fee=fee)


@router.post("/cashout", response_model=CashoutResp)
async def game_cashout(req: ActionReq):
    g = await db.games.find_one({"_id": req.game_id})
    if not g or g["status"] != "active":
        raise HTTPException(400, "Invalid game")

    # итоговая выплата
    payout = g["current_amount"] + g["hidden_amount"]

    # отмечаем раунд как завершённый
    await db.games.update_one(
        {"_id": req.game_id},
        {"$set": {"status": "won"}}
    )

    # начисляем payout на баланс пользователя
    await db.users.update_one(
        {"user_id": g["user_id"]},
        {"$inc": {"balance": payout}}
    )

    return CashoutResp(payout=payout)
