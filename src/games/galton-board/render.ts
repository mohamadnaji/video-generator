import { MARBLE_R, PEG_R, pileScale, stats, type Board } from './sim';

export const COLOR_TOKENS = ['field', 'ink', 'muted', 'line', 'peg', 'marble', 'pile', 'curve'] as const;
export type Colors = Record<(typeof COLOR_TOKENS)[number], string>;

const MONO = '"IBM Plex Mono", monospace';
const DISPLAY = 'Archivo, sans-serif';

export interface DrawOptions { curve: boolean; hud?: { lines: string[]; big?: string } }

export function draw(ctx: CanvasRenderingContext2D, w: number, h: number, b: Board, colors: Colors, opts: DrawOptions): void {
  ctx.fillStyle = colors.field;
  ctx.fillRect(0, 0, w, h);

  // Fit the board (plus a margin) into the canvas, leaving room for the HUD.
  const hudTop = opts.hud ? Math.min(70, h * 0.1) : 8;
  const hudBottom = opts.hud?.big ? Math.min(60, h * 0.09) : 8;
  const worldW = b.width + 0.6, worldH = b.floor + 0.3;
  const s = Math.min((w - 16) / worldW, (h - hudTop - hudBottom) / worldH);
  const ox = (w - b.width * s) / 2, oy = hudTop + (h - hudTop - hudBottom - worldH * s) / 2;
  const X = (x: number) => ox + x * s, Y = (y: number) => oy + y * s;

  // Funnel.
  ctx.strokeStyle = colors.line;
  ctx.lineWidth = Math.max(1.5, s * 0.06);
  ctx.beginPath();
  ctx.moveTo(X(b.width / 2 - 2.2), Y(-0.6)); ctx.lineTo(X(b.width / 2 - 0.35), Y(0.4));
  ctx.moveTo(X(b.width / 2 + 2.2), Y(-0.6)); ctx.lineTo(X(b.width / 2 + 0.35), Y(0.4));
  ctx.stroke();

  // Pegs.
  ctx.fillStyle = colors.peg;
  for (const p of b.pegs) { ctx.beginPath(); ctx.arc(X(p.x), Y(p.y), Math.max(1.2, PEG_R * s), 0, Math.PI * 2); ctx.fill(); }

  // Bin walls and frame.
  ctx.strokeStyle = colors.line;
  ctx.beginPath();
  for (let i = 0; i <= b.bins; i++) { ctx.moveTo(X(i), Y(b.binTop)); ctx.lineTo(X(i), Y(b.floor)); }
  ctx.moveTo(X(0), Y(0.3)); ctx.lineTo(X(0), Y(b.floor)); ctx.lineTo(X(b.width), Y(b.floor)); ctx.lineTo(X(b.width), Y(0.3));
  ctx.stroke();

  // Piles: marbles stacked three across; they shrink when the tallest pile is squeezed to fit.
  const scale = pileScale(b);
  ctx.fillStyle = colors.pile;
  for (let i = 0; i < b.bins; i++) {
    const c = b.counts[i] ?? 0;
    if (!c) continue;
    const height = c * scale * s;
    const cols = 3, rows = Math.ceil(c / cols);
    const cell = Math.min((s * 0.9) / cols, height / rows);
    const rad = Math.max(0.6, cell * 0.46);
    if (rad < 1.1) {
      ctx.fillRect(X(i + 0.05), Y(b.floor) - height, s * 0.9, height);
      continue;
    }
    for (let k = 0; k < c; k++) {
      const col = k % cols, row = Math.floor(k / cols);
      const x = X(i + 0.05) + (col + 0.5 + (row % 2 ? 0.25 : -0.25) * (rows > 1 ? 1 : 0)) * ((s * 0.9) / cols);
      ctx.beginPath(); ctx.arc(Math.min(X(i + 0.95) - rad, Math.max(X(i + 0.05) + rad, x)), Y(b.floor) - (row + 0.5) * cell, rad, 0, Math.PI * 2); ctx.fill();
    }
  }

  // Falling marbles.
  ctx.fillStyle = colors.marble;
  const mr = Math.max(1.5, MARBLE_R * s);
  for (const m of b.marbles) { ctx.beginPath(); ctx.arc(X(m.x), Y(m.y), mr, 0, Math.PI * 2); ctx.fill(); }

  // Bell curve fitted to what has landed so far.
  if (opts.curve && b.landed >= 20) {
    const { mean, sd } = stats(b);
    if (sd > 0.05) {
      const centre = (b.bins - 1) / 2;
      ctx.strokeStyle = colors.curve;
      ctx.lineWidth = Math.max(2, s * 0.08);
      ctx.beginPath();
      for (let k = 0; k <= 200; k++) {
        const x = (k / 200) * b.width;
        const z = (x - 0.5 - centre - mean) / sd;
        const expected = (b.landed / (sd * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * z * z);
        const y = Y(b.floor) - Math.min(expected * scale, b.floor - b.binTop + 0.6) * s;
        if (k === 0) ctx.moveTo(X(x), y); else ctx.lineTo(X(x), y);
      }
      ctx.stroke();
    }
  }

  if (opts.hud) {
    const fs = Math.max(11, Math.min(15, w / 36));
    ctx.textAlign = 'left';
    ctx.fillStyle = colors.muted;
    ctx.font = `600 ${fs}px ${MONO}`;
    opts.hud.lines.forEach((line, k) => ctx.fillText(line, 12, 8 + fs * (k + 1) * 1.35));
    if (opts.hud.big) {
      ctx.fillStyle = colors.ink;
      ctx.font = `800 ${fs * 2}px ${DISPLAY}`;
      ctx.textAlign = 'center';
      ctx.fillText(opts.hud.big, w / 2, h - fs * 1.1);
    }
  }
}
