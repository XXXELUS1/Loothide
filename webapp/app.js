// webapp/app.js

;(async () => {
  const tg = window.Telegram.WebApp;
  tg.expand();

  // UI элементы
  const usernameEl = document.getElementById("username");
  const balanceEl  = document.getElementById("balance");
  const infoEl     = document.getElementById("info");
  const stakeInput = document.getElementById("stakeInput");
  const playBtn    = document.getElementById("playBtn");
  const coinEl     = document.getElementById("coin");
  const hideBtn    = document.getElementById("hideBtn");
  const cashoutBtn = document.getElementById("cashoutBtn");
  const controls   = document.getElementById("controls");
  const actions    = document.getElementById("actions");

  // Переменные состояния
  const user = tg.initDataUnsafe.user;
  const userId   = user.id;
  const username = user.username || user.first_name || "anonymous";

  let stake = 0;
  let gameId = null;
  let clickCount = 0;
  let multiplier = 1;
  let hidden = 0;

  // Отрисовать шапку
  usernameEl.textContent = username;

  // Загрузить баланс
  async function refreshBalance() {
    try {
      const res = await fetch(`${API_BASE}/user/balance/${userId}`);
      if (!res.ok) return;
      const json = await res.json();
      balanceEl.textContent = json.balance.toFixed(2);
    } catch (e) { /* silent */ }
  }
  await refreshBalance();

  // Функция для обновления блока информации
  function renderInfo() {
    const onHand = (stake * multiplier - hidden).toFixed(2);
    const nextRisk = Math.min(1, R0 + DR * clickCount) * 100;
    infoEl.innerHTML = `
      <p>Множитель: x${multiplier.toFixed(2)}</p>
      <p>На руках: ${onHand}</p>
      <p>В тайнике: ${hidden.toFixed(2)}</p>
      <p>Риск следующего клика: ${nextRisk.toFixed(1)}%</p>
    `;
  }

  // Старт раунда
  playBtn.onclick = async () => {
    stake = parseFloat(stakeInput.value);
    if (isNaN(stake) || stake <= 0) {
      return alert("Введите корректную ставку!");
    }

    // POST /game/start
    const resp = await fetch(`${API_BASE}/game/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, stake })
    });
    if (!resp.ok) {
      const err = await resp.json().catch(()=>({detail:resp.statusText}));
      return alert("Ошибка старта: " + (err.detail || JSON.stringify(err)));
    }
    ({ game_id: gameId } = await resp.json());

    // Сменить UI
    controls.style.display = "none";
    actions.style.display  = "flex";
    coinEl.style.display   = "block";
    clickCount = 0;
    multiplier = 1;
    hidden     = 0;
    renderInfo();
  };

  // Клик по коину
  coinEl.onclick = () => {
    clickCount++;
    const risk = Math.min(1, R0 + DR * (clickCount - 1));
    if (Math.random() < risk) {
      return renderCrash();
    }
    multiplier = +(multiplier + D_C).toFixed(2);
    renderInfo();
  };

  // Частичный вывод (тайник)
  hideBtn.onclick = async () => {
    const amount = (stake * multiplier - hidden) * 0.3;
    const resp = await fetch(`${API_BASE}/game/hide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: gameId, amount })
    });
    if (!resp.ok) return alert("Ошибка спрятки");
    const r = await resp.json();
    hidden += r.hidden;
    renderInfo();
  };

  // Полный вывод
  cashoutBtn.onclick = async () => {
    clearInterval(); // на всякий случай
    const resp = await fetch(`${API_BASE}/game/cashout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: gameId })
    });
    if (!resp.ok) return alert("Ошибка cashout");
    const { payout } = await resp.json();
    renderFinal(`🏆 Вы забрали: ${payout.toFixed(2)}`);
  };

  // Экран краша
  function renderCrash() {
    infoEl.innerHTML = `<h2 style="color:#e74c3c">💥 Краш на x${multiplier.toFixed(2)}</h2>`;
    coinEl.style.display   = "none";
    actions.style.display  = "none";
    setTimeout(() => location.reload(), 2000);
  }

  // Экран финала
  async function renderFinal(message) {
    infoEl.innerHTML = `<h2 style="color:#2ecc71">${message}</h2>`;
    coinEl.style.display   = "none";
    actions.style.display  = "none";
    await refreshBalance();
    setTimeout(() => location.reload(), 2000);
  }

})();
