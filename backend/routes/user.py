# backend/routes/user.py

from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.database import db

router = APIRouter()

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
