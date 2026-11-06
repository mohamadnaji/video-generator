import './palette.css';
import type { Preview } from '@shared/game';
import { themeColors } from '@shared/engine/theme';
import { COLOR_TOKENS, createTrails, draw, recordTrails } from './render';
import { createSwarm, DEFAULT_PARAMS, step } from './sim';

/** Home page card: 120 double pendulums 0.001° apart, peeling into chaos, on repeat. */
export function createPreview(): Preview {
  const theme = themeColors(COLOR_TOKENS);
  const make = () => createSwarm(120, 135, 1e-3);
  let s = make();
  let tr = createTrails(120, 10);
  return {
    step(dt) {
      step(DEFAULT_PARAMS, s, dt);
      recordTrails(tr, DEFAULT_PARAMS, s);
      if (s.t > 16) { s = make(); tr = createTrails(120, 10); }
    },
    draw: (ctx, w, h) => draw(ctx, w, h, DEFAULT_PARAMS, s, tr, theme.colors),
  };
}
