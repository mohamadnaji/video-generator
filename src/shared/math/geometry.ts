import type { Vec } from './vec';

/** Signed area; positive when the points run clockwise on screen (y down). */
export function polygonArea(p: readonly Vec[]): number {
  let a = 0;
  for (let i = 0; i < p.length; i++) {
    const q = p[i]!, w = p[(i + 1) % p.length]!;
    a += q.x * w.y - w.x * q.y;
  }
  return a / 2;
}

/** Even-odd ray-casting test. */
export function pointInPolygon(x: number, y: number, p: readonly Vec[]): boolean {
  let inside = false;
  for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
    const a = p[i]!, b = p[j]!;
    if (a.y > y !== b.y > y && x < ((b.x - a.x) * (y - a.y)) / (b.y - a.y) + a.x) inside = !inside;
  }
  return inside;
}

export interface SegmentHit { d: number; t: number; qx: number; qy: number }

/** Distance from (x, y) to segment ab, with the closest point and its parameter t in [0, 1]. */
export function pointSegment(x: number, y: number, a: Vec, b: Vec): SegmentHit {
  const dx = b.x - a.x, dy = b.y - a.y;
  const l = dx * dx + dy * dy || 1;
  const t = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / l));
  const qx = a.x + dx * t, qy = a.y + dy * t;
  return { d: Math.hypot(x - qx, y - qy), t, qx, qy };
}

const orient = (a: Vec, b: Vec, c: Vec) => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);

/** True when segments ab and cd properly cross. */
export function segmentsCross(a: Vec, b: Vec, c: Vec, d: Vec): boolean {
  const d1 = orient(c, d, a), d2 = orient(c, d, b), d3 = orient(a, b, c), d4 = orient(a, b, d);
  return d1 > 0 !== d2 > 0 && d3 > 0 !== d4 > 0;
}

export function segmentSegmentDistance(a: Vec, b: Vec, c: Vec, d: Vec): number {
  if (segmentsCross(a, b, c, d)) return 0;
  return Math.min(
    pointSegment(a.x, a.y, c, d).d,
    pointSegment(b.x, b.y, c, d).d,
    pointSegment(c.x, c.y, a, b).d,
    pointSegment(d.x, d.y, a, b).d,
  );
}

/** Redistributes a closed outline into `n` points evenly spaced along its perimeter. */
export function resampleClosed(pts: readonly Vec[], n: number): Vec[] {
  if (pts.length < 2) throw new Error('resampleClosed needs at least 2 points');
  const c = [...pts, pts[0]!];
  const cum = [0];
  for (let i = 1; i < c.length; i++) cum.push(cum[i - 1]! + Math.hypot(c[i]!.x - c[i - 1]!.x, c[i]!.y - c[i - 1]!.y));
  const total = cum[cum.length - 1]!;
  const out: Vec[] = [];
  let k = 1;
  for (let j = 0; j < n; j++) {
    const t = (j * total) / n;
    while (k < cum.length - 1 && cum[k]! < t) k++;
    const span = cum[k]! - cum[k - 1]! || 1;
    const s = (t - cum[k - 1]!) / span;
    const p0 = c[k - 1]!, p1 = c[k]!;
    out.push({ x: p0.x + (p1.x - p0.x) * s, y: p0.y + (p1.y - p0.y) * s });
  }
  return out;
}

/** Scales and centres points so their larger side equals `size`, centred on (cx, cy). */
export function fitToBox(pts: readonly Vec[], size: number, cx: number, cy: number): Vec[] {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of pts) { x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y); }
  const s = size / (Math.max(x1 - x0, y1 - y0) || 1);
  const mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
  return pts.map((p) => ({ x: cx + (p.x - mx) * s, y: cy + (p.y - my) * s }));
}

/** Distance between two indices on a ring of `n` items. */
export function ringDistance(i: number, j: number, n: number): number {
  const d = Math.abs(i - j) % n;
  return Math.min(d, n - d);
}

export const wrapIndex = (i: number, n: number): number => ((i % n) + n) % n;

export function boundingBox(pts: readonly Vec[]) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of pts) { x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y); }
  return { x0, y0, x1, y1, width: x1 - x0, height: y1 - y0 };
}
