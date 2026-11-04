/**
 * Collision counter: a heavy block slides into a light one near a wall, on a
 * frictionless floor with perfectly elastic collisions. Event-driven, so the
 * count stays exact even for mass ratios of 10^8 (31,415 collisions).
 *
 * Positions are in CSS pixels along the floor; the wall's face is at `wall`.
 */
export interface CollisionState {
  m: number;          // small mass
  M: number;          // big mass
  exponent: number;   // M = 100^exponent
  smallSize: number;
  bigSize: number;
  x1: number; v1: number;  // small block left edge, velocity
  x2: number; v2: number;  // big block left edge, velocity
  speed: number;           // starting speed of the big block
  count: number;
  done: boolean;
}

export const WALL_X = 40;
export const SMALL_SIZE = 34;

/** Collisions needed for mass ratio 100^n: 3, 31, 314, 3141, 31415, ... */
export function createCollision(exponent: number, width: number): CollisionState {
  const M = Math.pow(100, exponent);
  const x1 = Math.max(width * 0.32, 140);
  const speed = Math.max(60, width * 0.12);
  return {
    m: 1, M, exponent,
    smallSize: SMALL_SIZE,
    bigSize: Math.min(150, 50 + exponent * 24),
    x1, v1: 0,
    x2: Math.max(width * 0.6, x1 + SMALL_SIZE + 60), v2: -speed,
    speed, count: 0, done: false,
  };
}

/** 1D elastic collision between masses m and M. */
export function elasticVelocities(m: number, M: number, u1: number, u2: number): [number, number] {
  return [((m - M) * u1 + 2 * M * u2) / (m + M), ((M - m) * u2 + 2 * m * u1) / (m + M)];
}

/**
 * Advances by dt seconds, resolving every collision inside the step exactly.
 * Returns how many collisions happened (for sound).
 */
export function stepCollision(c: CollisionState, dt: number, maxEvents = 200_000): number {
  let t = dt, events = 0;
  while (t > 0 && events < maxEvents) {
    let toBlock = Infinity, toWall = Infinity;
    const gap = c.x2 - (c.x1 + c.smallSize), closing = c.v1 - c.v2;
    if (closing > 0) toBlock = Math.max(0, gap / closing);
    if (c.v1 < 0) toWall = Math.max(0, (c.x1 - WALL_X) / -c.v1);
    const next = Math.min(toBlock, toWall);
    if (next > t) { c.x1 += c.v1 * t; c.x2 += c.v2 * t; break; }
    c.x1 += c.v1 * next; c.x2 += c.v2 * next; t -= next;
    if (toBlock <= toWall) {
      [c.v1, c.v2] = elasticVelocities(c.m, c.M, c.v1, c.v2);
      c.x2 = c.x1 + c.smallSize;
    } else {
      c.v1 = -c.v1;
      c.x1 = WALL_X;
    }
    c.count++;
    events++;
    // No more collisions once both move right and the big one is at least as fast.
    if (c.v1 >= 0 && c.v2 >= c.v1) c.done = true;
  }
  return events;
}

/** Both blocks have left the visible floor. */
export const collisionFinished = (c: CollisionState, width: number): boolean => c.done && c.x2 > width + 200;
