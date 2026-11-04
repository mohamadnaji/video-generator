import type { GameMeta } from '@shared/game';

export const meta: GameMeta = {
  id: 'block-push-lab',
  title: 'Block Push Lab',
  description:
    'Two blocks on a frictionless floor. Count the elastic collisions to find the digits of π, or push the small block and see the force it passes on.',
  tags: ['Elastic collisions', 'Forces', 'Friction'],
  order: 20,
  loadPreview: () => import('./preview'),
};
