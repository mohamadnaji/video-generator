import './palette.css';
import type { Preview } from '@shared/game';
import { themeColors } from '@shared/engine/theme';
import { createRng } from '@shared/math/random';
import { COLOR_TOKENS, createEffects, drawScene, updateEffects } from './render';
import { randomShape } from './shapes';
import { POINTS, SwellSim, WORLD } from './sim';

const MAX_RUN = 45;

/** Home page card: the real simulation, zoomed into a 16:9 window, restarting after each escape. */
export function createPreview(): Preview {
  const rng = createRng();
  const sim = new SwellSim({ speed: 420, swell: 9, growth: 0.5, radius: 16, opening: 80 }, rng);
  const fx = createEffects();
  const theme = themeColors(COLOR_TOKENS);
  const reset = () => { sim.setShape(randomShape(rng), rng.int(0, POINTS)); fx.trail = []; fx.ripples = []; };
  reset();

  return {
    step(dt) {
      // Start over once the ball is gone, or if a run drags on.
      if (sim.offscreen || sim.elapsed > MAX_RUN) { reset(); return; }
      const ev = sim.step(dt);
      updateEffects(fx, sim, dt, ev.bounces);
    },
    draw(ctx, width, height) {
      // Fit the whole shape (640 units plus room to swell) into the card.
      const s = Math.min(width / WORLD, height / 760);
      ctx.save();
      ctx.translate(width / 2, height / 2);
      ctx.scale(s, s);
      ctx.translate(-WORLD / 2, -WORLD / 2);
      drawScene(ctx, sim, theme.colors, fx, { wallWidth: 8 });
      ctx.restore();
    },
  };
}
