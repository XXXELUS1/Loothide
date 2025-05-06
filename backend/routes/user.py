# backend/routes/user.py
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.database import db

router = APIRouter()

class DepositReq(BaseModel):
    user_id: int
    amount: float


@router.post("/create/{user_id}")
async def create_user(user_id: int, username: str = None):
    """
    Создаёт нового пользователя с начальным балансом 1000 коинов.
    """
    exists = await db.users.find_one({"user_id": user_id})
    if exists:
        raise HTTPException(400, "User already exists")
    await db.users.insert_one({
        "user_id":    user_id,
        "username":   username,
        "balance":    1000.0,
        "created_at": datetime.utcnow()
    })
    return {"message": "User created", "balance": 1000.0}

@router.get("/balance/{user_id}")
async def get_balance(user_id: int):
    """
    Возвращает баланс пользователя.
    """
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")
    return {"user_id": user_id, "balance": user["balance"]}

@router.post("/deposit")
async def deposit(req: DepositReq):
    # пытаемся обновить
    updated = await db.users.find_one_and_update(
        {"user_id": req.user_id},
        {"$inc": {"balance": req.amount}},
        return_document=True
    )
    if not updated:
        # если пользователя нет — создаём сразу с этим балансом
        user = {
            "user_id":    req.user_id,
            "username":   None,
            "balance":    req.amount,
            "created_at": datetime.utcnow()
        }
        await db.users.insert_one(user)
        return {"balance": user["balance"]}
    return {"balance": updated["balance"]}