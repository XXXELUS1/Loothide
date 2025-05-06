# backend/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.user import router as user_router
from backend.routes.game import router as game_router

app = FastAPI()

# CORS для WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика WebApp
app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")

# Подключаем роутеры
app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(game_router, prefix="/game", tags=["game"])

@app.get("/health")
async def health():
    return {"status":"ok"}
