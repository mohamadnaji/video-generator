/**
 * Steady push: you push the small block (m), it pushes the big one (M).
 * Both sit on a floor with friction coefficient mu.
 */
export const G = 9.81;
export const MAX_SPEED = 40;

export interface PushParams { m: number; M: number; F: number; mu: number }

export interface PushForces extends PushParams {
  /** Push needed to get both blocks moving: mu·g·(m + M). */
  Fmin: number;
  /** Acceleration while moving (may be negative when slowing). */
  a: number;
  /** Contact force the small block passes to the big one. */
  N: number;
  moving: boolean;
}

export function pushForces(p: PushParams, velocity: number): PushForces {
  const { m, M, F, mu } = p;
  const Fmin = mu * G * (m + M);
  const moving = velocity > 1e-6 || F > Fmin;
  if (moving) return { ...p, Fmin, moving, a: F / (m + M) - mu * G, N: (M * F) / (m + M) };
  // At rest: static friction on the small block holds back part of the push.
  return { ...p, Fmin, moving, a: 0, N: Math.max(0, F - mu * m * G) };
}

export interface PushState { x: number; v: number }

/** Advances position and speed by dt seconds. */
export function stepPush(s: PushState, p: PushParams, dt: number): PushForces {
  const f = pushForces(p, s.v);
  if (p.F > f.Fmin) s.v += f.a * dt;
  else if (s.v > 0) {
    // Friction slows the pair down; the push still helps a little.
    const decel = p.mu * G - p.F / (p.m + p.M);
    s.v = Math.max(0, s.v - Math.max(decel, 0) * dt);
  }
  s.v = Math.min(s.v, MAX_SPEED);
  s.x += s.v * dt;
  return f;
}

export type PushStatus = 'moving' | 'slowing' | 'stuck';
export function pushStatus(f: PushForces, velocity: number): PushStatus {
  if (f.F > f.Fmin) return 'moving';
  return velocity > 0.01 ? 'slowing' : 'stuck';
}
