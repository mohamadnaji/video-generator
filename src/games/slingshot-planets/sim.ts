/**
 * Slingshot Planets: launch moons around a star and see which crash, which escape and which
 * lock into orbit. Pure logic, no DOM. World units; the star sits at the origin, y points down.
 */
import { createRng, type Rng } from '@shared/math/random';

export type MoonStatus = 'flying' | 'orbit' | 'crashed' | 'escaped';

export interface Moon {
  id: number;
  x: number; y: number; vx: number; vy: number;
  status: MoonStatus;
  /** Total angle swept around the star, in radians. */
  swept: number;
  trail: { x: number; y: number }[];
}

export interface Burst { x: number; y: number; age: number }

export interface Params {
  /** Star mass as a multiple of the default. */
  starMass: number;
  /** Adds a giant planet whose gravity tugs on every moon. */
  giant: boolean;
}

export interface World {
  t: number;
  moons: Moon[];
  bursts: Burst[];
  launched: number; crashed: number; escaped: number; locked: number;
  /** Most recent headline event, for on-screen captions. */
  lastEvent: { text: string; kind: MoonStatus; at: number } | null;
  nextId: number;
  rng: Rng;
}

export const MU = 1.2e7;
export const STAR_R = 28;
export const GIANT_ORBIT = 340;
export const GIANT_R = 13;
export const GIANT_MU_SHARE = 0.03;
/** World radius that always fits on screen. */
export const VIEW_R = 500;
/** Edge of the system: a moon that drifts past it is lost to deep space. */
export const SYSTEM_R = VIEW_R * 1.15;
/** Full turns a moon must survive to count as locked in orbit. */
export const ORBIT_TURNS = 2;
const SUBSTEP = 1 / 240;
const SOFT2 = 4;
const TRAIL_LEN = 90;
const MAX_MOONS = 40;

export const DEFAULT_PARAMS: Params = { starMass: 1, giant: false };

export function createWorld(seed?: number): World {
  return { t: 0, moons: [], bursts: [], launched: 0, crashed: 0, escaped: 0, locked: 0, lastEvent: null, nextId: 1, rng: createRng(seed) };
}

export const starMu = (p: Params): number => MU * p.starMass;

/** Giant planet position at time t (circular orbit, counter-clockwise on screen). */
export function giantPos(p: Params, t: number): { x: number; y: number } {
  const w = Math.sqrt(starMu(p) / GIANT_ORBIT ** 3);
  return { x: GIANT_ORBIT * Math.cos(-w * t), y: GIANT_ORBIT * Math.sin(-w * t) };
}

/** Speed for a circular orbit at radius r, and the escape speed there. */
export function orbitSpeeds(p: Params, r: number): { circular: number; escape: number } {
  const circular = Math.sqrt(starMu(p) / Math.max(r, 1));
  return { circular, escape: circular * Math.SQRT2 };
}

function accel(p: Params, t: number, x: number, y: number): [number, number] {
  const r2 = x * x + y * y + SOFT2;
  const k = -starMu(p) / (r2 * Math.sqrt(r2));
  let ax = k * x, ay = k * y;
  if (p.giant) {
    const g = giantPos(p, t);
    const dx = x - g.x, dy = y - g.y, d2 = dx * dx + dy * dy + SOFT2;
    const kg = (-starMu(p) * GIANT_MU_SHARE) / (d2 * Math.sqrt(d2));
    ax += kg * dx; ay += kg * dy;
  }
  return [ax, ay];
}

/** Leapfrog (kick-drift-kick) step for a single body; returns the swept angle. */
function advance(p: Params, t: number, b: { x: number; y: number; vx: number; vy: number }, h: number): number {
  const before = Math.atan2(b.y, b.x);
  let [ax, ay] = accel(p, t, b.x, b.y);
  b.vx += ax * h / 2; b.vy += ay * h / 2;
  b.x += b.vx * h; b.y += b.vy * h;
  [ax, ay] = accel(p, t + h, b.x, b.y);
  b.vx += ax * h / 2; b.vy += ay * h / 2;
  let d = Math.atan2(b.y, b.x) - before;
  if (d > Math.PI) d -= 2 * Math.PI;
  if (d < -Math.PI) d += 2 * Math.PI;
  return d;
}

