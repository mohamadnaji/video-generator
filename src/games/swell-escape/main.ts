import { setupCanvas } from '@shared/engine/canvas';
import { createLoop } from '@shared/engine/loop';
import { onTap, pointerToCanvas } from '@shared/engine/pointer';
import { themeColors } from '@shared/engine/theme';
import { createRng } from '@shared/math/random';
import { polygonArea } from '@shared/math/geometry';
import type { Vec } from '@shared/math/vec';
import { bindRange, byId, setText } from '@shared/ui/dom';
import { formatClock } from './format';
import { COLOR_TOKENS, createEffects, drawScene, drawStroke, updateEffects } from './render';
import { isPreset, presetShape, randomShape } from './shapes';
import { POINTS, SwellSim, WORLD } from './sim';

const rng = createRng();
const sim = new SwellSim({}, rng);
const theme = themeColors(COLOR_TOKENS);
const fx = createEffects();
const view = setupCanvas(byId<HTMLCanvasElement>('stage-canvas'));
const canvas = view.canvas;

const drawMsg = byId('draw-msg');
const escapeMsg = byId('escape-msg');
const drawBtn = byId('draw-btn');
const playBtn = byId('play-btn');

// ---------- shape loading ----------
function load(points: Vec[], gapIndex?: number) {
  stopDrawing();
  sim.setShape(points, gapIndex);
  resetRunUi();
}
const loadRandom = () => load(randomShape(rng), rng.int(0, POINTS));

function resetRunUi() {
  escapeMsg.hidden = true;
  fx.trail = [];
  fx.ripples = [];
}

// ---------- drawing a custom shape ----------
let drawing = false;
let stroke: Vec[] = [];
const MIN_DRAW_AREA = 15000;

function startDrawing() {
  drawing = true;
  stroke = [];
  canvas.classList.add('drawing');
  setText('draw-text', 'Draw a closed loop with your finger or mouse');
  drawMsg.hidden = false;
  escapeMsg.hidden = true;
  drawBtn.setAttribute('aria-pressed', 'true');
}
function stopDrawing() {
  drawing = false;
  stroke = [];
  canvas.classList.remove('drawing');
  drawMsg.hidden = true;
  drawBtn.setAttribute('aria-pressed', 'false');
}

canvas.addEventListener('pointerdown', (e) => {
  if (!drawing) return;
  canvas.setPointerCapture(e.pointerId);
  stroke = [pointerToCanvas(canvas, e, WORLD)];
});
canvas.addEventListener('pointermove', (e) => {
  if (!drawing || !stroke.length || !(e.buttons || e.pointerType === 'touch')) return;
  const p = pointerToCanvas(canvas, e, WORLD), last = stroke[stroke.length - 1]!;
  if (Math.hypot(p.x - last.x, p.y - last.y) > 4) {
    stroke.push({ x: Math.max(20, Math.min(WORLD - 20, p.x)), y: Math.max(20, Math.min(WORLD - 20, p.y)) });
  }
});
canvas.addEventListener('pointerup', () => {
  if (!drawing) return;
  if (stroke.length >= 8 && Math.abs(polygonArea(stroke)) > MIN_DRAW_AREA) load(stroke);
  else { setText('draw-text', 'Too small. Draw a bigger closed loop.'); stroke = []; }
});

onTap(canvas, (e) => {
  if (drawing) return;
  const p = pointerToCanvas(canvas, e, WORLD);
  if (sim.moveOpening(p)) return;
  if (sim.dropBall(p)) resetRunUi();
});

// ---------- buttons ----------
byId('random-btn').addEventListener('click', loadRandom);
byId('new-btn').addEventListener('click', loadRandom);
drawBtn.addEventListener('click', () => (drawing ? stopDrawing() : startDrawing()));
byId('cancel-draw').addEventListener('click', stopDrawing);
byId('presets').addEventListener('click', (e) => {
  const name = (e.target as HTMLElement).closest<HTMLElement>('[data-preset]')?.dataset.preset;
  if (name && isPreset(name)) load(presetShape(name));
});
byId('restart-btn').addEventListener('click', () => { stopDrawing(); sim.restart(); resetRunUi(); });
byId('again-btn').addEventListener('click', () => { sim.restart(); resetRunUi(); });
playBtn.addEventListener('click', () => {
  const paused = loop.togglePaused();
  playBtn.textContent = paused ? 'Play' : 'Pause';
});

// ---------- tuning ----------
bindRange('speed', { onInput: (v) => sim.setSpeed(v) });
bindRange('swell', { format: (v) => v.toFixed(1), onInput: (v) => { sim.settings.swell = v; } });
bindRange('growth', { format: (v) => `+${Math.round(v * 100)}%`, onInput: (v) => { sim.settings.growth = v; } });
bindRange('spread', { onInput: (v) => { sim.settings.spread = v; } });
bindRange('opening', { onInput: (v) => { sim.settings.opening = v; sim.updateOpening(); } });
bindRange('radius', { onInput: (v) => { sim.settings.radius = v; } });
// Pick up slider values the browser restored (back/forward cache, form restore).
for (const id of ['speed', 'swell', 'growth', 'spread', 'opening', 'radius'] as const) {
  const v = byId<HTMLInputElement>(id).valueAsNumber;
  if (id === 'speed') sim.settings.speed = v; else sim.settings[id] = v;
}

// ---------- loop ----------
let statTimer = 0;
const loop = createLoop({
  update(dt) {
    if (drawing || sim.offscreen) return;
    const ev = sim.step(dt);
    updateEffects(fx, sim, dt, ev.bounces);
    if (ev.escaped) {
      setText('escape-text', `${sim.bounces} bounces in ${formatClock(sim.elapsed)}`);
      escapeMsg.hidden = false;
    }
    statTimer += dt;
    if (statTimer > 0.1) { statTimer = 0; updateStats(); }
  },
  render() {
    view.beginFrame(WORLD);
    drawScene(view.ctx, sim, theme.colors, fx, { showBall: !drawing });
    if (drawing) drawStroke(view.ctx, stroke, theme.colors);
  },
});

function updateStats() {
  setText('stat-bounces', String(sim.bounces));
  setText('stat-time', formatClock(sim.elapsed));
  setText('stat-swell', `${Math.round((sim.maxSwell / sim.shapeWidth) * 100)}%`);
}

loadRandom();
loop.start();
