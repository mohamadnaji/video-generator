import './palette.css';
import type { Preview } from '@shared/game';
import { themeColors } from '@shared/engine/theme';
import { COLOR_TOKENS, draw } from './render';
import { createBoard, DEFAULT_PARAMS, finished, step } from './sim';

/** Home page card: a fast 400-marble run building its bell curve, on repeat. */
export function createPreview(): Preview {
  const theme = themeColors(COLOR_TOKENS);
  const p = { ...DEFAULT_PARAMS, rows: 10, total: 400, rate: 80 };
  let b = createBoard(p.rows);
  let pause = 0;
  return {
    step(dt) {
      if (finished(b, p)) { pause += dt; if (pause > 1.5) { b = createBoard(p.rows); pause = 0; } return; }
      step(b, p, dt * 1.5);
    },
    draw: (ctx, w, h) => draw(ctx, w, h, b, theme.colors, { curve: true }),
  };
}
