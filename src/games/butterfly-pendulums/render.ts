import { toRgb } from '@shared/engine/theme';
import { reach, tip, type Params, type Swarm } from './sim';

export const COLOR_TOKENS = ['field', 'ink', 'muted', 'pivot', 'rod'] as const;
export type Colors = Record<(typeof COLOR_TOKENS)[number], string>;

const MONO = '"IBM Plex Mono", monospace';
const DISPLAY = 'Archivo, sans-serif';

/** Recent tip positions for each pendulum, so the bobs leave short fading tails. */
export interface Trails { len: number; head: number; filled: number; x: Float32Array; y: Float32Array; n: number }

export function createTrails(n: number, len = 14): Trails {
  return { len, head: 0, filled: 0, n, x: new Float32Array(n * len), y: new Float32Array(n * len) };
}

export function recordTrails(tr: Trails, p: Params, s: Swarm): void {
  for (let i = 0; i < s.n; i++) {
    const t = tip(p, s, i);
    tr.x[i * tr.len + tr.head] = t.x;
    tr.y[i * tr.len + tr.head] = t.y;
  }
  tr.head = (tr.head + 1) % tr.len;
  tr.filled = Math.min(tr.len, tr.filled + 1);
}

/** Rainbow colour for pendulum i of n; brighter on dark backgrounds. */
function hue(i: number, n: number, dark: boolean, alpha: number): string {
  const h = n <= 1 ? 210 : (i / (n - 1)) * 300;
  return `hsl(${h.toFixed(1)} 90% ${dark ? 62 : 46}% / ${alpha})`;
}

export interface Hud { lines: string[]; big?: string }

export function draw(ctx: CanvasRenderingContext2D, w: number, h: number, p: Params, s: Swarm, tr: Trails | null, colors: Colors, hud?: Hud): void {
  ctx.fillStyle = colors.field;
  ctx.fillRect(0, 0, w, h);
  const [r, g, b] = toRgb(colors.field);
  const dark = r * 0.299 + g * 0.587 + b * 0.114 < 128;

  const cx = w / 2, cy = h / 2;
  const scale = (Math.min(w, h) / 2) * 0.9 / reach(p);
  const n = s.n;
  const rodAlpha = n > 200 ? 0.18 : n > 30 ? 0.35 : 0.9;

  // Faint reach circle so viewers see the space the tips can cover.
  ctx.strokeStyle = colors.rod;
  ctx.globalAlpha = 0.25;
  ctx.setLineDash([4, 6]);
  ctx.beginPath(); ctx.arc(cx, cy, reach(p) * scale, 0, Math.PI * 2); ctx.stroke();
  ctx.setLineDash([]);
  ctx.globalAlpha = 1;

  // Tails, last pendulum first to match the rods below.
  if (tr && tr.filled > 1) {
    ctx.lineWidth = n > 200 ? 1.2 : 2;
    ctx.lineCap = 'round';
    for (let i = n - 1; i >= 0; i--) {
      ctx.strokeStyle = hue(i, n, dark, n > 200 ? 0.45 : 0.6);
      ctx.beginPath();
      for (let k = 0; k < tr.filled; k++) {
        const idx = i * tr.len + ((tr.head - tr.filled + k + tr.len) % tr.len);
        const x = cx + tr.x[idx]! * scale, y = cy + tr.y[idx]! * scale;
        if (k === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }

  // Rods and bobs, drawn last pendulum first so the first one sits on top.
  const bob = Math.max(2, Math.min(9, 60 / Math.sqrt(n)));
  ctx.lineWidth = n > 200 ? 1 : 2;
  for (let i = n - 1; i >= 0; i--) {
    const x1 = cx + p.l1 * Math.sin(s.th1[i]!) * scale, y1 = cy + p.l1 * Math.cos(s.th1[i]!) * scale;
    const t = tip(p, s, i);
    const x2 = cx + t.x * scale, y2 = cy + t.y * scale;
    ctx.strokeStyle = hue(i, n, dark, rodAlpha);
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(x1, y1);
    if (p.arms === 2) ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.fillStyle = hue(i, n, dark, 1);
    if (p.arms === 2 && n <= 30) { ctx.beginPath(); ctx.arc(x1, y1, bob * 0.7, 0, Math.PI * 2); ctx.fill(); }
    ctx.beginPath(); ctx.arc(x2, y2, bob, 0, Math.PI * 2); ctx.fill();
  }

  ctx.fillStyle = colors.pivot;
  ctx.beginPath(); ctx.arc(cx, cy, 5, 0, Math.PI * 2); ctx.fill();

  if (hud) {
    const fs = Math.max(11, Math.min(15, w / 40));
    ctx.textAlign = 'left';
    ctx.fillStyle = colors.muted;
    ctx.font = `600 ${fs}px ${MONO}`;
    hud.lines.forEach((line, k) => ctx.fillText(line, 14, 14 + fs * (k + 1) * 1.35));
    if (hud.big) {
      ctx.fillStyle = colors.ink;
      ctx.font = `800 ${fs * 2.2}px ${DISPLAY}`;
      ctx.textAlign = 'center';
      ctx.fillText(hud.big, w / 2, h - fs * 1.6);
    }
  }
}
