import { setupCanvas } from '@shared/engine/canvas';
import { createLoop } from '@shared/engine/loop';
import { themeColors } from '@shared/engine/theme';
import { bindRange, byId, setText } from '@shared/ui/dom';
import { bindReelToggle } from '@shared/ui/reel';
import { COLOR_TOKENS, draw, viewFor, type Aim } from './render';
import { createWorld, DEFAULT_PARAMS, launch, orbitSpeeds, predict, spray, STAR_R, step, type Params, type World } from './sim';

const PLAYBACK = [
  { rate: 0.25, name: 'Slow motion' },
  { rate: 0.5, name: 'Half speed' },
  { rate: 1, name: 'Normal' },
  { rate: 2, name: 'Double speed' },
] as const;
/** World units per second of launch speed for each world unit of pull. */
const PULL = 1.6;
const MAX_SPEED = 900;

const canvas = byId<HTMLCanvasElement>('stage-canvas');
const view = setupCanvas(canvas);
const theme = themeColors(COLOR_TOKENS);
const params: Params = { ...DEFAULT_PARAMS };
let world: World = createWorld();
let paused = false;

bindRange('mass', { format: (v) => `${v.toFixed(1)}×`, onInput: (v) => { params.starMass = v; } });
const sprayCount = bindRange('spray-count', { format: String });
const speed = bindRange('speed', { format: (v) => PLAYBACK[v]?.name ?? '' });

const giantBtn = byId('giant-btn');
giantBtn.addEventListener('click', () => {
  params.giant = !params.giant;
  giantBtn.textContent = params.giant ? 'Giant planet on' : 'Giant planet off';
  giantBtn.setAttribute('aria-pressed', String(params.giant));
});
byId('spray-btn').addEventListener('click', () => spray(world, params, sprayCount.value));
byId('perfect-btn').addEventListener('click', () => {
  const r = 230, { circular } = orbitSpeeds(params, r);
  launch(world, 0, -r, -circular, 0);
});
const pauseBtn = byId('pause-btn');
pauseBtn.addEventListener('click', () => { paused = !paused; pauseBtn.textContent = paused ? 'Play' : 'Pause'; });
byId('clear-btn').addEventListener('click', () => { world = createWorld(); });
bindReelToggle();

// ---------- slingshot input ----------
let drag: { id: number; start: { x: number; y: number }; now: { x: number; y: number } } | null = null;

function toWorld(e: PointerEvent) {
  const r = canvas.getBoundingClientRect();
  const v = viewFor(view.width, view.height);
  return { x: (e.clientX - r.left - v.cx) / v.scale, y: (e.clientY - r.top - v.cy) / v.scale };
}
function launchVelocity(d: NonNullable<typeof drag>) {
  let vx = (d.start.x - d.now.x) * PULL, vy = (d.start.y - d.now.y) * PULL;
  const s = Math.hypot(vx, vy);
  if (s > MAX_SPEED) { vx *= MAX_SPEED / s; vy *= MAX_SPEED / s; }
  return { vx, vy };
}
canvas.addEventListener('pointerdown', (e) => {
  const pt = toWorld(e);
  if (Math.hypot(pt.x, pt.y) < STAR_R * 1.5) return;
  drag = { id: e.pointerId, start: pt, now: pt };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', (e) => { if (drag && e.pointerId === drag.id) drag.now = toWorld(e); });
const endDrag = (e: PointerEvent, fire: boolean) => {
  if (!drag || e.pointerId !== drag.id) return;
  const { vx, vy } = launchVelocity(drag);
  if (fire && Math.hypot(vx, vy) > 5) launch(world, drag.start.x, drag.start.y, vx, vy);
  drag = null;
};
canvas.addEventListener('pointerup', (e) => endDrag(e, true));
canvas.addEventListener('pointercancel', (e) => endDrag(e, false));

// ---------- loop ----------
const loop = createLoop({
  maxDt: 1 / 30,
  update(dt) { if (!paused) step(world, params, dt * (PLAYBACK[speed.value]?.rate ?? 1)); },
  render() {
    view.beginFrame();
    let aim: Aim | null = null;
    const lines = [`star mass ${params.starMass.toFixed(1)}×${params.giant ? ' · giant planet' : ''}`, `${world.locked} in orbit · ${world.crashed} crashed · ${world.escaped} lost`];
    if (drag) {
      const { vx, vy } = launchVelocity(drag);
      const { points, end } = predict(world, params, drag.start.x, drag.start.y, vx, vy);
      aim = { x: drag.start.x, y: drag.start.y, vx, vy, pull: drag.now, path: points, end };
      const r = Math.hypot(drag.start.x, drag.start.y);
      const { circular } = orbitSpeeds(params, r);
      lines.push(`speed ${(Math.hypot(vx, vy) / circular).toFixed(2)}× circular · escape at 1.41×`);
    }
    draw(view.ctx, view.width, view.height, params, world, theme.colors, aim, { lines });
    setText('s-locked', String(world.locked));
    setText('s-launched', String(world.launched));
    setText('s-crashed', String(world.crashed));
    setText('s-escaped', String(world.escaped));
  },
});

loop.start();
