import './palette.css';
import type { Preview } from '@shared/game';
import { themeColors } from '@shared/engine/theme';
import { collisionFinished, createCollision, stepCollision, type CollisionState } from './collision';
import { COLOR_TOKENS, drawCollision, FLOOR_Y } from './render';

/** Home page card: the real collision counter at a 1 : 100 mass ratio (31 hits), on repeat. */
export function createPreview(): Preview {
  const theme = themeColors(COLOR_TOKENS);
  const WIDTH = 520;
  let c: CollisionState = createCollision(1, WIDTH);
  let pause = 0;

  return {
    step(dt) {
      if (collisionFinished(c, WIDTH)) {
        pause += dt;
        if (pause > 0.8) { c = createCollision(1, WIDTH); pause = 0; }
        return;
      }
      stepCollision(c, dt * 1.6);
    },
    draw(ctx, width, height) {
      // Fit the 520-wide scene (floor at y=200) into the card.
      const s = Math.min(width / WIDTH, height / (FLOOR_Y + 50));
      ctx.save();
      ctx.translate((width - WIDTH * s) / 2, (height - (FLOOR_Y + 50) * s) / 2 + 10 * s);
      ctx.scale(s, s);
      drawCollision(ctx, WIDTH, FLOOR_Y + 50, c, `collisions ${c.count}`, theme.colors);
      ctx.restore();
    },
  };
}
