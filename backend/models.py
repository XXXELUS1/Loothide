from pydantic import BaseModel
from typing import Optional

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
    hidden_amount: float

class ActionReq(BaseModel):
    game_id: str
    amount: Optional[float] = None

class HideResp(BaseModel):
    hidden: float
    fee: float

class CashoutResp(BaseModel):
    payout: float

class DepositReq(BaseModel):
    user_id: int
    amount: float
