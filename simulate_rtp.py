#!/usr/bin/env python3
import random
import statistics
from backend.utils.crash import crash_point

def main():
    rounds = int(input("Сколько раундов симулировать? → "))
    print(f"Запускаю {rounds} симуляций…")
    results = [crash_point() for _ in range(rounds)]
    avg = statistics.mean(results)
    print(f"\n✅ Готово! Средний множитель: {avg:.4f}")
    print(f"   Это RTP ≃ {avg:.2%} при stake=1")

if __name__ == "__main__":
    main()
