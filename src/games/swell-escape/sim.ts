/**
 * Swell Escape simulation. Pure logic: no DOM, no drawing, so it can be unit tested
 * and reused by both the game page and the home page preview.
 *
 * The wall is a closed ring of N points in a WORLD x WORLD square. A few consecutive
 * segments are left open (the opening). The ball reflects off every other segment;
 * each hit pushes the wall outward around the contact point, more for spots that
 * have been hit before. A swell is only applied if the wall stays a simple polygon
 * (no self-crossing, no pinching), so it can never fold into a loop.
 */
import type { Vec } from '@shared/math/vec';
import { createRng, type Rng } from '@shared/math/random';
import {
  boundingBox, pointInPolygon, pointSegment, polygonArea, resampleClosed,
  ringDistance, segmentSegmentDistance, segmentsCross, wrapIndex,
} from '@shared/math/geometry';

export const WORLD = 1000;
export const POINTS = 400;
/** Closest two non-neighbouring parts of the wall may get after a swell. */
const MIN_WALL_GAP = 6;
/** Keep the wall inside the play area. */
const EDGE_MARGIN = 8;

export interface SwellSettings {
  speed: number;     // world units per second
  swell: number;     // outward push on the first hit, world units
  growth: number;    // extra push per previous hit at the same spot (0.35 = +35%)
  spread: number;    // swelling width, in wall points (Gaussian sigma)
  opening: number;   // opening width, world units
  radius: number;    // ball radius, world units
}

export const DEFAULT_SETTINGS: SwellSettings = { speed: 480, swell: 5, growth: 0.35, spread: 7, opening: 64, radius: 13 };

export interface Ball { x: number; y: number; vx: number; vy: number }

export interface StepEvents {
  bounces: Vec[];
  escaped: boolean;
}

export class SwellSim {
  settings: SwellSettings;
  /** Current wall points. */
  wall: Vec[] = [];
  /** Wall before any swelling (for measuring how far it moved). */
  private rest: Vec[] = [];
  private original: Vec[] = [];
  /** How often each wall point has been hit (Gaussian-weighted). */
  heat = new Float32Array(POINTS);
  /** True for segments that are part of the opening. */
  open: boolean[] = new Array(POINTS).fill(false);
  private taper = new Float32Array(POINTS);
  /** Wall points at the two ends of the opening. */
  lipA = 0;
  lipB = 0;
  private gapCenter = 0;
  private originalGap = 0;

  ball: Ball = { x: WORLD / 2, y: WORLD / 2, vx: 0, vy: 0 };
  bounces = 0;
  elapsed = 0;
  escaped = false;
  /** Largest distance any wall point has moved, in world units. */
  maxSwell = 0;
  shapeWidth = 1;
  private rng: Rng;

  constructor(settings: Partial<SwellSettings> = {}, rng: Rng = createRng()) {
    this.settings = { ...DEFAULT_SETTINGS, ...settings };
    this.rng = rng;
  }

  /** Loads a new outline. `gapIndex` picks the opening; default is the top-most point. */
  setShape(points: readonly Vec[], gapIndex?: number): void {
    if (points.length < 3) throw new Error('A shape needs at least 3 points');
    let ring = resampleClosed(points, POINTS);
    if (polygonArea(ring) < 0) ring = ring.reverse();
    this.original = ring;
    if (gapIndex === undefined) {
      gapIndex = 0;
      ring.forEach((p, j) => { if (p.y < ring[gapIndex!]!.y) gapIndex = j; });
    }
    this.originalGap = wrapIndex(gapIndex, POINTS);
    this.restart();
  }

  /** Puts the wall back to its original outline and relaunches the ball. */
  restart(): void {
    this.wall = this.original.map((p) => ({ ...p }));
    this.rest = this.original.map((p) => ({ ...p }));
    this.heat = new Float32Array(POINTS);
    this.gapCenter = this.originalGap;
    this.computeOpening();
    this.shapeWidth = boundingBox(this.wall).width || 1;
    this.resetRun();
    this.launch(this.roomiestPoint());
  }

  /** Drops the ball at a point (if it's inside the shape). Returns whether it was placed. */
  dropBall(p: Vec): boolean {
    if (!this.contains(p)) return false;
    this.resetRun();
    this.launch(p);
    return true;
  }

  /** Moves the opening to the wall point nearest `p` if it's within `reach`. */
  moveOpening(p: Vec, reach = 45): boolean {
    let best = 0, bestD = Infinity;
    this.wall.forEach((q, j) => {
      const d = Math.hypot(q.x - p.x, q.y - p.y);
      if (d < bestD) { bestD = d; best = j; }
    });
    if (bestD > reach) return false;
    this.gapCenter = best;
    this.computeOpening();
    return true;
  }

