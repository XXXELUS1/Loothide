from pydantic import BaseModel
from typing import Optional

class GameStart(BaseModel):
    user_id: int    # Telegram-ID игрока
    stake: float    # сумма ставки в коинах

class GameAction(BaseModel):
    game_id: str
    amount:  Optional[float] = None