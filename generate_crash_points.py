#!/usr/bin/env python3
# generate_crash_points.py

import os
import uuid
import sys
from statistics import mean

# pip install python-dotenv
from dotenv import load_dotenv

# путь до вашей папки с проектом, чтобы корректно импортировать утилиту crash_point
# если скрипт лежит в корне LootHide, то:
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from backend.utils.crash import crash_point
except ImportError:
    print("❌ Не удалось импортировать crash_point из backend/utils/crash.py")
    print("   Проверьте, что вы запустили скрипт из корня проекта LootHide")
    sys.exit(1)

def main():
    # 1) подгружаем .env
    load_dotenv()

    SERVER_SEED = os.getenv("SERVER_SEED")
    if SERVER_SEED is None:
        print("❌ В .env не задан SERVER_SEED")
        return

    try:
        HOUSE_EDGE = float(os.getenv("HOUSE_EDGE", "0.10"))
    except ValueError:
        print("❌ Неверный формат HOUSE_EDGE в .env. Например: HOUSE_EDGE=0.10")
        return

    # 2) спрашиваем у пользователя
    try:
        n_rounds = int(input("Сколько раундов сгенерировать? → ").strip())
    except ValueError:
        print("❌ Нужно ввести целое число.")
        return

    user_id = input("Введите user_id (ENTER для 12345): ").strip() or "12345"

    out_file = "crash_points.txt"
    cps = []

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("game_id|crash_point\n")
        for i in range(1, n_rounds + 1):
            gid = uuid.uuid4().hex
            cp  = crash_point(SERVER_SEED, str(user_id), gid, HOUSE_EDGE)
            cps.append(cp)
            f.write(f"{gid}|{cp:.6f}\n")
            if i % 1000 == 0 or i == n_rounds:
                print(f"  → Сгенерировано {i}/{n_rounds}…")

    avg_cp = mean(cps) if cps else 0
    print()
    print(f"✅ Готово! Результаты в ./{out_file}")
    print(f"🧮 Средний crash_point: {avg_cp:.4f}")
    print(f"📈 При средней ставке 1 коин это RTP ≃ {avg_cp*100:.2f}% (без учёта тайников и комиссии)")

if __name__ == "__main__":
    main()
