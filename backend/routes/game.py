import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config import HOUSE_EDGE
from ..database import db

router = APIRouter(prefix="/game", tags=["Game"])

# ─── Pydantic-схемы ─────────────────────────────────────────────────────────
class StartReq(BaseModel):
    user_id: int
    stake: float

class StartResp(BaseModel):
    game_id: str
    round_id: int
    crash_point: float

class StatusResp(BaseModel):
    game_id: str
    status: str
    crash_point: float
    current_amount: float

class CashoutReq(BaseModel):
    game_id: str
    amount: Optional[float] = None

class CashoutResp(BaseModel):
    payout: float

class GameHistoryItem(BaseModel):
    game_id: str
    created_at: datetime
    multiplier: float
    stake: float
    profit: float

class HistoryResp(BaseModel):
    history: List[GameHistoryItem]

# ─── /game/start ────────────────────────────────────────────────────────────
@router.post("/start", response_model=StartResp)
async def game_start(req: StartReq):
    user = await db.users.find_one({"user_id": req.user_id})
    if not user or user.get("balance", 0) < req.stake:
        raise HTTPException(400, "Invalid user or balance")
    # Получаем активный раунд
    rnd = await db.rounds.find_one({"status": "active"})
    if not rnd:
        raise HTTPException(400, "No active round")
    # Снимаем ставку
    await db.users.update_one({"user_id": req.user_id}, {"$inc": {"balance": -req.stake}})
    # Создаём игру
    game_id = uuid.uuid4().hex
    await db.games.insert_one({
        "_id":         game_id,
        "user_id":     req.user_id,
        "round_id":    rnd["_id"],
        "stake":       req.stake,
        "crash_point": rnd["crash_point"],
        "status":      "active",
        "created_at":  datetime.utcnow()
    })
    return StartResp(game_id=game_id, round_id=rnd["_id"], crash_point=rnd["crash_point"])

# ─── /game/status/{game_id} ─────────────────────────────────────────────────
@router.get("/status/{game_id}", response_model=StatusResp)
async def game_status(game_id: str):
    g = await db.games.find_one({"_id": game_id})
    if not g:
        raise HTTPException(404, "Game not found")
    return StatusResp(
        game_id=g["_id"],
        status=g["status"],
        crash_point=g["crash_point"],
        current_amount=g.get("current_amount", g.get("stake", 0))
    )

# ─── /game/cashout ──────────────────────────────────────────────────────────
@router.post("/cashout", response_model=CashoutResp)
async def game_cashout(req: CashoutReq):
    g = await db.games.find_one({"_id": req.game_id})
    if not g:
        raise HTTPException(404, "Game not found")
    if g["status"] != "active":
        raise HTTPException(400, f"Cannot cash out status {g['status']}")

    # Выплата в зависимости от указания amount (можно вывести всю текущую сумму)
    onhand = req.amount if req.amount is not None else g.get("current_amount", g.get("stake",0))
    payout = round(onhand, 4)

    # Начислить баланс
    await db.users.update_one(
        {"user_id": g["user_id"]},
        {"$inc": {"balance": payout}}
    )
    # Обновить статус игры
    await db.games.update_one(
        {"_id": req.game_id},
        {"$set": {
            "status":           "cashed_out",
            "payout":           payout,
            "cashed_at":        datetime.utcnow(),
            "cashed_multiplier": round(payout / g["stake"], 2)
        }}
    )

    return CashoutResp(payout=payout)

# ─── /game/history/{user_id} ────────────────────────────────────────────────
@router.get("/history/{user_id}", response_model=HistoryResp)
async def game_history(user_id: int, limit: int = Query(15, ge=1, le=100)):
    cursor = db.games.find(
        {"user_id": user_id, "status": {"$in": ["cashed_out", "crashed"]}},
        sort=[("created_at", -1)],
        limit=limit
    )
    items = []
    async for g in cursor:
        stake = g["stake"]
        if g["status"] == "cashed_out":
            payout = g.get("payout", 0.0)
            profit = round(payout - stake, 2)
            m = round(payout / stake, 2)
        else:
            payout = 0.0
            profit = -stake
            m = g.get("crash_point", 0.0)
        items.append(GameHistoryItem(
            game_id    = g["_id"],
            created_at = g["created_at"],
            multiplier = m,
            stake      = stake,
            profit     = profit
        ))
    return HistoryResp(history=items)