/** What happens to a body at its current spot, or null if it's still free. */
function outcome(p: Params, t: number, b: { x: number; y: number; vx: number; vy: number }): 'crashed' | 'escaped' | null {
  const r = Math.hypot(b.x, b.y);
  if (r < STAR_R) return 'crashed';
  if (p.giant) {
    const g = giantPos(p, t);
    if (Math.hypot(b.x - g.x, b.y - g.y) < GIANT_R + 3) return 'crashed';
  }
  if (r > SYSTEM_R) return 'escaped';
  return null;
}

export function launch(w: World, x: number, y: number, vx: number, vy: number): Moon {
  const m: Moon = { id: w.nextId++, x, y, vx, vy, status: 'flying', swept: 0, trail: [] };
  w.moons.push(m);
  w.launched++;
  // Keep the busiest scenes light: drop the oldest moon that isn't in orbit.
  if (w.moons.length > MAX_MOONS) {
    const i = w.moons.findIndex((mm) => mm.status !== 'orbit');
    w.moons.splice(i >= 0 ? i : 0, 1);
  }
  return m;
}

/**
 * Sprays `count` moons from one launch point with random speeds around circular speed.
 * Most crash or fly off; a lucky few settle into orbit.
 */
export function spray(w: World, p: Params, count: number, x = 0, y = -230): void {
  const r = Math.hypot(x, y);
  const { circular } = orbitSpeeds(p, r);
  const tx = -y / r, ty = x / r; // tangent (counter-clockwise on screen)
  for (let i = 0; i < count; i++) {
    const s = circular * w.rng.range(0.1, 1.8);
    const radial = circular * w.rng.range(-0.7, 0.7);
    launch(w, x, y, tx * s + (x / r) * radial, ty * s + (y / r) * radial);
  }
}

/** Advances the world by dt seconds. */
export function step(w: World, p: Params, dt: number): void {
  const steps = Math.max(1, Math.ceil(dt / SUBSTEP));
  const h = dt / steps;
  for (let k = 0; k < steps; k++) {
    for (const m of w.moons) {
      if (m.status === 'crashed' || m.status === 'escaped') continue;
      m.swept += advance(p, w.t, m, h);
      const end = outcome(p, w.t + h, m);
      if (end === 'crashed') {
        m.status = 'crashed'; w.crashed++;
        w.bursts.push({ x: m.x, y: m.y, age: 0 });
        w.lastEvent = { text: 'Crashed!', kind: 'crashed', at: w.t };
      } else if (end === 'escaped') {
        m.status = 'escaped'; w.escaped++;
        w.lastEvent = { text: 'Lost to space', kind: 'escaped', at: w.t };
      } else if (m.status === 'flying' && Math.abs(m.swept) >= ORBIT_TURNS * 2 * Math.PI) {
        m.status = 'orbit'; w.locked++;
        w.lastEvent = { text: 'Locked in orbit!', kind: 'orbit', at: w.t };
      }
    }
    w.t += h;
  }
  for (const m of w.moons) {
    if (m.status === 'crashed' || m.status === 'escaped') continue;
    m.trail.push({ x: m.x, y: m.y });
    if (m.trail.length > TRAIL_LEN) m.trail.shift();
  }
  w.moons = w.moons.filter((m) => m.status === 'flying' || m.status === 'orbit');
  for (const b of w.bursts) b.age += dt;
  w.bursts = w.bursts.filter((b) => b.age < 1.2);
}

/** Predicts a launch's path for up to `seconds`, stopping at a crash or escape. */
export function predict(w: World, p: Params, x: number, y: number, vx: number, vy: number, seconds = 5): { points: { x: number; y: number }[]; end: MoonStatus } {
  const b = { x, y, vx, vy };
  const points = [{ x, y }];
  const h = 1 / 120;
  let swept = 0, t = w.t;
  for (let i = 0; i < seconds / h; i++) {
    swept += advance(p, t, b, h);
    t += h;
    if (i % 2 === 0) points.push({ x: b.x, y: b.y });
    const end = outcome(p, t, b);
    if (end) return { points, end };
    if (Math.abs(swept) >= 2 * Math.PI + 0.3) return { points, end: 'orbit' };
  }
  return { points, end: 'flying' };
}
