from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.user import router as user_router
from backend.routes.game import router as game_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")
app.include_router(user_router, prefix="/user")
app.include_router(game_router, prefix="/game")

@app.get("/health")
async def health():
    return {"status": "ok"}
