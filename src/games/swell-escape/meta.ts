import type { GameMeta } from '@shared/game';

export const meta: GameMeta = {
  id: 'swell-escape',
  title: 'Swell Escape',
  description:
    'A ball bounces inside a closed shape with one small opening. Each hit swells the wall at that spot, and repeat hits make it grow, until the ball gets out.',
  tags: ['Reflection', 'Random shapes', 'Draw your own'],
  order: 10,
  loadPreview: () => import('./preview'),
};
