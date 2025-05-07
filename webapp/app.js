;(async () => {
  // --- Init Telegram WebApp or fallback to test-id ---
  const tg = window.Telegram?.WebApp;
  const userId = tg?.initDataUnsafe
    ? tg.initDataUnsafe.user.id
    : 12345;      // тестовый ID при localhost или прямом открытии

  // --- Константы игры ---
  const API_BASE   = window.location.origin;
  const D_C        = 0.05;   // +5% к множителю за клик
  const COMMISSION = 0.10;   // 10% комиссия
  const MAX_HIDE   = 2;
  const SPAWN_INT  = 3000;   // интервал падения коинов (ms)

  // --- DOM-узлы ---
  const balanceEl    = document.getElementById("balance");
  const roundIdEl    = document.getElementById("roundId");
  const stakeInput   = document.getElementById("stakeInput");
  const quickBtns    = document.querySelectorAll("#quick-stakes button");
  const playBtn      = document.getElementById("playBtn");
  const startMenu    = document.getElementById("start-controls");
  const statusDiv    = document.getElementById("status");
  const multiplierEl = document.getElementById("multiplier");
  const onhandEl     = document.getElementById("onhand");
  const riskEl       = document.getElementById("risk");
  const hiddenEl     = document.getElementById("hidden");
  const gameField    = document.getElementById("game-field");
  const controlsDiv  = document.getElementById("controls");
  const hideBtn      = document.getElementById("hideBtn");
  const cashoutBtn   = document.getElementById("cashoutBtn");

  // --- Внутреннее состояние ---
  let stake       = 0;
  let gameId      = null;
  let crashPoint  = 0;
  let clicks      = 0;
  let multiplier  = 1;
  let hidden      = 0;
  let hideCount   = 0;
  let spawnTimer  = null;

  // --- Обновляем баланс на экране ---
  async function refreshBalance() {
    try {
      const res = await fetch(`${API_BASE}/user/balance/${userId}`);
      if (!res.ok) throw new Error(`status ${res.status}`);
      const { balance } = await res.json();
      balanceEl.textContent = balance.toFixed(2);
    } catch (e) {
      console.error("refreshBalance:", e);
      balanceEl.textContent = "–";
    }
  }
  // Начальный вызов
  await refreshBalance();

  // --- Быстрые кнопки ставок ---
  quickBtns.forEach(btn => {
    btn.onclick = () => stakeInput.value = btn.dataset.value;
  });

  // --- Обновление HUD (множитель, на руках, риск, спрятано) ---
  function updateStatus() {
    const onHand = stake * multiplier - hidden;
    // Риск отображаем как процент от пути 1→crashPoint
    const risk = Math.min(1, (multiplier - 1) / (crashPoint - 1)) * 100;
    multiplierEl.textContent = `x${multiplier.toFixed(2)}`;
    onhandEl.textContent     = onHand.toFixed(2);
    riskEl.textContent       = `${risk.toFixed(1)}%`;
    hiddenEl.textContent     = hidden.toFixed(2);
  }

  // --- Сбрасываем интерфейс в главное меню ---
  function resetToMenu() {
    clearInterval(spawnTimer);
    gameField.innerHTML       = "";
    gameField.style.display   = "none";
    controlsDiv.style.display = "none";
    statusDiv.style.display   = "none";
    startMenu.style.display   = "flex";
    roundIdEl.textContent     = "—";
    stakeInput.value          = "";
    hideCount                 = 0;
    refreshBalance();
  }

  // --- Появление и обработка клика по «коину» ---
  function spawnCoin() {
    const coin = document.createElement("div");
    coin.className   = "coin";
    coin.textContent = "$";
    coin.style.left  = `${Math.random() * (gameField.clientWidth - 24)}px`;
    coin.onclick     = () => {
      coin.remove();
      clicks++;
      multiplier = +(1 + D_C * clicks).toFixed(2);
      if (multiplier >= crashPoint) {
        handleCrash();
      } else {
        updateStatus();
      }
    };
    coin.addEventListener("animationend", () => coin.remove());
    gameField.appendChild(coin);
  }

  // --- Обработка краша (вне зависимости от «спряток») ---
  async function handleCrash() {
    clearInterval(spawnTimer);
    hideBtn.disabled = cashoutBtn.disabled = true;

    gameField.innerHTML = `
      <h2 style="color:#e74c3c; text-align:center; margin-top:2rem">
        💥 Краш на ${multiplier.toFixed(2)}×
      </h2>`;

    // Авто-кашаут спрятанных средств
    try {
      const resp = await fetch(`${API_BASE}/game/cashout`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ game_id: gameId })
      });
      if (resp.ok) {
        const { payout } = await resp.json();
        gameField.innerHTML += `
          <h3 style="color:#f1c40f; text-align:center">
            🗄️ Сохранено: ${payout.toFixed(2)}
          </h3>`;
        await refreshBalance();
      }
    } catch (e) {
      console.error("handleCrash cashout:", e);
    }

    setTimeout(resetToMenu, 2000);
  }

  // --- Старт раунда ---
  playBtn.onclick = async () => {
    stake = parseFloat(stakeInput.value);
    if (!stake || stake <= 0) return alert("Введите корректную ставку");

    try {
      const res = await fetch(`${API_BASE}/game/start`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ user_id: userId, stake })
      });
      if (!res.ok) throw new Error(`start ${res.status}`);
      const data = await res.json();
      gameId     = data.game_id;
      crashPoint = data.crash_point;
      roundIdEl.textContent = gameId.slice(0, 8);

      await refreshBalance();

      // Переключаем UI в режим «игры»
      startMenu.style.display   = "none";
      gameField.style.display   = "block";
      controlsDiv.style.display = "flex";
      statusDiv.style.display   = "block";

      // Сброс состояния
      clicks     = 0;
      multiplier = 1;
      hidden     = 0;
      hideCount  = 0;
      hideBtn.disabled    = false;
      cashoutBtn.disabled = false;
      updateStatus();

      // Запускаем генерацию коинов
      spawnTimer = setInterval(spawnCoin, SPAWN_INT);
    } catch (e) {
      console.error("start error:", e);
      alert("Не удалось начать игру");
    }
  };

  // --- Спрятать часть «on-hand» (до MAX_HIDE раз) ---
  hideBtn.onclick = async () => {
    if (hideCount >= MAX_HIDE) {
      return alert(`Максимум ${MAX_HIDE} спряток`);
    }
    const onHand = stake * multiplier - hidden;
    if (onHand <= 0) {
      return alert("Нечего прятать");
    }
    // 1) берём часть → 2) снимаем комиссию сразу
    let keep = +(onHand * (1 - COMMISSION)).toFixed(2);

    try {
      const resp = await fetch(`${API_BASE}/game/hide`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ game_id: gameId, amount: keep })
      });
      if (!resp.ok) throw new Error(`hide ${resp.status}`);
      const { hidden: got } = await resp.json();
      hidden += got;
      hideCount++;
      updateStatus();
    } catch (e) {
      console.error("hide error:", e);
      alert("Не удалось спрятать");
    }
  };

  // --- Кашаут (выбрать всё: on-hand + скрытое) ---
  cashoutBtn.onclick = async () => {
    clearInterval(spawnTimer);
    hideBtn.disabled    = true;
    cashoutBtn.disabled = true;

    try {
      const resp = await fetch(`${API_BASE}/game/cashout`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ game_id: gameId })
      });
      if (!resp.ok) throw new Error(`cashout ${resp.status}`);
      const { payout } = await resp.json();
      gameField.innerHTML = `
        <h2 style="color:#2ecc71; text-align:center; margin-top:2rem">
          🏆 Вы забрали ${payout.toFixed(2)}
        </h2>`;
      await refreshBalance();
    } catch (e) {
      console.error("cashout error:", e);
      gameField.innerHTML = `
        <h2 style="color:#e67e22; text-align:center; margin-top:2rem">
          Ошибка при выводе
        </h2>`;
    } finally {
      setTimeout(resetToMenu, 2000);
    }
  };
})();
