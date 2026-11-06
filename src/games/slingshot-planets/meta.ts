import type { GameMeta } from '@shared/game';

export const meta: GameMeta = {
  id: 'slingshot-planets',
  title: 'Slingshot Planets',
  description:
    'Drag to launch moons around a star. Too slow and they crash, too fast and they fly off into space. Find the speed that locks one into orbit.',
  tags: ['Gravity', 'Orbits', 'Escape speed'],
  order: 50,
  loadPreview: () => import('./preview'),
};
