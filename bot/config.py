import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL    = os.getenv("BACKEND_URL")
WEBAPP_URL     = os.getenv("WEBAPP_URL")
if not TELEGRAM_TOKEN or not BACKEND_URL or not WEBAPP_URL:
    raise RuntimeError("TELEGRAM_TOKEN и API_BASE должны быть заданы в .env")