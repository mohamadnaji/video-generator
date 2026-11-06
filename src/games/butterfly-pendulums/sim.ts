/**
 * Butterfly Pendulums: many single or double pendulums that start a hair apart.
 * Pure logic, no DOM. Angles are measured from straight down, in radians; lengths in metres.
 */
export interface Params {
  /** 1 = simple pendulum, 2 = double pendulum. */
  arms: 1 | 2;
  g: number;
  l1: number;
  l2: number;
  m1: number;
  m2: number;
}

export interface Swarm {
  n: number;
  th1: Float64Array;
  th2: Float64Array;
  w1: Float64Array;
  w2: Float64Array;
  /** Seconds since release. */
  t: number;
  /** Time when the tips first spread past SPLIT_FRACTION of the reach, or null. */
  splitAt: number | null;
}

export const DEFAULT_PARAMS: Params = { arms: 2, g: 9.81, l1: 1, l2: 1, m1: 1, m2: 1 };
/** Tips count as "split" once their spread passes this share of the full reach. */
export const SPLIT_FRACTION = 0.1;
const SUBSTEP = 1 / 240;

/**
 * Creates n pendulums. All start at `angleDeg` (both arms), and each one is `offsetDeg`
 * further out than the one before, so the whole fan spans (n - 1) × offset.
 */
export function createSwarm(n: number, angleDeg: number, offsetDeg: number): Swarm {
  const s: Swarm = {
    n,
    th1: new Float64Array(n), th2: new Float64Array(n),
    w1: new Float64Array(n), w2: new Float64Array(n),
    t: 0, splitAt: null,
  };
  const rad = Math.PI / 180;
  for (let i = 0; i < n; i++) {
    const a = (angleDeg + i * offsetDeg) * rad;
    s.th1[i] = a;
    s.th2[i] = a;
  }
  return s;
}

/** Angular accelerations for one pendulum. */
export function accel(p: Params, th1: number, th2: number, w1: number, w2: number): [number, number] {
  const { g, l1, l2, m1, m2 } = p;
  if (p.arms === 1) return [(-g / l1) * Math.sin(th1), 0];
  const d = th1 - th2;
  const sd = Math.sin(d), cd = Math.cos(d);
  const den = 2 * m1 + m2 - m2 * Math.cos(2 * d);
  const a1 = (-g * (2 * m1 + m2) * Math.sin(th1) - m2 * g * Math.sin(th1 - 2 * th2) - 2 * sd * m2 * (w2 * w2 * l2 + w1 * w1 * l1 * cd)) / (l1 * den);
  const a2 = (2 * sd * (w1 * w1 * l1 * (m1 + m2) + g * (m1 + m2) * Math.cos(th1) + w2 * w2 * l2 * m2 * cd)) / (l2 * den);
  return [a1, a2];
}

/** One RK4 step of size h for pendulum i. */
function rk4(p: Params, s: Swarm, i: number, h: number): void {
  const a = s.th1[i]!, b = s.th2[i]!, c = s.w1[i]!, d = s.w2[i]!;
  const [k1c, k1d] = accel(p, a, b, c, d);
  const [k2c, k2d] = accel(p, a + (h / 2) * c, b + (h / 2) * d, c + (h / 2) * k1c, d + (h / 2) * k1d);
  const c2 = c + (h / 2) * k1c, d2 = d + (h / 2) * k1d;
  const c3 = c + (h / 2) * k2c, d3 = d + (h / 2) * k2d;
  const [k3c, k3d] = accel(p, a + (h / 2) * c2, b + (h / 2) * d2, c3, d3);
  const c4 = c + h * k3c, d4 = d + h * k3d;
  const [k4c, k4d] = accel(p, a + h * c3, b + h * d3, c4, d4);
  s.th1[i] = a + (h / 6) * (c + 2 * c2 + 2 * c3 + c4);
  s.th2[i] = b + (h / 6) * (d + 2 * d2 + 2 * d3 + d4);
  s.w1[i] = c + (h / 6) * (k1c + 2 * k2c + 2 * k3c + k4c);
  s.w2[i] = d + (h / 6) * (k1d + 2 * k2d + 2 * k3d + k4d);
}

/** Advances every pendulum by dt seconds using fixed RK4 substeps. */
export function step(p: Params, s: Swarm, dt: number): void {
  const steps = Math.max(1, Math.ceil(dt / SUBSTEP));
  const h = dt / steps;
  for (let k = 0; k < steps; k++) for (let i = 0; i < s.n; i++) rk4(p, s, i, h);
  s.t += dt;
  if (s.splitAt === null && s.n > 1 && spread(p, s) > SPLIT_FRACTION) s.splitAt = s.t;
}

/** Tip position of pendulum i, in metres, pivot at the origin and y pointing down. */
export function tip(p: Params, s: Swarm, i: number): { x: number; y: number } {
  const x1 = p.l1 * Math.sin(s.th1[i]!), y1 = p.l1 * Math.cos(s.th1[i]!);
  if (p.arms === 1) return { x: x1, y: y1 };
  return { x: x1 + p.l2 * Math.sin(s.th2[i]!), y: y1 + p.l2 * Math.cos(s.th2[i]!) };
}

export const reach = (p: Params): number => (p.arms === 1 ? p.l1 : p.l1 + p.l2);

/** Root-mean-square distance of the tips from their average, as a share of the reach (0 = all together). */
export function spread(p: Params, s: Swarm): number {
  if (s.n < 2) return 0;
  let mx = 0, my = 0;
  const pts = [];
  for (let i = 0; i < s.n; i++) { const t = tip(p, s, i); pts.push(t); mx += t.x; my += t.y; }
  mx /= s.n; my /= s.n;
  let sum = 0;
  for (const t of pts) sum += (t.x - mx) ** 2 + (t.y - my) ** 2;
  return Math.sqrt(sum / s.n) / reach(p);
}

/** Total mechanical energy of pendulum i (joules), used to check the integrator. */
export function energy(p: Params, s: Swarm, i: number): number {
  const { g, l1, l2, m1, m2 } = p;
  const a = s.th1[i]!, b = s.th2[i]!, c = s.w1[i]!, d = s.w2[i]!;
  if (p.arms === 1) return 0.5 * m1 * l1 * l1 * c * c - m1 * g * l1 * Math.cos(a);
  const ke = 0.5 * m1 * l1 * l1 * c * c + 0.5 * m2 * (l1 * l1 * c * c + l2 * l2 * d * d + 2 * l1 * l2 * c * d * Math.cos(a - b));
  const pe = -(m1 + m2) * g * l1 * Math.cos(a) - m2 * g * l2 * Math.cos(b);
  return ke + pe;
}
