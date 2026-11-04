import { createClicker } from '@shared/engine/audio';
import { setupCanvas } from '@shared/engine/canvas';
import { createLoop } from '@shared/engine/loop';
import { themeColors } from '@shared/engine/theme';
import { bindRange, byId, setText } from '@shared/ui/dom';
import { collisionFinished, createCollision, stepCollision, type CollisionState } from './collision';
import { pushForces, pushStatus, stepPush, type PushState } from './push';
import { COLOR_TOKENS, drawCollision, drawPush } from './render';

type Mode = 'collision' | 'push';

const view = setupCanvas(byId<HTMLCanvasElement>('stage-canvas'));
const theme = themeColors(COLOR_TOKENS);
const clicker = createClicker();
let mode: Mode = 'collision';

// ---------- tabs ----------
function setMode(m: Mode) {
  mode = m;
  for (const id of ['collision', 'push'] as const) {
    byId(`tab-${id}`).setAttribute('aria-selected', String(id === m));
    byId(`mode-${id}`).hidden = id !== m;
  }
}
byId('tab-collision').addEventListener('click', () => setMode('collision'));
byId('tab-push').addEventListener('click', () => setMode('push'));

// ---------- collision mode ----------
const PLAYBACK = [
  { rate: 0.25, name: 'Slow' },
  { rate: 1, name: 'Normal' },
  { rate: 4, name: 'Fast' },
  { rate: 16, name: 'Very fast' },
] as const;

const massInput = bindRange('c-mass', { format: (v) => `${Math.pow(100, v).toLocaleString()} × small`, onInput: () => resetCollision() });
const speedInput = bindRange('c-speed', { format: (v) => PLAYBACK[v]?.name ?? '' });
const goBtn = byId('c-go');
const soundBtn = byId('c-sound');

let col: CollisionState = createCollision(massInput.value, view.width);
let running = false;

function resetCollision() {
  col = createCollision(massInput.value, view.width);
  running = false;
  goBtn.textContent = 'Start';
  updateCollisionStats();
}
function updateCollisionStats() {
  setText('c-count', col.count.toLocaleString());
  setText('c-ratio', `1 : ${col.M.toLocaleString()}`);
  setText('c-v1', (col.v1 / col.speed).toFixed(3));
  setText('c-v2', (col.v2 / col.speed).toFixed(3).replace('-', '−'));
}
goBtn.addEventListener('click', () => {
  if (col.done) resetCollision();
  running = !running;
  goBtn.textContent = running ? 'Pause' : 'Resume';
});
byId('c-reset').addEventListener('click', resetCollision);
soundBtn.addEventListener('click', () => {
  const on = clicker.setEnabled(!clicker.enabled);
  soundBtn.textContent = on ? 'Sound on' : 'Sound off';
  soundBtn.setAttribute('aria-pressed', String(on));
});
// Re-lay out a block set that hasn't started when the canvas changes size.
view.onResize(() => { if (!running && col.count === 0) resetCollision(); });

// ---------- push mode ----------
const pm = bindRange('p-m', { format: (v) => `${v} kg` });
const pM = bindRange('p-M', { format: (v) => `${v} kg` });
const pF = bindRange('p-F', { format: (v) => `${v} N` });
const pmu = bindRange('p-mu', { format: (v) => v.toFixed(2) });
const params = () => ({ m: pm.value, M: pM.value, F: pF.value, mu: pmu.value });
let push: PushState = { x: 0, v: 0 };
byId('p-reset').addEventListener('click', () => { push = { x: 0, v: 0 }; });

const STATUS_TAG = {
  moving: '<span class="tag ok">Moving</span>',
  slowing: '<span class="tag">Slowing</span>',
  stuck: '<span class="tag stuck">Stuck</span>',
} as const;

// ---------- loop ----------
const loop = createLoop({
  maxDt: 0.05,
  update(dt) {
    if (mode === 'collision') {
      if (running) {
        const hits = stepCollision(col, dt * (PLAYBACK[speedInput.value]?.rate ?? 1));
        if (hits) clicker.click();
        if (collisionFinished(col, view.width)) { running = false; goBtn.textContent = 'Run again'; }
      }
      updateCollisionStats();
    } else {
      stepPush(push, params(), dt);
    }
  },
  render() {
    view.beginFrame();
    if (mode === 'collision') {
      const status = col.done ? 'Done — no more collisions' : running ? 'Running' : 'Ready';
      drawCollision(view.ctx, view.width, view.height, col, status, theme.colors);
    } else {
      const f = pushForces(params(), push.v);
      drawPush(view.ctx, view.width, view.height, push, f, theme.colors);
      setText('p-n', `${f.N.toFixed(1)} N`);
      setText('p-min', `${f.Fmin.toFixed(1)} N`);
      setText('p-a', `${(f.moving ? Math.max(f.a, 0) : 0).toFixed(2)} m/s²`);
      byId('p-status').innerHTML = STATUS_TAG[pushStatus(f, push.v)];
    }
  },
});

resetCollision();
loop.start();
