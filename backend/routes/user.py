# backend/routes/user.py

from fastapi import APIRouter, HTTPException
from ..database import db
from ..models import (
    CreateUserResp, BalanceResp,
    DepositReq, DepositResp
)

from datetime import datetime
from typing import List

from ..database import db
from ..models import (
    CreateUserReq, CreateUserResp,
    ReferralsResp, Referral
)
router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/create", response_model=CreateUserResp)
async def create_user(req: CreateUserReq):
    # если уже есть — 400
    if await db.users.find_one({"user_id": req.user_id}):
        raise HTTPException(400, "User already exists")

    # создаём нового
    await db.users.insert_one({
        "user_id":     req.user_id,
        "balance":     0.0,
        "created_at":  datetime.utcnow(),
        "referrer_id": req.referrer_id,
        "referrals":   []
    })

    # если указан реферер — добавляем его список
    if req.referrer_id is not None:
        await db.users.update_one(
            {"user_id": req.referrer_id},
            {"$addToSet": {"referrals": req.user_id}}
        )

    return CreateUserResp(user_id=req.user_id, balance=0.0)

@router.get("/referrals/{user_id}", response_model=ReferralsResp)
async def get_referrals(user_id: int):
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    # получаем список id приглашённых
    refs = user.get("referrals", [])
    arr = []
    cursor = db.users.find(
        {"user_id": {"$in": refs}},
        projection={"user_id": 1, "created_at": 1}
    )
    async for r in cursor:
        arr.append(Referral(user_id=r["user_id"], joined_at=r["created_at"]))

    return ReferralsResp(
        user_id=user_id,
        total_referrals=len(arr),
        referrals=arr
    )

@router.get("/balance/{user_id}", response_model=BalanceResp)
async def get_balance(user_id: int):
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")
    return BalanceResp(user_id=user_id, balance=user["balance"])

@router.post("/deposit", response_model=DepositResp)
async def deposit(req: DepositReq):
    user = await db.users.find_one({"user_id": req.user_id})
    if not user:
        raise HTTPException(404, "User not found")
    old = user["balance"]
    new = old + req.amount
    await db.users.update_one(
        {"user_id": req.user_id},
        {"$inc": {"balance": req.amount}}
    )
    return DepositResp(
        user_id     = req.user_id,
        old_balance = old,
        new_balance = new
    )
