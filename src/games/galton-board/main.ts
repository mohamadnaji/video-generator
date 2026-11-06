import { setupCanvas } from '@shared/engine/canvas';
import { createLoop } from '@shared/engine/loop';
import { themeColors } from '@shared/engine/theme';
import { bindRange, byId, setText } from '@shared/ui/dom';
import { bindReelToggle } from '@shared/ui/reel';
import { COLOR_TOKENS, draw } from './render';
import { createBoard, DEFAULT_PARAMS, finished, stats, step, type Board, type Params } from './sim';

const view = setupCanvas(byId<HTMLCanvasElement>('stage-canvas'));
const theme = themeColors(COLOR_TOKENS);
const params: Params = { ...DEFAULT_PARAMS };
const goBtn = byId('go-btn');
const curveBtn = byId('curve-btn');

const signed = (v: number, unit: string) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v)}${unit}`;
bindRange('rows', { format: String, onInput: (v) => { params.rows = v; reset(); } });
bindRange('total', { format: (v) => v.toLocaleString(), onInput: (v) => { params.total = v; } });
bindRange('rate', { format: (v) => `${v} / s`, onInput: (v) => { params.rate = v; } });
bindRange('tilt', { format: (v) => signed(v, '°'), onInput: (v) => { params.tiltDeg = v; } });
bindRange('wind', { format: (v) => (v === 0 ? 'Calm' : `${signed(Math.round(v * 100), '%')} of g`), onInput: (v) => { params.wind = v; } });
bindRange('bounce', { format: (v) => v.toFixed(2), onInput: (v) => { params.bounce = v; } });

let board: Board;
let running = false;
let showCurve = true;

function reset() {
  board = createBoard(params.rows);
  running = false;
  goBtn.textContent = 'Drop';
}

goBtn.addEventListener('click', () => {
  if (finished(board, params)) reset();
  running = !running;
  goBtn.textContent = running ? 'Pause' : 'Resume';
});
byId('reset-btn').addEventListener('click', reset);
curveBtn.addEventListener('click', () => {
  showCurve = !showCurve;
  curveBtn.textContent = showCurve ? 'Bell curve on' : 'Bell curve off';
  curveBtn.setAttribute('aria-pressed', String(showCurve));
  curveBtn.classList.toggle('on', showCurve);
});
bindReelToggle();

const fmt = (v: number) => `${v > 0.005 ? '+' : v < -0.005 ? '−' : ''}${Math.abs(v).toFixed(2)}`;

const loop = createLoop({
  maxDt: 1 / 30,
  update(dt) {
    if (!running) return;
    step(board, params, dt);
    if (finished(board, params)) { running = false; goBtn.textContent = 'Drop again'; }
  },
  render() {
    view.beginFrame();
    const { mean, sd } = stats(board);
    const push = [params.tiltDeg ? `tilt ${signed(params.tiltDeg, '°')}` : '', params.wind ? `wind ${signed(Math.round(params.wind * 100), '%')}` : ''].filter(Boolean).join(' · ');
    draw(view.ctx, view.width, view.height, board, theme.colors, {
      curve: showCurve,
      hud: {
        lines: [`${params.total.toLocaleString()} marbles · ${params.rows} rows`, push || 'level board · no wind'],
        big: `${board.landed.toLocaleString()} landed`,
      },
    });
    setText('s-landed', board.landed.toLocaleString());
    setText('s-mean', board.landed ? fmt(mean) : '—');
    setText('s-sd', board.landed > 1 ? sd.toFixed(2) : '—');
    setText('s-theory', (Math.sqrt(params.rows) / 2).toFixed(2));
  },
});

reset();
loop.start();