  /** Re-applies the opening width after a settings change. */
  updateOpening(): void { this.computeOpening(); }

  setSpeed(speed: number): void {
    this.settings.speed = speed;
    const s = Math.hypot(this.ball.vx, this.ball.vy) || 1;
    this.ball.vx *= speed / s;
    this.ball.vy *= speed / s;
  }

  contains(p: Vec): boolean { return pointInPolygon(p.x, p.y, this.wall); }

  step(dt: number): StepEvents {
    const ev: StepEvents = { bounces: [], escaped: false };
    const b = this.ball, r = this.settings.radius;
    const speed = Math.hypot(b.vx, b.vy);
    // Sub-step so the ball never moves more than a fraction of its radius per step.
    const n = Math.max(1, Math.ceil((speed * dt) / (r * 0.4)));
    const h = dt / n;
    for (let k = 0; k < n; k++) {
      b.x += b.vx * h;
      b.y += b.vy * h;
      if (!this.escaped) this.collide(ev);
    }
    if (!this.escaped) {
      this.elapsed += dt;
      const lipA = this.wall[this.lipA]!, lipB = this.wall[this.lipB]!;
      if (!this.contains(b) && pointSegment(b.x, b.y, lipA, lipB).d > r) {
        this.escaped = true;
        ev.escaped = true;
      }
    }
    return ev;
  }

  /** Ball is far enough outside that there's nothing left to simulate. */
  get offscreen(): boolean {
    const { x, y } = this.ball, m = 200;
    return x < -m || y < -m || x > WORLD + m || y > WORLD + m;
  }

  // ---------- internals ----------

  private resetRun(): void {
    this.bounces = 0;
    this.elapsed = 0;
    this.escaped = false;
    this.maxSwell = 0;
  }

  private launch(p: Vec): void {
    const t = this.rng.range(0, 2 * Math.PI), s = this.settings.speed;
    this.ball = { x: p.x, y: p.y, vx: Math.cos(t) * s, vy: Math.sin(t) * s };
  }

  /** Point inside the shape furthest from the wall, sampled on a grid. */
  private roomiestPoint(): Vec {
    const bb = boundingBox(this.wall);
    let best: Vec = { x: WORLD / 2, y: WORLD / 2 }, bestD = -1;
    for (let i = 1; i < 24; i++) for (let j = 1; j < 24; j++) {
      const p = { x: bb.x0 + (bb.width * i) / 24, y: bb.y0 + (bb.height * j) / 24 };
      if (!this.contains(p)) continue;
      let d = Infinity;
      for (let k = 0; k < POINTS; k++) d = Math.min(d, pointSegment(p.x, p.y, this.wall[k]!, this.wall[(k + 1) % POINTS]!).d);
      if (d > bestD) { bestD = d; best = p; }
    }
    return best;
  }

  private segLength(i: number): number {
    const a = this.wall[i]!, b = this.wall[(i + 1) % POINTS]!;
    return Math.hypot(b.x - a.x, b.y - a.y);
  }

  private computeOpening(): void {
    const half = this.settings.opening / 2;
    this.open = new Array(POINTS).fill(false);
    let acc = 0, i = this.gapCenter;
    while (acc < half) { this.open[i] = true; acc += this.segLength(i); i = (i + 1) % POINTS; }
    this.lipB = i;
    acc = 0; i = wrapIndex(this.gapCenter - 1, POINTS);
    while (acc < half) { this.open[i] = true; acc += this.segLength(i); i = wrapIndex(i - 1, POINTS); }
    this.lipA = (i + 1) % POINTS;

    // Swelling fades out near the opening so its lips stay put.
    const openPts: number[] = [];
    for (let j = 0; j < POINTS; j++) if (this.open[j] || this.open[wrapIndex(j - 1, POINTS)]) openPts.push(j);
    for (let j = 0; j < POINTS; j++) {
      let d = Infinity;
      for (const g of openPts) d = Math.min(d, ringDistance(j, g, POINTS));
      const t = Math.min(1, d / 12);
      this.taper[j] = t * t * (3 - 2 * t);
    }
  }

