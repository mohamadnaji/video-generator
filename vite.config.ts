import { readdirSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig } from 'vitest/config';

const root = resolve(import.meta.dirname, 'src');
const gamesDir = resolve(root, 'games');

/** Every folder in src/games with an index.html becomes its own page: /games/<id>/ */
function gamePages(): Record<string, string> {
  const pages: Record<string, string> = {};
  for (const entry of readdirSync(gamesDir, { withFileTypes: true })) {
    const html = resolve(gamesDir, entry.name, 'index.html');
    if (entry.isDirectory() && existsSync(html)) pages[entry.name] = html;
  }
  return pages;
}

export default defineConfig({
  root,
  // Relative base so the built site works from any folder (Nginx subpath, GitHub Pages, file server).
  base: './',
  publicDir: resolve(import.meta.dirname, 'public'),
  resolve: { alias: { '@shared': resolve(root, 'shared') } },
  build: {
    outDir: resolve(import.meta.dirname, 'dist'),
    emptyOutDir: true,
    rollupOptions: { input: { home: resolve(root, 'index.html'), ...gamePages() } },
  },
  test: {
    root: import.meta.dirname,
    include: ['src/**/*.test.ts', 'scripts/**/*.test.ts'],
    environment: 'node',
  },
});
