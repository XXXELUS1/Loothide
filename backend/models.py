from pydantic import BaseModel

class GameStart(BaseModel):
    user_id: int    # Telegram-ID игрока
    stake: float    # сумма ставки в коинах
