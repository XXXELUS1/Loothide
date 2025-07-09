import os
from dotenv import load_dotenv

SERVER_SEED = "Asspgm,sa&@^$%Lvmajsd^dsnmc()@#31GFSD$#%2sca3w(@3)"
HOUSE_EDGE  = 0.1

# Константы раунд-шедулера:
ROUND_DURATION = 10.0   # сек между раундами
TICK_INTERVAL  = 0.05   # сек — шаг анимации/теля

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL    = os.getenv("BACKEND_URL")
WEBAPP_URL     = os.getenv("WEBAPP_URL")
if not TELEGRAM_TOKEN or not BACKEND_URL or not WEBAPP_URL:
    raise RuntimeError("TELEGRAM_TOKEN и API_BASE должны быть заданы в .env")