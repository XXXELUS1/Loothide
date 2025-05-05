from fastapi import FastAPI
from dotenv import load_dotenv

# импортируем
from routes.game import router as game_router

load_dotenv()
app = FastAPI()

# existing health-check
@app.get("/health")
async def health():
    return {"status": "ok"}

# подключаем наш роутер
app.include_router(game_router, prefix="/game", tags=["game"])
