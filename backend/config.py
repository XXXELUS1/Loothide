# backend/config.py

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env в корне проекта
load_dotenv()
BREAK_DURATION = 10.0
# ——————— Константы для раунд-шедулера —————————
ROUND_DURATION: float = 10.0   # длительность раунда в секундах
TICK_INTERVAL: float   = 0.05  # шаг WebSocket-тика


# Токен для Telegram-бота (если потребуется)
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")

# Адреса серверной части и фронтенда
BACKEND_URL: str = os.getenv("BACKEND_URL", "")
WEBAPP_URL: str  = os.getenv("WEBAPP_URL", "")

# MongoDB
MONGO_URL: str     = os.getenv("MONGO_URL", "")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "loothide_db")

# Provably-fair seed и параметры комиссии/дома
SERVER_SEED: str      = os.getenv("SERVER_SEED", "")
HOUSE_EDGE: float     = float(os.getenv("HOUSE_EDGE",  "0.1"))
D_C: float            = float(os.getenv("D_C",         "0.05"))
COMMISSION: float     = float(os.getenv("COMMISSION",  "0.10"))
# добавляем новую переменную
HIDE_COMMISSION: float = float(os.getenv("HIDE_COMMISSION", "0.07"))

