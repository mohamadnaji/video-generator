import { describe, expect, it } from 'vitest';
import { createRng } from '@shared/math/random';
import { pointInPolygon, segmentsCross } from '@shared/math/geometry';
import { presetShape, randomShape } from './shapes';
import { POINTS, SwellSim } from './sim';
import { formatClock } from './format';

/** True if any two non-adjacent wall segments cross (the "loop inside the border" bug). */
function selfIntersects(sim: SwellSim): boolean {
  const P = sim.wall;
  for (let i = 0; i < POINTS; i++) {
    for (let j = i + 2; j < POINTS; j++) {
      if (i === 0 && j === POINTS - 1) continue;
      if (segmentsCross(P[i]!, P[i + 1]!, P[j]!, P[(j + 1) % POINTS]!)) return true;
    }
  }
  return false;
}

describe('SwellSim', () => {
  it('starts the ball inside the shape', () => {
    const sim = new SwellSim({}, createRng(1));
    sim.setShape(presetShape('circle'));
    expect(sim.contains(sim.ball)).toBe(true);
    expect(sim.wall).toHaveLength(POINTS);
  });

  it('keeps ball speed constant through bounces (elastic reflection)', () => {
    const sim = new SwellSim({ swell: 0, opening: 30 }, createRng(2));
    sim.setShape(presetShape('square'));
    for (let i = 0; i < 600; i++) sim.step(1 / 60);
    expect(sim.bounces).toBeGreaterThan(0);
    expect(Math.hypot(sim.ball.vx, sim.ball.vy)).toBeCloseTo(sim.settings.speed, 6);
  });

  it('swells the wall outward where it is hit', () => {
    const sim = new SwellSim({ opening: 30 }, createRng(3));
    sim.setShape(presetShape('circle'));
    for (let i = 0; i < 300; i++) sim.step(1 / 60);
    expect(sim.maxSwell).toBeGreaterThan(0);
  });

  // Regression: swellings used to fold the wall into a small loop inside the border.
  it.each([1, 2, 3, 4, 5, 6])('never lets the wall cross itself (seed %i)', (seed) => {
    const rng = createRng(seed);
    const sim = new SwellSim({ swell: 20, growth: 1, spread: 3, opening: 30, speed: 900 }, rng);
    sim.setShape(randomShape(rng), rng.int(0, POINTS));
    for (let i = 0; i < 1500 && !sim.escaped; i++) {
      sim.step(1 / 60);
      if (i % 50 === 0) expect(selfIntersects(sim)).toBe(false);
    }
    expect(selfIntersects(sim)).toBe(false);
  });

  it('eventually lets the ball escape through the opening', () => {
    const sim = new SwellSim({ opening: 200, radius: 10 }, createRng(7));
    sim.setShape(presetShape('circle'));
    let escaped = false;
    for (let i = 0; i < 60 * 300 && !escaped; i++) escaped = sim.step(1 / 60).escaped;
    expect(escaped).toBe(true);
    expect(pointInPolygon(sim.ball.x, sim.ball.y, sim.wall)).toBe(false);
  });

  it('only drops the ball inside the shape', () => {
    const sim = new SwellSim({}, createRng(8));
    sim.setShape(presetShape('circle'));
    expect(sim.dropBall({ x: 500, y: 500 })).toBe(true);
    expect(sim.dropBall({ x: 5, y: 5 })).toBe(false);
  });

  it('rejects shapes with too few points', () => {
    expect(() => new SwellSim().setShape([{ x: 0, y: 0 }, { x: 1, y: 1 }])).toThrow();
  });
});

describe('formatClock', () => {
  it('formats minutes and tenths', () => {
    expect(formatClock(0)).toBe('0:00.0');
    expect(formatClock(75.34)).toBe('1:15.3');
  });
});

describe('randomShape', () => {
  it('never returns a thin sliver', async () => {
    const { roominess } = await import('./shapes');
    for (let seed = 1; seed <= 200; seed++) expect(roominess(randomShape(createRng(seed)))).toBeGreaterThanOrEqual(0.3);
  });
});
