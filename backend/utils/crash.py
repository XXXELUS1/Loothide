# backend/utils/crash.py

import hmac
import hashlib
import math
import os

# линейный шаг множителя за клик (5% = 0.05)
D_C = float(os.getenv("D_C", "0.05"))
# комиссия при выводе (10% = 0.10) → обеспечивает RTP ≃ (1/(1−0.10))*(1−0.10) = 0.90 net
COMMISSION = float(os.getenv("COMMISSION", "0.10"))

def crash_point(server_seed: str, client_seed: str, game_id: str) -> float:
    """
    Provably-fair «Mines-like» crash:
      - генерим uniform r∈(0,1] через HMAC-SHA256 первых 52 бит
      - p = d*(1−edge)/(edge + d*(1−edge))
      - crash_tick ~ Geometric(p)
      - gross_mult = 1 + d * crash_tick
    Возвращает gross_mult (до вычета COMMISSION).
    """
    # 1) HMAC-SHA256 от client_seed+game_id
    msg    = (client_seed + game_id).encode()
    key    = server_seed.encode()
    digest = hmac.new(key, msg, hashlib.sha256).hexdigest()

    # 2) первые 13 hex → 52 бита → r в (0,1]
    hash_int = int(digest[:13], 16)
    r = hash_int / float(1 << 52) or 1e-12

    # 3) вероятность краша p (чтобы E[gross]=1/(1−edge))
    d    = D_C
    edge = COMMISSION
    p    = (d * (1 - edge)) / (edge + d * (1 - edge))

    # 4) geometric: число безопасных кликов до краша
    crash_tick = math.floor(math.log(r) / math.log(1 - p)) + 1
    if crash_tick < 1:
        crash_tick = 1

    # 5) gross-множитель (до комиссии)
    gross = 1 + d * crash_tick
    return round(gross, 4)
