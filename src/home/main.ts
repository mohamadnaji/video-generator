import type { GameMeta, Preview } from '@shared/game';
import { setupCanvas, type CanvasHandle } from '@shared/engine/canvas';
import { createLoop, prefersReducedMotion } from '@shared/engine/loop';
import { byId } from '@shared/ui/dom';
import { gameHref, games } from '../games/registry';

interface LivePreview { view: CanvasHandle; preview: Preview; visible: boolean }

const list = byId('games');
const template = byId<HTMLTemplateElement>('card-template');
const live: LivePreview[] = [];

byId('game-count').textContent = `${games.length} ${games.length === 1 ? 'game' : 'games'}`;

// Only animate previews that are on screen.
const visibility = new IntersectionObserver((entries) => {
  for (const e of entries) {
    const p = live.find((l) => l.view.canvas === e.target);
    if (p) p.visible = e.isIntersecting;
  }
});

function renderCard(game: GameMeta) {
  const node = template.content.firstElementChild!.cloneNode(true) as HTMLAnchorElement;
  node.href = gameHref(game.id);
  node.querySelector('h2')!.textContent = game.title;
  node.querySelector('p')!.textContent = game.description;
  node.querySelector('.play')!.textContent = `Play ${game.title} →`;
  const tags = node.querySelector('.meta')!;
  for (const t of game.tags) {
    const s = document.createElement('span');
    s.textContent = t;
    tags.append(s);
  }
  list.append(node);

  const canvas = node.querySelector('canvas')!;
  // A broken preview must never break the home page; the card still links to the game.
  game.loadPreview?.()
    .then(({ createPreview }) => {
      const entry: LivePreview = { view: setupCanvas(canvas), preview: createPreview(), visible: true };
      live.push(entry);
      visibility.observe(canvas);
      if (prefersReducedMotion()) {
        for (let i = 0; i < 300; i++) entry.preview.step(1 / 60);
        draw(entry);
      }
    })
    .catch((err: unknown) => console.error(`Preview for ${game.id} failed`, err));
}

function draw({ view, preview }: LivePreview) {
  view.beginFrame();
  view.ctx.clearRect(0, 0, view.width, view.height);
  preview.draw(view.ctx, view.width, view.height);
}

games.forEach(renderCard);

if (!prefersReducedMotion()) {
  createLoop({
    maxDt: 0.05,
    update(dt) { for (const p of live) if (p.visible) p.preview.step(dt); },
    render() { for (const p of live) if (p.visible) draw(p); },
  }).start();
}