  private collide(ev: StepEvents): void {
    const b = this.ball, r = this.settings.radius;
    for (let iter = 0; iter < 3; iter++) {
      let best: (ReturnType<typeof pointSegment> & { i: number; depth: number }) | null = null;
      for (let i = 0; i < POINTS; i++) {
        if (this.open[i]) continue;
        const s = pointSegment(b.x, b.y, this.wall[i]!, this.wall[(i + 1) % POINTS]!);
        if (s.d < r && (!best || r - s.d > best.depth)) best = { ...s, i, depth: r - s.d };
      }
      if (!best) return;

      let nx: number, ny: number;
      if (best.d > 1e-6) { nx = (b.x - best.qx) / best.d; ny = (b.y - best.qy) / best.d; }
      else {
        const a = this.wall[best.i]!, c = this.wall[(best.i + 1) % POINTS]!, l = Math.hypot(c.x - a.x, c.y - a.y) || 1;
        nx = -(c.y - a.y) / l; ny = (c.x - a.x) / l;
      }
      b.x = best.qx + nx * r;
      b.y = best.qy + ny * r;
      const vn = b.vx * nx + b.vy * ny;
      if (vn < 0) {
        // Mirror reflection: angle in equals angle out.
        b.vx -= 2 * vn * nx;
        b.vy -= 2 * vn * ny;
        this.bounces++;
        ev.bounces.push({ x: best.qx, y: best.qy });
        if (this.settings.swell > 0) this.swellAt(best.i + best.t);
      }
    }
  }

  /** Normals averaged over a window so neighbouring points push the same way (no kinks). */
  private smoothNormals(k: number): Vec[] {
    const raw = this.wall.map((_, j) => {
      const a = this.wall[wrapIndex(j - 1, POINTS)]!, c = this.wall[(j + 1) % POINTS]!;
      const tx = c.x - a.x, ty = c.y - a.y, l = Math.hypot(tx, ty) || 1;
      return { x: ty / l, y: -tx / l };
    });
    return raw.map((_, j) => {
      let x = 0, y = 0;
      for (let o = -k; o <= k; o++) {
        const q = raw[wrapIndex(j + o, POINTS)]!, w = 1 - Math.abs(o) / (k + 1);
        x += q.x * w; y += q.y * w;
      }
      const l = Math.hypot(x, y) || 1;
      return { x: x / l, y: y / l };
    });
  }

  /** The changed stretch [lo, hi] must not cross or pinch against any other part of the wall. */
  private wallIsSimple(lo: number, hi: number): boolean {
    for (let ii = lo - 1; ii <= hi; ii++) {
      const i = wrapIndex(ii, POINTS), a = this.wall[i]!, b = this.wall[(i + 1) % POINTS]!;
      for (let j = 0; j < POINTS; j++) {
        const d = ringDistance(i, j, POINTS);
        if (d <= 1) continue;
        const c = this.wall[j]!, e = this.wall[(j + 1) % POINTS]!;
        if (segmentsCross(a, b, c, e)) return false;
        if (d > 3 && segmentSegmentDistance(a, b, c, e) < MIN_WALL_GAP) return false;
      }
    }
    return true;
  }

  private swellAt(hit: number): void {
    const { spread: sig, swell, growth } = this.settings;
    const normals = this.smoothNormals(Math.max(2, Math.round(sig / 2)));
    const centre = wrapIndex(Math.round(hit), POINTS);
    const amp = swell * Math.min(1 + growth * this.heat[centre]!, 6);
    const lo = Math.floor(hit - sig * 4), hi = Math.ceil(hit + sig * 4);
    const idx: number[] = [];
    for (let j = lo; j <= hi; j++) idx.push(wrapIndex(j, POINTS));
    const saved = idx.map((j) => ({ ...this.wall[j]! }));
    const weights = idx.map((j) => {
      const d = ringDistance(j, hit, POINTS);
      return Math.exp(-(d * d) / (2 * sig * sig)) * this.taper[j]!;
    });

    // Try the full swell, then smaller ones, until the wall stays simple.
    for (let f = 1; f >= 0.06; f /= 2) {
      idx.forEach((j, k) => {
        const m = amp * weights[k]! * f, n = normals[j]!, s = saved[k]!;
        this.wall[j] = {
          x: Math.max(EDGE_MARGIN, Math.min(WORLD - EDGE_MARGIN, s.x + n.x * m)),
          y: Math.max(EDGE_MARGIN, Math.min(WORLD - EDGE_MARGIN, s.y + n.y * m)),
        };
      });
      if (this.wallIsSimple(lo, hi)) break;
      idx.forEach((j, k) => { this.wall[j] = { ...saved[k]! }; });
    }

    idx.forEach((j, k) => {
      this.heat[j]! += weights[k]!;
      const moved = Math.hypot(this.wall[j]!.x - this.rest[j]!.x, this.wall[j]!.y - this.rest[j]!.y);
      if (moved > this.maxSwell) this.maxSwell = moved;
    });
  }
}
