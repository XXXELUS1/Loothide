(async () => {
    const tg = window.Telegram.WebApp;
    tg.expand(); // разворачиваем Web App на весь экран
  
    const apiBase = tg.initDataUnsafe?.query_id 
      ? "/game"      // если нужен параметр verify
      : "/game";
  
    const gameDiv = document.getElementById("game");
  
    // 1) Стартуем игру:
    const userId = tg.initDataUnsafe.user.id;
    let stake = prompt("Введите ставку (коины):");
    const startResp = await fetch(`${apiBase}/start`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ user_id: userId, stake: +stake })
    });
    const { game_id } = await startResp.json();
  
    // 2) Запускаем цикл обновления статуса
    const statusLoop = setInterval(async () => {
      const st = await fetch(`${apiBase}/status/${game_id}`);
      const data = await st.json();
      renderStatus(data);
      if (data.status !== "active") {
        clearInterval(statusLoop);
        renderFinal(data);
      }
    }, 1000);
  
    // Функция рендера текущего состояния
    function renderStatus({ multiplier, current_amount, hidden_amount, risk_level }) {
      gameDiv.innerHTML = `
        <p>Множитель: x${multiplier.toFixed(2)}</p>
        <p>На руках: ${current_amount.toFixed(2)}</p>
        <p>В тайнике: ${hidden_amount.toFixed(2)}</p>
        <p>Риск: ${risk_level}%</p>
        <button id="hide">Спрятать</button>
        <button id="cashout">Забрать</button>
      `;
      document.getElementById("hide").onclick = async () => {
        const hideResp = await fetch(`${apiBase}/hide`, {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body: JSON.stringify({ game_id, amount: current_amount*0.3 })
        });
        const r = await hideResp.json();
        alert(`Спрятано: ${r.hidden.toFixed(2)} (комиссия ${r.fee.toFixed(2)})`);
      };
      document.getElementById("cashout").onclick = async () => {
        const co = await fetch(`${apiBase}/cashout`, {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body: JSON.stringify({ game_id })
        });
        const d = await co.json();
        clearInterval(statusLoop);
        renderFinal({ current_amount: d.payout, hidden_amount: 0 });
      };
    }
  
    function renderFinal({ current_amount, hidden_amount }) {
      const total = current_amount + hidden_amount;
      gameDiv.innerHTML = `<h2>Игра завершена!</h2><p>Выигрыш: ${total.toFixed(2)}</p>`;
      tg.BackButton.show(); // чтобы можно было закрыть WebApp
    }
  })();
  