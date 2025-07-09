class CrashGraph {
  constructor(canvasId, statusId, onFinish) {
    this.canvas   = document.getElementById(canvasId);
    this.ctx      = this.canvas.getContext('2d');
    this.statusEl = document.getElementById(statusId);
    this.onFinish = onFinish;

    this.W = this.canvas.width;
    this.H = this.canvas.height;
    this.DURATION = 10000;

    this.reset();
  }

  reset() {
    this.points  = [];
    this.scale   = 1;
    this.offsetX = 0;
    this.startT  = null;
    this.ctx.setTransform(1,0,0,1,0,0);
    this.ctx.clearRect(0,0,this.W,this.H);

    this._drawAxes();
    this.ctx.beginPath();
    this.ctx.moveTo(0, this.H);

    const grad = this.ctx.createLinearGradient(0,0,this.W,0);
    grad.addColorStop(0,'#a855f7');
    grad.addColorStop(1,'#ec4899');
    this.ctx.strokeStyle = grad;
    this.ctx.lineWidth   = 3;
    this.ctx.shadowColor = '#a855f7';
    this.ctx.shadowBlur  = 8;

    this.statusEl.textContent = '1.00×';
  }

  _drawAxes() {
    const ctx = this.ctx;
    ctx.save();
    ctx.setTransform(1,0,0,1,0,0);
    ctx.strokeStyle = 'rgba(255,255,255,0.3)';
    ctx.lineWidth   = 1;
    ctx.font        = '12px sans-serif';
    ctx.fillStyle   = 'rgba(255,255,255,0.7)';
    // X axis
    ctx.beginPath(); ctx.moveTo(0,this.H); ctx.lineTo(this.W,this.H); ctx.stroke();
    for(let x=0; x<=this.W; x+=100){
      ctx.beginPath();
      ctx.moveTo(x,this.H);
      ctx.lineTo(x,this.H+6);
      ctx.stroke();
      ctx.fillText((x/this.W*10).toFixed(0), x-6, this.H+20);
    }
    // Y axis
    ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(0,this.H); ctx.stroke();
    for(let y=0; y<=this.H; y+=80){
      ctx.beginPath();
      ctx.moveTo(0,this.H-y);
      ctx.lineTo(-6,this.H-y);
      ctx.stroke();
      ctx.fillText((y/this.H*5).toFixed(1), -30, this.H-y+4);
    }
    ctx.restore();
  }

  start() {
    this.reset();
    this._step = this._step.bind(this);
    requestAnimationFrame(this._step);
  }

  _step(ts) {
    if (!this.startT) this.startT = ts;
    const t = Math.min((ts - this.startT)/this.DURATION, 1);
    const x = t * this.W;
    const y = this.H - t*t * this.H;
    this.points.push({x,y});

    if (t > 0.9) {
      this.scale   = Math.min(5, this.scale * 1.005);
      this.offsetX += this.W * 0.002;
    }

    // clear + draw
    this.ctx.setTransform(1,0,0,1,0,0);
    this.ctx.clearRect(0,0,this.W,this.H);
    this._drawAxes();

    this.ctx.save();
    this.ctx.translate(0, this.H);
    this.ctx.scale(1/this.scale, -1/this.scale);
    this.ctx.translate(-this.offsetX, 0);
    this.ctx.beginPath();
    this.points.forEach((p,i)=> i ? this.ctx.lineTo(p.x,p.y) : this.ctx.moveTo(p.x,p.y) );
    this.ctx.stroke();
    this.ctx.restore();

    const mult = (1 + t*4).toFixed(2);
    this.statusEl.textContent = mult + '×';

    if (t < 1) {
      requestAnimationFrame(this._step);
    } else {
      this.onFinish();
    }
  }
}

// Делаем CrashGraph глобальным, чтобы его видел app.js
window.CrashGraph = CrashGraph;
