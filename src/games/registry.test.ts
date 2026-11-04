import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { games, validateGames } from './registry';

describe('game registry', () => {
  it('finds every game, sorted by order', () => {
    const ids = games.map((g) => g.id);
    expect(ids).toEqual(expect.arrayContaining(['swell-escape', 'block-push-lab']));
    const orders = games.map((g) => g.order);
    expect(orders).toEqual([...orders].sort((a, b) => a - b));
  });

  it('has a page and a preview for every game', () => {
    for (const g of games) {
      expect(existsSync(resolve(import.meta.dirname, g.id, 'index.html')), `${g.id}/index.html`).toBe(true);
      expect(g.title && g.description && g.tags.length, g.id).toBeTruthy();
    }
  });

  it('rejects an id that does not match its folder', () => {
    const meta = { id: 'wrong', title: 'X', description: 'X', tags: [], order: 0 };
    expect(() => validateGames({ './right/meta.ts': { meta } })).toThrow(/must match/);
  });
});
