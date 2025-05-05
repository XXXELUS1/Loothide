import os
from dotenv import load_dotenv
import motor.motor_asyncio

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME   = os.getenv("MONGO_DB_NAME")

if not MONGO_URL or not DB_NAME:
    raise RuntimeError("MONGO_URL и MONGO_DB_NAME должны быть заданы в .env")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db     = client[DB_NAME]  # явно выбираем базу loothide_db
