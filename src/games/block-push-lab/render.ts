import { WALL_X, type CollisionState } from './collision';
import type { PushForces, PushState } from './push';

export const COLOR_TOKENS = ['ink', 'muted', 'accent', 'block-small', 'block-big', 'block-label'] as const;
export type Colors = Record<(typeof COLOR_TOKENS)[number], string>;

export const FLOOR_Y = 200;
const MONO = '"IBM Plex Mono", monospace';
const DISPLAY = 'Archivo, sans-serif';

function block(ctx: CanvasRenderingContext2D, x: number, size: number, floor: number, fill: string, label: string, labelColor: string, maxFont: number) {
  ctx.fillStyle = fill;
  ctx.fillRect(x, floor - size, size, size);
  ctx.fillStyle = labelColor;
  ctx.font = `700 ${Math.min(maxFont, size / 3)}px ${DISPLAY}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, x + size / 2, floor - size / 2);
  ctx.textBaseline = 'alphabetic';
}

export function drawWallAndFloor(ctx: CanvasRenderingContext2D, width: number, floor: number, top: number, colors: Pick<Colors, 'ink' | 'muted'>, wall = WALL_X) {
  ctx.strokeStyle = colors.ink;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(wall, floor); ctx.lineTo(width, floor);
  ctx.moveTo(wall, floor); ctx.lineTo(wall, top);
  ctx.stroke();
  ctx.strokeStyle = colors.muted;
  ctx.lineWidth = 1;
  for (let y = top + 6; y < floor; y += 14) {
    ctx.beginPath(); ctx.moveTo(wall, y); ctx.lineTo(wall - 10, y + 10); ctx.stroke();
  }
}

export function drawCollision(ctx: CanvasRenderingContext2D, width: number, height: number, c: CollisionState, status: string, colors: Colors) {
  ctx.clearRect(0, 0, width, height);
  drawWallAndFloor(ctx, width, FLOOR_Y, 30, colors);
  const x1 = Math.max(WALL_X, c.x1);
  const bigLabel = c.M >= 1e7 ? `10^${Math.log10(c.M)}` : c.M.toLocaleString();
  block(ctx, x1, c.smallSize, FLOOR_Y, colors['block-small'], '1', colors['block-label'], 22);
  block(ctx, Math.max(c.x2, x1 + c.smallSize), c.bigSize, FLOOR_Y, colors['block-big'], bigLabel, colors['block-label'], 22);
  ctx.fillStyle = colors.muted;
  ctx.font = `600 12px ${MONO}`;
  ctx.textAlign = 'left';
  ctx.fillText(status, WALL_X + 8, FLOOR_Y + 30);
}

const PX_PER_METRE = 40;
const MAX_FORCE = 600;
/** Block size grows with the square root of mass (area ∝ mass), clamped. */
const blockSize = (mass: number) => Math.max(28, Math.min(150, 22 * Math.sqrt(mass)));

function arrow(ctx: CanvasRenderingContext2D, xa: number, xb: number, y: number, color: string, lineWidth: number, label: string) {
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.beginPath(); ctx.moveTo(xa, y); ctx.lineTo(xb - 8, y); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(xb, y); ctx.lineTo(xb - 10, y - 6); ctx.lineTo(xb - 10, y + 6); ctx.closePath(); ctx.fill();
  ctx.font = `600 12px ${MONO}`;
  ctx.textAlign = 'center';
  ctx.fillText(label, (xa + xb) / 2, y - 10);
}

export function drawPush(ctx: CanvasRenderingContext2D, width: number, height: number, s: PushState, f: PushForces, colors: Colors) {
  ctx.clearRect(0, 0, width, height);
  // Floor with distance ticks that scroll as the blocks move.
  ctx.strokeStyle = colors.ink;
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, FLOOR_Y); ctx.lineTo(width, FLOOR_Y); ctx.stroke();
  ctx.fillStyle = colors.muted;
  ctx.font = `400 11px ${MONO}`;
  ctx.textAlign = 'center';
  const offset = (s.x * PX_PER_METRE) % PX_PER_METRE, base = Math.floor(s.x);
  for (let i = -1; i < width / PX_PER_METRE + 2; i++) {
    const x = i * PX_PER_METRE - offset, major = (base + i) % 5 === 0;
    ctx.strokeStyle = colors.muted;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x, FLOOR_Y); ctx.lineTo(x, FLOOR_Y + (major ? 10 : 5)); ctx.stroke();
    if (major) ctx.fillText(`${base + i} m`, x, FLOOR_Y + 24);
  }

  const ws = blockSize(f.m), wb = blockSize(f.M);
  const x1 = Math.max(90, (width - ws - wb) / 2), x2 = x1 + ws;
  block(ctx, x1, ws, FLOOR_Y, colors['block-small'], `${f.m}kg`, colors['block-label'], 16);
  block(ctx, x2, wb, FLOOR_Y, colors['block-big'], `${f.M}kg`, colors['block-label'], 20);

  if (f.F > 0) {
    const len = (f.F / MAX_FORCE) * (x1 - 14);
    arrow(ctx, x1 - 6 - len, x1 - 6, FLOOR_Y - ws / 2, colors.accent, 3, `F = ${f.F} N`);
  }
  if (f.N > 0) {
    const len = Math.min(wb * 0.9, (f.N / MAX_FORCE) * 200 + 12), y = FLOOR_Y - Math.min(ws, wb) / 2 - 18;
    arrow(ctx, x2 + 2, x2 + 2 + len, y, colors.ink, 2, `${f.N.toFixed(0)} N`);
  }
}
