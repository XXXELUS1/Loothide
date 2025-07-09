import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from crash import router, game_loop

app = FastAPI()
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def start_game():
    asyncio.create_task(game_loop())
