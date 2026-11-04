#!/usr/bin/env node
/**
 * Creates a new game folder with everything the project expects:
 *   npm run new:game -- <id> "<Title>"
 * e.g. npm run new:game -- gravity-wells "Gravity Wells"
 *
 * The game shows up on the home page automatically (it's discovered from meta.ts).
 */
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const gamesDir = resolve(root, 'src/games');
const [id, ...titleParts] = process.argv.slice(2);
const title = titleParts.join(' ').trim();

function fail(msg) {
  console.error(`\n  ${msg}\n\n  Usage: npm run new:game -- <id> "<Title>"\n  Example: npm run new:game -- gravity-wells "Gravity Wells"\n`);
  process.exit(1);
}

if (!id || !/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/.test(id)) fail('The id must be lowercase words joined by hyphens, like "gravity-wells".');
if (!title) fail('Give the game a title.');
const dir = resolve(gamesDir, id);
if (existsSync(dir)) fail(`src/games/${id} already exists.`);

// Put the new game after the existing ones on the home page.
const orders = readdirSync(gamesDir, { withFileTypes: true })
  .filter((d) => d.isDirectory() && existsSync(resolve(gamesDir, d.name, 'meta.ts')))
  .map((d) => Number(/order:\s*(\d+)/.exec(readFileSync(resolve(gamesDir, d.name, 'meta.ts'), 'utf8'))?.[1] ?? 0));
const order = Math.max(0, ...orders) + 10;
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
const str = (s) => JSON.stringify(s);

const files = {
  'index.html': `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>${esc(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
  <link rel="stylesheet" href="../../shared/styles/base.css">
  <link rel="stylesheet" href="../../shared/styles/components.css">
  <link rel="stylesheet" href="./styles.css">
</head>
<body>
  <main class="page">
    <header class="page-header">
      <a class="back-link" href="../../">&larr; All games</a>
      <h1>${esc(title)}</h1>
      <p>Describe what happens in this game.</p>
    </header>
    <canvas id="stage-canvas" class="stage-canvas" aria-label="Simulation area"></canvas>
    <div class="panel btn-row">
      <button class="btn" id="play-btn" type="button">Pause</button>
      <button class="btn" id="reset-btn" type="button">Reset</button>
    </div>
  </main>
  <script type="module" src="./main.ts"></script>
</body>
</html>
`,
  'palette.css': `/* Colour tokens for ${title}. Loaded by the game page and by its home page preview. */
:root { --ball: #2f56cf; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --ball: #7e9dff; } }
:root[data-theme="dark"] { --ball: #7e9dff; }
`,
  'styles.css': `/* ${title}: page layout. Shared styles live in src/shared/styles. */
@import "./palette.css";

#stage-canvas { aspect-ratio: 16 / 9; }
`,
  'sim.ts': `/**
 * ${title} simulation. Keep this file free of DOM and drawing code so it can be
 * unit tested and reused by the home page preview.
 */
export const WIDTH = 1600;
export const HEIGHT = 900;

export interface State { x: number; y: number; vx: number; vy: number; r: number }

export function createState(): State {
  return { x: WIDTH / 2, y: HEIGHT / 2, vx: 420, vy: 300, r: 30 };
}

/** Advances the state by dt seconds. */
export function step(s: State, dt: number): void {
  s.x += s.vx * dt;
  s.y += s.vy * dt;
  if (s.x < s.r || s.x > WIDTH - s.r) { s.vx = -s.vx; s.x = Math.min(WIDTH - s.r, Math.max(s.r, s.x)); }
  if (s.y < s.r || s.y > HEIGHT - s.r) { s.vy = -s.vy; s.y = Math.min(HEIGHT - s.r, Math.max(s.r, s.y)); }
}
`,
  'render.ts': `import { HEIGHT, WIDTH, type State } from './sim';

export const COLOR_TOKENS = ['field', 'ball'] as const;
export type Colors = Record<(typeof COLOR_TOKENS)[number], string>;

/** Draws in world units (WIDTH x HEIGHT); scale the context to the canvas first. */
export function draw(ctx: CanvasRenderingContext2D, s: State, colors: Colors): void {
  ctx.fillStyle = colors.field;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.fillStyle = colors.ball;
  ctx.beginPath();
  ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
  ctx.fill();
}
`,
  'main.ts': `import { setupCanvas } from '@shared/engine/canvas';
import { createLoop } from '@shared/engine/loop';
import { themeColors } from '@shared/engine/theme';
import { byId } from '@shared/ui/dom';
import { COLOR_TOKENS, draw } from './render';
import { createState, step, WIDTH } from './sim';

const view = setupCanvas(byId<HTMLCanvasElement>('stage-canvas'));
const theme = themeColors(COLOR_TOKENS);
let state = createState();

const loop = createLoop({
  update: (dt) => step(state, dt),
  render() {
    view.beginFrame(WIDTH);
    draw(view.ctx, state, theme.colors);
  },
});

const playBtn = byId('play-btn');
playBtn.addEventListener('click', () => { playBtn.textContent = loop.togglePaused() ? 'Play' : 'Pause'; });
byId('reset-btn').addEventListener('click', () => { state = createState(); });

loop.start();
`,
  'preview.ts': `import './palette.css';
import type { Preview } from '@shared/game';
import { themeColors } from '@shared/engine/theme';
import { COLOR_TOKENS, draw } from './render';
import { createState, HEIGHT, step, WIDTH } from './sim';

/** Small looping version of the game for the home page card. */
export function createPreview(): Preview {
  const theme = themeColors(COLOR_TOKENS);
  const state = createState();
  return {
    step: (dt) => step(state, dt),
    draw(ctx, width, height) {
      const s = Math.min(width / WIDTH, height / HEIGHT);
      ctx.save();
      ctx.translate((width - WIDTH * s) / 2, (height - HEIGHT * s) / 2);
      ctx.scale(s, s);
      draw(ctx, state, theme.colors);
      ctx.restore();
    },
  };
}
`,
  'meta.ts': `import type { GameMeta } from '@shared/game';

export const meta: GameMeta = {
  id: ${str(id)},
  title: ${str(title)},
  description: 'One or two sentences for the home page card.',
  tags: ['Tag one', 'Tag two'],
  order: ${order},
  loadPreview: () => import('./preview'),
};
`,
  'sim.test.ts': `import { describe, expect, it } from 'vitest';
import { createState, HEIGHT, step, WIDTH } from './sim';

describe(${str(title)}, () => {
  it('keeps the ball inside the play area', () => {
    const s = createState();
    for (let i = 0; i < 600; i++) step(s, 1 / 60);
    expect(s.x).toBeGreaterThanOrEqual(s.r);
    expect(s.x).toBeLessThanOrEqual(WIDTH - s.r);
    expect(s.y).toBeGreaterThanOrEqual(s.r);
    expect(s.y).toBeLessThanOrEqual(HEIGHT - s.r);
  });
});
`,
};

mkdirSync(dir, { recursive: true });
for (const [name, content] of Object.entries(files)) writeFileSync(resolve(dir, name), content);

console.log(`\n  Created src/games/${id}/ (${Object.keys(files).length} files).`);
console.log(`  It's listed on the home page already. Run \`npm run dev\` and open /games/${id}/.`);
console.log(`  Next: edit sim.ts (logic), render.ts (drawing), meta.ts (home page card).\n`);
