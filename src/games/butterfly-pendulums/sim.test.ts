import { describe, expect, it } from 'vitest';
import { createSwarm, DEFAULT_PARAMS, energy, spread, step, type Params } from './sim';

describe('Butterfly Pendulums', () => {
  it('keeps a single pendulum period close to 2π√(L/g) for small swings', () => {
    const p: Params = { ...DEFAULT_PARAMS, arms: 1 };
    const s = createSwarm(1, 5, 0);
    let t = 0, crossings = 0, prev = s.th1[0]!, firstCross = 0, lastCross = 0;
    while (crossings < 5) {
      step(p, s, 1 / 240); t += 1 / 240;
      const cur = s.th1[0]!;
      if (prev > 0 && cur <= 0) { crossings++; if (crossings === 1) firstCross = t; lastCross = t; }
      prev = cur;
    }
    const period = (lastCross - firstCross) / 4;
    expect(period).toBeCloseTo(2 * Math.PI * Math.sqrt(1 / 9.81), 1);
  });

  it('conserves energy for a wild double pendulum', () => {
    const s = createSwarm(1, 150, 0);
    const e0 = energy(DEFAULT_PARAMS, s, 0);
    for (let i = 0; i < 60 * 10; i++) step(DEFAULT_PARAMS, s, 1 / 60);
    expect(Math.abs(energy(DEFAULT_PARAMS, s, 0) - e0)).toBeLessThan(0.01 * Math.abs(e0) + 0.05);
  });

  it('nearly identical double pendulums stay together, then split apart', () => {
    const s = createSwarm(20, 120, 1e-4);
    expect(spread(DEFAULT_PARAMS, s)).toBeLessThan(1e-4);
    for (let i = 0; i < 60; i++) step(DEFAULT_PARAMS, s, 1 / 60);
    expect(spread(DEFAULT_PARAMS, s)).toBeLessThan(0.01);
    for (let i = 0; i < 60 * 30 && s.splitAt === null; i++) step(DEFAULT_PARAMS, s, 1 / 60);
    expect(s.splitAt).not.toBeNull();
  });

  it('simple pendulums with the same offsets stay predictable', () => {
    const p: Params = { ...DEFAULT_PARAMS, arms: 1 };
    const s = createSwarm(20, 60, 1e-3);
    for (let i = 0; i < 60 * 20; i++) step(p, s, 1 / 60);
    expect(s.splitAt).toBeNull();
  });
});
