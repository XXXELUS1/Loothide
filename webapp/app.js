document.addEventListener("DOMContentLoaded", () => {
  const API = window.CONFIG.BACKEND_URL;
  const multEl = document.getElementById("multiplier");
  const canvas = document.getElementById("crashCanvas");
  const ctx    = canvas.getContext("2d");

  function drawAxes() { /* ваша реализация */ }
  function drawPoint(x,y) { /* ваша реализация */ }

  async function runLoop() {
    const res = await fetch(`${API}/crash/current`);
    if (!res.ok) throw new Error("No round");
    const { round_id, crash_point, phase } = await res.json();

    if (phase === "break") {
      // показываем таймер бекенда
      let t = 10;
      multEl.textContent = `⏱ ${t}s`;
      const iv = setInterval(() => {
        t--;
        multEl.textContent = `⏱ ${t}s`;
        if (t <= 0) {
          clearInterval(iv);
          runLoop();
        }
      }, 1000);
      return;
    }

    // фаза game
    multEl.textContent = "1.00×";
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawAxes();

    const proto = API.startsWith("https") ? "wss" : "ws";
    const url   = `${proto}://${new URL(API).host}/crash/ws/${round_id}`;
    const ws    = new WebSocket(url);

    ws.onmessage = ({ data }) => {
      const msg = JSON.parse(data);
      if (msg.multiplier != null) {
        const m = msg.multiplier;
        multEl.textContent = m.toFixed(2) + "×";
        const t = m / crash_point;
        drawPoint(t*canvas.width, canvas.height - t*t*canvas.height);
      }
      if (msg.status === "crash") {
        multEl.textContent += " 💥";
      }
    };

    ws.onclose = () => {
      setTimeout(runLoop, 500);
    };
    ws.onerror = () => ws.close();
  }

  runLoop();
});
