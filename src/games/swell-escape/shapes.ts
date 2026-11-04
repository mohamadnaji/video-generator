import type { Vec } from '@shared/math/vec';
import type { Rng } from '@shared/math/random';
import { boundingBox, fitToBox, polygonArea } from '@shared/math/geometry';
import { WORLD } from './sim';

const polygon = (k: number, r: number, rot = -Math.PI / 2): Vec[] =>
  Array.from({ length: k }, (_, i) => {
    const t = rot + (i * 2 * Math.PI) / k;
    return { x: Math.cos(t) * r, y: Math.sin(t) * r };
  });

export const PRESETS = {
  circle: () => polygon(90, 1),
  square: () => [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1, y: 1 }, { x: 0, y: 1 }],
  hexagon: () => polygon(6, 1),
  star: () =>
    Array.from({ length: 10 }, (_, i) => {
      const t = -Math.PI / 2 + (i * Math.PI) / 5, r = i % 2 ? 0.48 : 1;
      return { x: Math.cos(t) * r, y: Math.sin(t) * r };
    }),
  heart: () =>
    Array.from({ length: 160 }, (_, i) => {
      const t = (i / 160) * 2 * Math.PI;
      return {
        x: 16 * Math.sin(t) ** 3,
        y: -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)),
      };
    }),
} satisfies Record<string, () => Vec[]>;

export type PresetName = keyof typeof PRESETS;
export const isPreset = (s: string): s is PresetName => s in PRESETS;

/** Fits any outline into the play area. */
export const fitShape = (pts: Vec[], size = 640): Vec[] => fitToBox(pts, size, WORLD / 2, WORLD / 2);

export function presetShape(name: PresetName): Vec[] {
  return fitShape(PRESETS[name]());
}

/** Shape area as a share of its bounding square; thin slivers score low. */
export function roominess(pts: readonly Vec[]): number {
  const bb = boundingBox(pts), side = Math.max(bb.width, bb.height) || 1;
  return Math.abs(polygonArea(pts)) / (side * side);
}
const MIN_ROOMINESS = 0.3;

/** A random shape with enough room inside to be fun (retries thin slivers). */
export function randomShape(rng: Rng): Vec[] {
  let best: Vec[] = [], bestScore = -1;
  for (let i = 0; i < 20; i++) {
    const s = randomOutline(rng), score = roominess(s);
    if (score >= MIN_ROOMINESS) return s;
    if (score > bestScore) { best = s; bestScore = score; }
  }
  return best;
}

/** One of three families: a smooth blob, an irregular polygon, or a jagged star. */
function randomOutline(rng: Rng): Vec[] {
  const family = rng.int(0, 3);
  const rot = rng.range(0, 2 * Math.PI);
  let pts: Vec[] = [];

  if (family === 0) {
    const harmonics = Array.from({ length: 6 }, (_, i) => {
      const k = i + 2;
      return { k, a: rng.range(0, 0.32) / Math.pow(k, 0.55), p: rng.range(0, 7) };
    });
    const n = 240;
    let radii = Array.from({ length: n }, (_, i) => {
      const t = (i / n) * 2 * Math.PI;
      return 1 + harmonics.reduce((s, h) => s + h.a * Math.cos(h.k * t + h.p), 0);
    });
    const mn = Math.min(...radii), mx = Math.max(...radii);
    if (mn < 0.4) radii = radii.map((r) => 0.4 + ((r - mn) * (mx - 0.4)) / (mx - mn));
    pts = radii.map((r, i) => {
      const t = rot + (i / n) * 2 * Math.PI;
      return { x: Math.cos(t) * r, y: Math.sin(t) * r };
    });
  } else if (family === 1) {
    const k = rng.int(3, 10);
    pts = Array.from({ length: k }, (_, i) => {
      const t = ((i + rng.range(-0.3, 0.3)) * 2 * Math.PI) / k + rot;
      const r = rng.range(0.5, 1);
      return { x: Math.cos(t) * r, y: Math.sin(t) * r };
    });
  } else {
    const k = rng.int(4, 10), inner = rng.range(0.4, 0.72);
    for (let i = 0; i < 2 * k; i++) {
      const t = rot + (i * Math.PI) / k, r = (i % 2 ? inner : 1) * rng.range(0.88, 1.08);
      pts.push({ x: Math.cos(t) * r, y: Math.sin(t) * r });
    }
  }
  return fitShape(pts);
}
