from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.database import db
from backend.models import DepositReq

router = APIRouter()

@router.post("/create/{user_id}")
async def create_user(user_id: int, username: str = None):
    existing = await db.users.find_one({"user_id": user_id})
    if existing:
        return {"balance": existing["balance"]}

    user = {
        "user_id":    user_id,
        "username":   username,
        "balance":    1000.0,
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(user)
    return {"balance": user["balance"]}

@router.get("/balance/{user_id}")
async def get_balance(user_id: int):
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")
    return {"balance": user["balance"]}

@router.post("/deposit")
async def deposit(req: DepositReq):
    updated = await db.users.find_one_and_update(
        {"user_id": req.user_id},
        {"$inc": {"balance": req.amount}},
        return_document=True
    )
    if not updated:
        raise HTTPException(404, "User not found")
    return {"balance": updated["balance"]}
