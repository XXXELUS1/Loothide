# bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # подхватывает .env из корня LootHide/

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_BASE       = os.getenv("API_BASE", "http://127.0.0.1:8000")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не задан в .env")
