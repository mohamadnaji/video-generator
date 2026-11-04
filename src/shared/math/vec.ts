export interface Vec { x: number; y: number }

export const vec = (x = 0, y = 0): Vec => ({ x, y });
export const add = (a: Vec, b: Vec): Vec => ({ x: a.x + b.x, y: a.y + b.y });
export const sub = (a: Vec, b: Vec): Vec => ({ x: a.x - b.x, y: a.y - b.y });
export const scale = (a: Vec, s: number): Vec => ({ x: a.x * s, y: a.y * s });
export const dot = (a: Vec, b: Vec): number => a.x * b.x + a.y * b.y;
export const cross = (a: Vec, b: Vec): number => a.x * b.y - a.y * b.x;
export const length = (a: Vec): number => Math.hypot(a.x, a.y);
export const dist = (a: Vec, b: Vec): number => Math.hypot(a.x - b.x, a.y - b.y);
export function normalize(a: Vec): Vec {
  const l = Math.hypot(a.x, a.y);
  return l > 0 ? { x: a.x / l, y: a.y / l } : { x: 0, y: 0 };
}
/** Reflects velocity `v` off a surface with unit normal `n` (angle of incidence = angle of reflection). */
export function reflect(v: Vec, n: Vec): Vec {
  const d = 2 * dot(v, n);
  return { x: v.x - d * n.x, y: v.y - d * n.y };
}
export const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));
