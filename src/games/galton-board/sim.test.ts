import { describe, expect, it } from 'vitest';
import { createBoard, DEFAULT_PARAMS, finished, stats, step, type Params } from './sim';

function run(p: Params, seed = 7) {
  const b = createBoard(p.rows, seed);
  for (let i = 0; i < 60 * 300 && !finished(b, p); i++) step(b, p, 1 / 60);
  return b;
}

describe('Marble Galton Board', () => {
  it('lands every marble it releases', () => {
    const p = { ...DEFAULT_PARAMS, total: 300, rate: 200 };
    const b = run(p);
    expect(finished(b, p)).toBe(true);
    expect(b.counts.reduce((a, c) => a + c, 0)).toBe(300);
  });

  it('piles marbles into a centred bell shape on a level board', () => {
    const p = { ...DEFAULT_PARAMS, total: 600, rate: 300 };
    const b = run(p);
    const { mean, sd } = stats(b);
    expect(Math.abs(mean)).toBeLessThan(0.6);
    expect(sd).toBeGreaterThan(0.6);
    expect(sd).toBeLessThan(4);
    const centre = Math.floor(b.bins / 2);
    expect(b.counts[centre]!).toBeGreaterThan(b.counts[0]! + b.counts[b.bins - 1]!);
  });

  it('shifts the pile when the board is tilted or the wind blows', () => {
    const tilted = stats(run({ ...DEFAULT_PARAMS, total: 400, rate: 300, tiltDeg: 6 })).mean;
    const windy = stats(run({ ...DEFAULT_PARAMS, total: 400, rate: 300, wind: -0.1 })).mean;
    expect(tilted).toBeGreaterThan(0.8);
    expect(windy).toBeLessThan(-0.8);
  });
});
