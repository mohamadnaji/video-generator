import { setupCanvas } from '@shared/engine/canvas';
import { createLoop } from '@shared/engine/loop';
import { themeColors } from '@shared/engine/theme';
import { bindRange, byId, setText } from '@shared/ui/dom';
import { bindReelToggle } from '@shared/ui/reel';
import { COLOR_TOKENS, createTrails, draw, recordTrails, type Trails } from './render';
import { createSwarm, DEFAULT_PARAMS, spread, step, type Params, type Swarm } from './sim';

const COUNTS = [1, 2, 3, 5, 10, 25, 50, 100, 250, 500, 1000] as const;
const PLAYBACK = [
  { rate: 0.25, name: 'Slow motion' },
  { rate: 0.5, name: 'Half speed' },
  { rate: 1, name: 'Real time' },
  { rate: 2, name: 'Double speed' },
] as const;

const view = setupCanvas(byId<HTMLCanvasElement>('stage-canvas'));
const theme = themeColors(COLOR_TOKENS);
const params: Params = { ...DEFAULT_PARAMS };
const goBtn = byId('go-btn');

const gapLabel = (v: number) => `${Number(Math.pow(10, v).toFixed(-v))}°`;
const count = bindRange('count', { format: (v) => `${COUNTS[v] ?? 1}`, onInput: () => reset() });
const gap = bindRange('gap', { format: gapLabel, onInput: () => reset() });
const angle = bindRange('angle', { format: (v) => `${v}°`, onInput: () => reset() });
bindRange('l2', { format: (v) => `${v.toFixed(2)} m`, onInput: (v) => { params.l2 = v; reset(); } });
const speed = bindRange('speed', { format: (v) => PLAYBACK[v]?.name ?? '' });

let swarm: Swarm;
let trails: Trails;
let running = false;

function reset() {
  const n = COUNTS[count.value] ?? 1;
  swarm = createSwarm(n, angle.value, n > 1 ? Math.pow(10, gap.value) : 0);
  trails = createTrails(n, n > 300 ? 8 : 14);
  running = false;
  goBtn.textContent = 'Release';
}

function setArms(a: 1 | 2) {
  params.arms = a;
  byId('arms-1').setAttribute('aria-selected', String(a === 1));
  byId('arms-2').setAttribute('aria-selected', String(a === 2));
  reset();
}
byId('arms-1').addEventListener('click', () => setArms(1));
byId('arms-2').addEventListener('click', () => setArms(2));

for (const btn of byId('gravity-row').querySelectorAll<HTMLButtonElement>('button')) {
  btn.addEventListener('click', () => {
    params.g = Number(btn.dataset.g);
    byId('gravity-row').querySelectorAll('button').forEach((b) => b.classList.toggle('on', b === btn));
  });
}

goBtn.addEventListener('click', () => {
  running = !running;
  goBtn.textContent = running ? 'Pause' : 'Resume';
});
byId('reset-btn').addEventListener('click', reset);
bindReelToggle();

const loop = createLoop({
  maxDt: 1 / 30,
  update(dt) {
    if (!running) return;
    step(params, swarm, dt * (PLAYBACK[speed.value]?.rate ?? 1));
    recordTrails(trails, params, swarm);
  },
  render() {
    view.beginFrame();
    const n = swarm.n;
    const gapText = n > 1 ? ` · ${gapLabel(gap.value)} apart` : '';
    draw(view.ctx, view.width, view.height, params, swarm, trails, theme.colors, {
      lines: [`${n} ${params.arms === 2 ? 'double' : 'simple'} pendulum${n === 1 ? '' : 's'}${gapText}`, `g = ${params.g} m/s²`],
      big: swarm.splitAt !== null ? `Split after ${swarm.splitAt.toFixed(1)} s` : `${swarm.t.toFixed(1)} s`,
    });
    setText('s-time', `${swarm.t.toFixed(1)} s`);
    setText('s-spread', `${Math.round(spread(params, swarm) * 100)}%`);
    setText('s-split', swarm.splitAt !== null ? `${swarm.splitAt.toFixed(1)} s` : n > 1 ? 'Still together' : '—');
    setText('s-g', `${params.g} m/s²`);
  },
});

reset();
loop.start();
