import { describe, expect, it } from 'vitest';
import { createCollision, elasticVelocities, stepCollision } from './collision';

function runToEnd(exponent: number) {
  const c = createCollision(exponent, 800);
  for (let i = 0; i < 100_000 && !c.done; i++) stepCollision(c, 0.05);
  return c;
}

describe('collision counter', () => {
  it.each([
    [0, 3],
    [1, 31],
    [2, 314],
    [3, 3141],
  ])('mass ratio 100^%i gives %i collisions (digits of π)', (n, expected) => {
    expect(runToEnd(n).count).toBe(expected);
  });

  it('conserves momentum and kinetic energy in a block collision', () => {
    const m = 1, M = 100, u1 = 0.3, u2 = -1;
    const [v1, v2] = elasticVelocities(m, M, u1, u2);
    expect(m * v1 + M * v2).toBeCloseTo(m * u1 + M * u2, 10);
    expect(m * v1 ** 2 + M * v2 ** 2).toBeCloseTo(m * u1 ** 2 + M * u2 ** 2, 10);
  });
});
