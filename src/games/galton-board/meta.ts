import type { GameMeta } from '@shared/game';

export const meta: GameMeta = {
  id: 'galton-board',
  title: 'Marble Galton Board',
  description:
    'A thousand marbles bounce randomly through pegs, yet they always pile up into the same bell curve. Tilt the board or turn on the wind and watch the curve slide.',
  tags: ['Probability', 'Bell curve', 'Collisions'],
  order: 40,
  loadPreview: () => import('./preview'),
};
