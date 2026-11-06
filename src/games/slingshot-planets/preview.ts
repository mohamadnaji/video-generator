import './palette.css';
import type { Preview } from '@shared/game';
import { themeColors } from '@shared/engine/theme';
import { COLOR_TOKENS, draw } from './render';
import { createWorld, DEFAULT_PARAMS, spray, step } from './sim';

/** Home page card: a spray of moons around a star, renewed every few seconds. */
export function createPreview(): Preview {
  const theme = themeColors(COLOR_TOKENS);
  const p = { ...DEFAULT_PARAMS, giant: true };
  const w = createWorld();
  let next = 0;
  return {
    step(dt) {
      next -= dt;
      if (next <= 0) { spray(w, p, 6); next = 4; }
      step(w, p, dt);
    },
    draw: (ctx, width, height) => draw(ctx, width, height, p, w, theme.colors, null),
  };
}
