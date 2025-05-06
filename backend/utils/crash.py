# backend/utils/crash.py

import hmac
import hashlib
import math

MAX_INT = 2**52

def crash_point(server_seed: str, client_seed: str, nonce: str, house_edge: float) -> float:
    """
    Provably fair: HMAC-SHA256(server_seed, f"{client_seed}:{nonce}")
    Берём первые 13 hex → 52-бит int h ∈ [0,2^52).
    rv = h/2^52 ∈ (0,1]
    crash = (1 − house_edge) / rv
    Округление вниз до сотых, минимум 1.00
    """
    msg = f"{client_seed}:{nonce}".encode()
    hmac_hash = hmac.new(server_seed.encode(), msg, hashlib.sha256).hexdigest()
    h = int(hmac_hash[:13], 16)
    rv = h / float(MAX_INT) or 1e-18
    multiplier = (1 - house_edge) / rv
    # округляем вниз до 2 знаков
    return max(1.00, math.floor(multiplier * 100) / 100)
