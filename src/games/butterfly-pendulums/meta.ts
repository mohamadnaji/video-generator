import type { GameMeta } from '@shared/game';

export const meta: GameMeta = {
  id: 'butterfly-pendulums',
  title: 'Butterfly Pendulums',
  description:
    'Hundreds of double pendulums start a tiny fraction of a degree apart. They swing as one, then suddenly explode into a rainbow of chaos: the butterfly effect.',
  tags: ['Chaos', 'Butterfly effect', 'Pendulums'],
  order: 30,
  loadPreview: () => import('./preview'),
};
