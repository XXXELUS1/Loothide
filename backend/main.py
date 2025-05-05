from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from backend.database import db
from backend.routes.user import router as user_router

# импортируем
from backend.routes.game import router as game_router
from backend.routes.user import router as user_router


load_dotenv()
app = FastAPI()

# existing health-check
@app.get("/health")
async def health():
    try:
        # простейшая команда ping
        await db.command("ping")
        return {"status": "ok", "mongo": "alive"}
    except Exception as e:
        raise HTTPException(500, f"Mongo ping failed: {e}")

app.include_router(game_router, prefix="/game", tags=["game"])
app.include_router(user_router, prefix="/user", tags=["user"])
