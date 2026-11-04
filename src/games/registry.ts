/**
 * Every game folder exports `meta` from meta.ts. Vite finds them at build time,
 * so a new folder shows up on the home page with no edits here.
 */
import type { GameMeta } from '@shared/game';

const modules = import.meta.glob<{ meta: GameMeta }>('./*/meta.ts', { eager: true });

export function validateGames(entries: Record<string, { meta: GameMeta }>): GameMeta[] {
  const seen = new Set<string>();
  const games = Object.entries(entries).map(([path, mod]) => {
    const folder = /^\.\/([^/]+)\/meta\.ts$/.exec(path)?.[1];
    const m = mod.meta;
    if (!m) throw new Error(`${path} must export \`meta\``);
    if (m.id !== folder) throw new Error(`${path}: meta.id "${m.id}" must match its folder name "${folder}"`);
    if (seen.has(m.id)) throw new Error(`Duplicate game id "${m.id}"`);
    seen.add(m.id);
    return m;
  });
  return games.sort((a, b) => a.order - b.order || a.title.localeCompare(b.title));
}

export const games: GameMeta[] = validateGames(modules);

/** Link to a game page, relative to the home page. */
export const gameHref = (id: string): string => `games/${id}/`;
