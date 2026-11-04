import type { Vec } from '../math/vec';

/** Converts a pointer event to canvas coordinates, optionally scaled to a world width. */
export function pointerToCanvas(canvas: HTMLCanvasElement, e: PointerEvent, worldWidth?: number): Vec {
  const r = canvas.getBoundingClientRect();
  const sx = worldWidth ? worldWidth / r.width : 1;
  return { x: (e.clientX - r.left) * sx, y: (e.clientY - r.top) * sx };
}

/**
 * Fires `cb` for a tap/click that didn't move more than `slop` CSS pixels,
 * so drags and scrolls on touch screens don't count as taps.
 */
export function onTap(canvas: HTMLCanvasElement, cb: (e: PointerEvent) => void, slop = 10): () => void {
  let down: { x: number; y: number; id: number } | null = null;
  const onDown = (e: PointerEvent) => { down = { x: e.clientX, y: e.clientY, id: e.pointerId }; };
  const onUp = (e: PointerEvent) => {
    if (down && down.id === e.pointerId && Math.hypot(e.clientX - down.x, e.clientY - down.y) <= slop) cb(e);
    down = null;
  };
  canvas.addEventListener('pointerdown', onDown);
  canvas.addEventListener('pointerup', onUp);
  return () => {
    canvas.removeEventListener('pointerdown', onDown);
    canvas.removeEventListener('pointerup', onUp);
  };
}
