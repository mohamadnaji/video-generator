import { describe, expect, it } from 'vitest';
import { G, pushForces, pushStatus, stepPush } from './push';

describe('steady push', () => {
  const base = { m: 2, M: 20, mu: 0.2 };
  const Fmin = 0.2 * G * 22;

  it('needs F ≥ μ·g·(m + M) to start moving', () => {
    const below = pushForces({ ...base, F: Fmin - 1 }, 0);
    expect(below.Fmin).toBeCloseTo(Fmin);
    expect(below.moving).toBe(false);
    expect(pushStatus(below, 0)).toBe('stuck');
    expect(pushForces({ ...base, F: Fmin + 1 }, 0).moving).toBe(true);
  });

  it('passes F × M ÷ (m + M) to the big block while moving', () => {
    const f = pushForces({ ...base, F: 100 }, 0);
    expect(f.N).toBeCloseTo((100 * 20) / 22);
    expect(f.a).toBeCloseTo(100 / 22 - 0.2 * G);
  });

  it('speeds up under a strong push and slows to a stop without one', () => {
    const s = { x: 0, v: 0 };
    for (let i = 0; i < 60; i++) stepPush(s, { ...base, F: 200 }, 1 / 60);
    expect(s.v).toBeGreaterThan(0);
    for (let i = 0; i < 60 * 30; i++) stepPush(s, { ...base, F: 0 }, 1 / 60);
    expect(s.v).toBe(0);
  });
});
