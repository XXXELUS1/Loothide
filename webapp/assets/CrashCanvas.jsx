import React, { useRef, useEffect, useState } from 'react';

export default function CrashCanvas({ BACKEND_URL, setBalance }) {
  const canvasRef = useRef(null);
  const [stake, setStake] = useState(1);
  const [canPlace, setCanPlace] = useState(true);
  const [canCashout, setCanCashout] = useState(false);
  const [multiplier, setMultiplier] = useState('—');
  
  useEffect(() => {
    // При маунте загрузить баланс
    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/user/balance/${window.Telegram.WebApp.initDataUnsafe.user.id}`);
        const { balance } = await res.json();
        setBalance(balance);
      } catch {}
    })();
  }, []);

  useEffect(() => {
    const ctx = canvasRef.current.getContext('2d');
    // сюда вставь свою логику рисования: resetCanvas, drawAxes, drawPoint
    // и WebSocket внутри startGame()
  }, []);

  function onQuick(val) {
    setStake(val);
  }

  async function startGame() {
    setCanPlace(false);
    setCanCashout(false);
    setMultiplier('—');
    // POST /game/start
    const res = await fetch(`${BACKEND_URL}/game/start`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        user_id: window.Telegram.WebApp.initDataUnsafe.user.id,
        stake
      })
    });
    const { game_id, crash_point } = await res.json();

    // очистка канваса и начало drawing…
    // открываем WebSocket:
    const ws = new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/crash/ws/${game_id}/${crash_point}`);
    ws.onopen = () => setCanCashout(true);
    ws.onmessage = e => {
      const msg = JSON.parse(e.data);
      const t = Math.min(msg.multiplier / crash_point, 1);
      // drawPoint(t);
      setMultiplier(msg.multiplier.toFixed(2));
      if (msg.status === 'cashed_out' || msg.status === 'crash') {
        ws.close();
        setCanCashout(false);
        setCanPlace(true);
        // reload balance:
        fetch(`${BACKEND_URL}/user/balance/${window.Telegram.WebApp.initDataUnsafe.user.id}`)
          .then(r=>r.json()).then(j=>setBalance(j.balance));
      }
    };
  }

  function cashout() {
    // отправка
    // ws.send(JSON.stringify({ action: 'cashout' }));
    setCanCashout(false);
  }

  return (
    <div>
      <canvas ref={canvasRef} width={600} height={400} className="mb-4 rounded-2xl shadow-xl" />
      <div className="flex gap-2 mb-4">
        {[1,5,10,20,50,100].map(v=>(
          <button
            key={v}
            onClick={()=>onQuick(v)}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded"
          >{v} Ƀ</button>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <input
          type="number"
          value={stake}
          onChange={e=>setStake(+e.target.value)}
          className="p-2 rounded bg-white/10 text-white"
        />
        <button
          disabled={!canPlace}
          onClick={startGame}
          className="bg-purple-600 py-2 rounded text-white"
        >Place Bet</button>
        <button
          disabled={!canCashout}
          onClick={cashout}
          className="bg-pink-600 py-2 rounded text-white"
        >Cashout</button>
      </div>
      <div className="text-2xl text-center mt-4">{multiplier}×</div>
    </div>
  );
}
