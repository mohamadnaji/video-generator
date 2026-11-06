import { toRgb, rgba } from '@shared/engine/theme';
import { giantPos, GIANT_ORBIT, GIANT_R, STAR_R, SYSTEM_R, type MoonStatus, type Params, type World } from './sim';

export const COLOR_TOKENS = ['space', 'space-ink', 'space-muted', 'sun', 'giant', 'moon', 'orbit', 'crash'] as const;
export type Colors = Record<(typeof COLOR_TOKENS)[number], string>;

const MONO = '"IBM Plex Mono", monospace';
const DISPLAY = 'Archivo, sans-serif';

export interface Aim { x: number; y: number; vx: number; vy: number; pull: { x: number; y: number }; path: { x: number; y: number }[]; end: MoonStatus }
export interface View { cx: number; cy: number; scale: number }

export const viewFor = (w: number, h: number): View => ({ cx: w / 2, cy: h / 2, scale: (Math.min(w, h) / 2) * 0.97 / SYSTEM_R });

/** Fixed starfield so the background doesn't shimmer between frames. */
const STARS = Array.from({ length: 160 }, (_, i) => {
  const a = Math.sin(i * 12.9898) * 43758.5453;
  const b = Math.sin(i * 78.233) * 12345.6789;
  return { u: a - Math.floor(a), v: b - Math.floor(b), s: (i % 5) === 0 ? 1.4 : 0.8 };
});

const statusColor = (c: Colors, s: MoonStatus) => (s === 'orbit' ? c.orbit : s === 'crashed' ? c.crash : c.moon);

export function draw(ctx: CanvasRenderingContext2D, w: number, h: number, p: Params, world: World, colors: Colors, aim: Aim | null, hud?: { lines: string[] }): void {
  const v = viewFor(w, h);
  const X = (x: number) => v.cx + x * v.scale, Y = (y: number) => v.cy + y * v.scale;
  const ink = toRgb(colors['space-ink']);

  ctx.fillStyle = colors.space;
  ctx.fillRect(0, 0, w, h);
  for (const s of STARS) { ctx.fillStyle = rgba(ink, 0.35); ctx.fillRect(s.u * w, s.v * h, s.s, s.s); }

  // Edge of the system.
  ctx.strokeStyle = rgba(ink, 0.12);
  ctx.setLineDash([3, 7]);
  ctx.beginPath(); ctx.arc(v.cx, v.cy, SYSTEM_R * v.scale, 0, Math.PI * 2); ctx.stroke();

  // Giant planet and its orbit.
  if (p.giant) {
    ctx.strokeStyle = rgba(toRgb(colors.giant), 0.3);
    ctx.beginPath(); ctx.arc(v.cx, v.cy, GIANT_ORBIT * v.scale, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.setLineDash([]);
  if (p.giant) {
    const g = giantPos(p, world.t);
    ctx.fillStyle = colors.giant;
    ctx.beginPath(); ctx.arc(X(g.x), Y(g.y), Math.max(4, GIANT_R * v.scale), 0, Math.PI * 2); ctx.fill();
  }

  // Star with a glow that grows with its mass.
  const sun = toRgb(colors.sun);
  const sr = STAR_R * v.scale * (0.85 + 0.15 * p.starMass);
  const glow = ctx.createRadialGradient(v.cx, v.cy, sr * 0.6, v.cx, v.cy, sr * 3.2);
  glow.addColorStop(0, rgba(sun, 0.45)); glow.addColorStop(1, rgba(sun, 0));
  ctx.fillStyle = glow;
  ctx.beginPath(); ctx.arc(v.cx, v.cy, sr * 3.2, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = colors.sun;
  ctx.beginPath(); ctx.arc(v.cx, v.cy, sr, 0, Math.PI * 2); ctx.fill();

  // Moons and their trails.
  for (const m of world.moons) {
    const col = toRgb(statusColor(colors, m.status));
    const n = m.trail.length;
    ctx.lineWidth = m.status === 'orbit' ? 2.2 : 1.6;
    for (let i = 1; i < n; i++) {
      ctx.strokeStyle = rgba(col, (i / n) * 0.8);
      ctx.beginPath();
      ctx.moveTo(X(m.trail[i - 1]!.x), Y(m.trail[i - 1]!.y));
      ctx.lineTo(X(m.trail[i]!.x), Y(m.trail[i]!.y));
      ctx.stroke();
    }
    if (m.status === 'orbit') {
      ctx.fillStyle = rgba(col, 0.25);
      ctx.beginPath(); ctx.arc(X(m.x), Y(m.y), 10, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = rgba(col, 1);
    ctx.beginPath(); ctx.arc(X(m.x), Y(m.y), 4, 0, Math.PI * 2); ctx.fill();
  }

  // Crash bursts.
  const crash = toRgb(colors.crash);
  for (const b of world.bursts) {
    const k = b.age / 1.2;
    ctx.strokeStyle = rgba(crash, 1 - k);
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(X(b.x), Y(b.y), 4 + k * 28, 0, Math.PI * 2); ctx.stroke();
  }

  // Aiming: rubber band, launch point and predicted path.
  if (aim) {
    ctx.strokeStyle = rgba(ink, 0.6);
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(X(aim.x), Y(aim.y)); ctx.lineTo(X(aim.pull.x), Y(aim.pull.y)); ctx.stroke();
    ctx.strokeStyle = rgba(toRgb(statusColor(colors, aim.end === 'escaped' ? 'flying' : aim.end)), 0.75);
    ctx.setLineDash([5, 6]);
    ctx.beginPath();
    aim.path.forEach((pt, i) => (i ? ctx.lineTo(X(pt.x), Y(pt.y)) : ctx.moveTo(X(pt.x), Y(pt.y))));
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = colors.moon;
    ctx.beginPath(); ctx.arc(X(aim.x), Y(aim.y), 5, 0, Math.PI * 2); ctx.fill();
  }

  const fs = Math.max(11, Math.min(15, w / 36));
  if (hud) {
    ctx.textAlign = 'left';
    ctx.fillStyle = colors['space-muted'];
    ctx.font = `600 ${fs}px ${MONO}`;
    hud.lines.forEach((line, k) => ctx.fillText(line, 12, 8 + fs * (k + 1) * 1.35));
  }
  // Headline for the latest event, fading out after two seconds.
  const ev = world.lastEvent;
  if (hud && ev && world.t - ev.at < 2) {
    ctx.globalAlpha = Math.min(1, 2 - (world.t - ev.at));
    ctx.fillStyle = statusColor(colors, ev.kind === 'escaped' ? 'flying' : ev.kind);
    ctx.font = `800 ${fs * 2.2}px ${DISPLAY}`;
    ctx.textAlign = 'center';
    ctx.fillText(ev.text, w / 2, h - fs * 1.4);
    ctx.globalAlpha = 1;
  }
}
