import { describe, expect, it } from 'vitest';
import { createWorld, DEFAULT_PARAMS, launch, orbitSpeeds, predict, spray, step } from './sim';

const run = (w: ReturnType<typeof createWorld>, seconds: number, p = DEFAULT_PARAMS) => {
  for (let i = 0; i < seconds * 60; i++) step(w, p, 1 / 60);
};

describe('Slingshot Planets', () => {
  it('a moon at exactly circular speed locks into orbit and keeps its radius', () => {
    const w = createWorld(1);
    const r = 220;
    const { circular } = orbitSpeeds(DEFAULT_PARAMS, r);
    const m = launch(w, 0, -r, -circular, 0);
    run(w, 30);
    expect(m.status).toBe('orbit');
    expect(Math.abs(Math.hypot(m.x, m.y) - r)).toBeLessThan(3);
  });

  it('a slow moon falls into the star', () => {
    const w = createWorld(1);
    launch(w, 0, -220, -20, 0);
    run(w, 10);
    expect(w.crashed).toBe(1);
    expect(w.bursts.length + w.crashed).toBeGreaterThan(0);
  });

  it('a moon faster than escape speed leaves for good', () => {
    const w = createWorld(1);
    const { escape } = orbitSpeeds(DEFAULT_PARAMS, 220);
    launch(w, 0, -220, -escape * 1.1, 0);
    run(w, 30);
    expect(w.escaped).toBe(1);
  });

  it('prediction agrees with the real outcome', () => {
    const w = createWorld(1);
    const { circular } = orbitSpeeds(DEFAULT_PARAMS, 220);
    expect(predict(w, DEFAULT_PARAMS, 0, -220, -circular, 0, 8).end).toBe('orbit');
    expect(predict(w, DEFAULT_PARAMS, 0, -220, -20, 0, 8).end).toBe('crashed');
  });

  it('a random spray mostly fails', () => {
    const w = createWorld(3);
    spray(w, DEFAULT_PARAMS, 30);
    run(w, 40);
    expect(w.crashed + w.escaped).toBeGreaterThan(w.locked);
  });
});
