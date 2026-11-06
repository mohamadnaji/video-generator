/**
 * Marble Galton Board: marbles bounce down a field of pegs into bins and pile up into a
 * bell curve. Pure logic, no DOM. World units: one peg spacing = 1, y points down.
 */
import { createRng, type Rng } from '@shared/math/random';

export interface Params {
  rows: number;
  /** Board tilt in degrees; positive leans gravity to the right. */
  tiltDeg: number;
  /** Sideways wind, as a share of gravity (positive = to the right). */
  wind: number;
  /** Bounciness of a peg hit, 0..1. */
  bounce: number;
  /** Marbles released per second. */
  rate: number;
  /** Total marbles in one run. */
  total: number;
}

export interface Marble { x: number; y: number; vx: number; vy: number; bin: number }

export interface Board {
  rows: number;
  /** Board width; bins sit between x = 0 and x = width, one unit each. */
  width: number;
  bins: number;
  pegs: { x: number; y: number }[];
  /** y of the first peg row and of the bin tops. */
  pegTop: number;
  binTop: number;
  floor: number;
  counts: number[];
  marbles: Marble[];
  released: number;
  landed: number;
  /** Fractional marble left over between frames, so the release rate stays exact. */
  carry: number;
  rng: Rng;
}

export const DEFAULT_PARAMS: Params = { rows: 12, tiltDeg: 0, wind: 0, bounce: 0.45, rate: 40, total: 1000 };
export const G = 30;
export const MARBLE_R = 0.17;
export const PEG_R = 0.1;
const ROW_DY = 0.866;
const BIN_DEPTH = 9;
const SUBSTEPS = 6;
/** Air and rolling drag (per second). Without it marbles skip rows and the curve flattens. */
const DRAG = 3.5;

/** Builds an empty board. The last peg row sits right above the bin walls. */
export function createBoard(rows: number, seed?: number): Board {
  const bins = rows + 1;
  const width = bins;
  const pegTop = 1.5;
  const pegs: { x: number; y: number }[] = [];
  for (let i = 0; i < rows; i++) {
    const y = pegTop + i * ROW_DY;
    const onWalls = (rows - 1 - i) % 2 === 0;
    for (let x = onWalls ? 1 : 0.5; x < width - 0.01; x += 1) pegs.push({ x, y });
  }
  const binTop = pegTop + (rows - 1) * ROW_DY + 0.75;
  return {
    rows, width, bins, pegs, pegTop, binTop, floor: binTop + BIN_DEPTH,
    counts: new Array<number>(bins).fill(0), marbles: [], released: 0, landed: 0, carry: 0,
    rng: createRng(seed),
  };
}

/** World units of pile height per marble, squeezed so the tallest pile always fits in its bin. */
export function pileScale(b: Board): number {
  const perMarble = (2 * MARBLE_R) ** 2 * 0.9;
  const max = Math.max(1, ...b.counts) * perMarble;
  return max > BIN_DEPTH * 0.95 ? (BIN_DEPTH * 0.95) / Math.max(1, ...b.counts) : perMarble;
}

/** Height of a bin's pile in world units. */
export const pileHeight = (b: Board, bin: number): number => (b.counts[bin] ?? 0) * pileScale(b);

function release(b: Board): void {
  b.marbles.push({ x: b.width / 2 + b.rng.range(-0.04, 0.04), y: 0.2, vx: b.rng.range(-0.3, 0.3), vy: 0, bin: -1 });
  b.released++;
}

/** Advances the board by dt seconds. */
export function step(b: Board, p: Params, dt: number): void {
  b.carry += p.rate * dt;
  while (b.carry >= 1 && b.released < p.total) { release(b); b.carry -= 1; }
  if (b.released >= p.total) b.carry = 0;

  const tilt = (p.tiltDeg * Math.PI) / 180;
  const ax = G * Math.sin(tilt) + G * p.wind, ay = G * Math.cos(tilt);
  const h = dt / SUBSTEPS;
  const hit = MARBLE_R + PEG_R;

  for (let k = 0; k < SUBSTEPS; k++) {
    for (let m = b.marbles.length - 1; m >= 0; m--) {
      const mb = b.marbles[m]!;
      const damp = Math.exp(-DRAG * h);
      mb.vx = (mb.vx + ax * h) * damp; mb.vy = (mb.vy + ay * h) * damp;
      mb.x += mb.vx * h; mb.y += mb.vy * h;

      // Side walls.
      if (mb.x < MARBLE_R) { mb.x = MARBLE_R; mb.vx = Math.abs(mb.vx) * p.bounce; }
      if (mb.x > b.width - MARBLE_R) { mb.x = b.width - MARBLE_R; mb.vx = -Math.abs(mb.vx) * p.bounce; }

      if (mb.y < b.binTop) {
        const row = Math.round((mb.y - b.pegTop) / ROW_DY);
        if (row < 0 || row >= b.rows) continue;
        for (const pg of b.pegs) {
          if (Math.abs(pg.y - mb.y) > hit || Math.abs(pg.x - mb.x) > hit) continue;
          const dx = mb.x - pg.x, dy = mb.y - pg.y, d = Math.hypot(dx, dy);
          if (d >= hit || d === 0) continue;
          const nx = dx / d, ny = dy / d;
          mb.x = pg.x + nx * hit; mb.y = pg.y + ny * hit;
          const vn = mb.vx * nx + mb.vy * ny;
          if (vn < 0) {
            mb.vx -= (1 + p.bounce) * vn * nx;
            mb.vy -= (1 + p.bounce) * vn * ny;
            // A tiny random nudge: real pegs and marbles are never perfect.
            const j = b.rng.range(-0.25, 0.25);
            mb.vx += -ny * j; mb.vy += nx * j;
          }
        }
      } else {
        // Inside a bin: stay between its walls and fall onto the pile.
        if (mb.bin < 0) mb.bin = Math.min(b.bins - 1, Math.max(0, Math.floor(mb.x)));
        const lo = mb.bin + MARBLE_R, hi = mb.bin + 1 - MARBLE_R;
        if (mb.x < lo) { mb.x = lo; mb.vx = Math.abs(mb.vx) * 0.3; }
        if (mb.x > hi) { mb.x = hi; mb.vx = -Math.abs(mb.vx) * 0.3; }
        if (mb.y + MARBLE_R >= b.floor - pileHeight(b, mb.bin)) {
          b.counts[mb.bin]!++;
          b.landed++;
          b.marbles.splice(m, 1);
        }
      }
    }
  }
}

export const finished = (b: Board, p: Params): boolean => b.released >= p.total && b.marbles.length === 0;

/** Mean and standard deviation of landed marbles, in bins measured from the centre bin. */
export function stats(b: Board): { mean: number; sd: number } {
  if (b.landed === 0) return { mean: 0, sd: 0 };
  const centre = (b.bins - 1) / 2;
  let sum = 0;
  b.counts.forEach((c, i) => { sum += c * (i - centre); });
  const mean = sum / b.landed;
  let v = 0;
  b.counts.forEach((c, i) => { v += c * (i - centre - mean) ** 2; });
  return { mean, sd: Math.sqrt(v / b.landed) };
}
