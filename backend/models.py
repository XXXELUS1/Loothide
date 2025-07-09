from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ─── Crash API Schemas ─────────────────────────────────────────────────────────

class StartReq(BaseModel):
    user_id: int
    stake: float

class StartResp(BaseModel):
    game_id: str
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


class GameHistoryResp(BaseModel):
    game_id: str
    stake: float
    crash_point: float
    status: str         # active / cashed_out / crashed / disconnected
    payout: float       # 0.0 если не было cashout
    created_at: datetime

class GameHistoryItem(BaseModel):
    game_id: str
    created_at: datetime
    multiplier: float
    stake: float
    profit: float

class HistoryResp(BaseModel):
    history: List[GameHistoryItem]
# ─── User API Schemas ──────────────────────────────────────────────────────────

class CreateUserResp(BaseModel):
    user_id: int
    balance: float

class BalanceResp(BaseModel):
    user_id: int
    balance: float

class DepositReq(BaseModel):
    user_id: int
    amount: float

class DepositResp(BaseModel):
    user_id: int
    old_balance: float
    new_balance: float


class CreateUserReq(BaseModel):
    user_id: int
    referrer_id: Optional[int] = None

class CreateUserResp(BaseModel):
    user_id: int
    balance: float

class Referral(BaseModel):
    user_id: int
    joined_at: datetime

class ReferralsResp(BaseModel):
    user_id: int
    total_referrals: int
    referrals: List[Referral]