import { byId } from './dom';

/**
 * Wires a button that switches the stage to a 9:16 frame for recording vertical reels.
 * Canvas code should draw from the canvas's current width and height, not a fixed size.
 */
export function bindReelToggle(buttonId = 'reel-btn'): void {
  const btn = byId(buttonId);
  const sync = () => {
    const on = document.body.classList.contains('reel');
    btn.setAttribute('aria-pressed', String(on));
    btn.textContent = on ? 'Reel 9:16 on' : 'Reel 9:16';
  };
  btn.addEventListener('click', () => { document.body.classList.toggle('reel'); sync(); });
  sync();
}
