import asyncio
import random
from fastapi import APIRouter, WebSocket
from typing import List

from backend.config import TICK_INTERVAL, BREAK_DURATION

router = APIRouter()

clients: List[WebSocket] = []
current_round_id = 0
crash_point = 0.0
is_game_running = False

def generate_crash_point():
    r = random.random()
    if r < 0.01:
        return 1.0
    return round(1 / (1 - r), 2)

async def notify_clients(event_type: str, data: dict):
    disconnected = []
    for ws in clients:
        try:
            await ws.send_json({"event": event_type, "data": data})
        except:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in clients:
            clients.remove(ws)

@router.websocket("/crash/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        if websocket in clients:
            clients.remove(websocket)

async def game_loop():
    global current_round_id, crash_point, is_game_running
    while True:
        current_round_id += 1
        crash_point = generate_crash_point()
        print(f"\n> Раунд #{current_round_id} стартовал, crash at {crash_point}×")
        is_game_running = True

        await notify_clients("start", {
            "round_id": current_round_id,
            "crash": crash_point
        })

        multiplier = 1.0
        step = 0.01
        while multiplier < crash_point:
            await asyncio.sleep(TICK_INTERVAL)
            multiplier = round(multiplier + step, 2)
            await notify_clients("tick", {"multiplier": multiplier})

        print(f"> Раунд #{current_round_id} крашнулся")
        await notify_clients("crash", {"multiplier": crash_point})
        is_game_running = False

        print("  ↪ Пауза 10s перед следующим раундом…")
        await asyncio.sleep(BREAK_DURATION)
