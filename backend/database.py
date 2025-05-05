import os
from dotenv import load_dotenv
import motor.motor_asyncio

load_dotenv()  # подгружает MONGO_URL из .env

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL не задан в .env")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.get_default_database()  # будет использовать базу из URL
