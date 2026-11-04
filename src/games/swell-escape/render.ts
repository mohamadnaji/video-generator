import type { Vec } from '@shared/math/vec';
import { mixRgb, rgba, toRgb, type Rgb } from '@shared/engine/theme';
import { POINTS, WORLD, type SwellSim } from './sim';

export const COLOR_TOKENS = ['field', 'grid', 'muted', 'wall', 'wall-hot', 'ball'] as const;
export type Colors = Record<(typeof COLOR_TOKENS)[number], string>;

export interface Effects {
  trail: Vec[];
  ripples: { x: number; y: number; t: number }[];
}

export const RIPPLE_LIFE = 0.6;
export const createEffects = (): Effects => ({ trail: [], ripples: [] });

export function updateEffects(fx: Effects, sim: SwellSim, dt: number, bounces: Vec[]): void {
  fx.trail.push({ x: sim.ball.x, y: sim.ball.y });
  if (fx.trail.length > 26) fx.trail.shift();
  for (const b of bounces) fx.ripples.push({ ...b, t: 0 });
  for (const r of fx.ripples) r.t += dt;
  fx.ripples = fx.ripples.filter((r) => r.t < RIPPLE_LIFE);
}

interface DrawOptions {
  showGrid?: boolean;
  showBall?: boolean;
  wallWidth?: number;
}

/** Draws the whole scene in world units; call ctx transform so WORLD fits the canvas first. */
export function drawScene(ctx: CanvasRenderingContext2D, sim: SwellSim, colors: Colors, fx: Effects, opts: DrawOptions = {}): void {
  const { showGrid = true, showBall = true, wallWidth = 6 } = opts;
  const wall: Rgb = toRgb(colors.wall), hot: Rgb = toRgb(colors['wall-hot']), ball: Rgb = toRgb(colors.ball);

  ctx.fillStyle = colors.field;
  ctx.fillRect(0, 0, WORLD, WORLD);
  if (showGrid) {
    ctx.fillStyle = colors.grid;
    for (let x = 50; x < WORLD; x += 50) for (let y = 50; y < WORLD; y += 50) ctx.fillRect(x - 1.5, y - 1.5, 3, 3);
  }

  const P = sim.wall;
  if (P.length) {
    ctx.beginPath();
    P.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
    ctx.closePath();
    ctx.fillStyle = rgba(ball, 0.06);
    ctx.fill();

    ctx.lineCap = 'round';
    ctx.lineWidth = wallWidth;
    for (let i = 0; i < POINTS; i++) {
      if (sim.open[i]) continue;
      const a = P[i]!, b = P[(i + 1) % POINTS]!;
      const h = (sim.heat[i]! + sim.heat[(i + 1) % POINTS]!) / 2;
      ctx.strokeStyle = rgba(mixRgb(wall, hot, 1 - Math.exp(-h / 2.5)));
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }

    const la = P[sim.lipA]!, lb = P[sim.lipB]!;
    ctx.setLineDash([6, 8]);
    ctx.lineWidth = 2;
    ctx.strokeStyle = colors.muted;
    ctx.beginPath();
    ctx.moveTo(la.x, la.y);
    ctx.lineTo(lb.x, lb.y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = rgba(wall);
    for (const p of [la, lb]) { ctx.beginPath(); ctx.arc(p.x, p.y, wallWidth, 0, Math.PI * 2); ctx.fill(); }
  }

  for (const q of fx.ripples) {
    const k = q.t / RIPPLE_LIFE;
    ctx.strokeStyle = rgba(hot, 0.7 * (1 - k));
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(q.x, q.y, 8 + k * 36, 0, Math.PI * 2);
    ctx.stroke();
  }

  if (showBall) {
    const r = sim.settings.radius;
    fx.trail.forEach((t, i) => {
      const k = i / fx.trail.length;
      ctx.fillStyle = rgba(ball, 0.25 * k);
      ctx.beginPath();
      ctx.arc(t.x, t.y, r * (0.3 + 0.6 * k), 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.fillStyle = rgba(ball);
    ctx.beginPath();
    ctx.arc(sim.ball.x, sim.ball.y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgb(255 255 255 / 0.55)';
    ctx.beginPath();
    ctx.arc(sim.ball.x - r * 0.35, sim.ball.y - r * 0.35, r * 0.3, 0, Math.PI * 2);
    ctx.fill();
  }
}

/** The loop the player is drawing, with a dashed line back to the start. */
export function drawStroke(ctx: CanvasRenderingContext2D, stroke: Vec[], colors: Colors): void {
  if (stroke.length < 2) return;
  const first = stroke[0]!, last = stroke[stroke.length - 1]!;
  ctx.strokeStyle = colors.ball;
  ctx.lineWidth = 5;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  stroke.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
  ctx.stroke();
  ctx.setLineDash([6, 8]);
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(last.x, last.y);
  ctx.lineTo(first.x, first.y);
  ctx.stroke();
  ctx.setLineDash([]);
}
