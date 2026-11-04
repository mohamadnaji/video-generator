/**
 * Keeps a <canvas> backing store in sync with its CSS size and the device pixel ratio.
 * Drawing code works in CSS pixels (or in a fixed "world" size via `beginFrame(worldWidth)`).
 */
export interface CanvasHandle {
  readonly canvas: HTMLCanvasElement;
  readonly ctx: CanvasRenderingContext2D;
  /** Current CSS width / height in pixels. */
  readonly width: number;
  readonly height: number;
  /**
   * Resets the transform for a new frame. With `worldWidth`, one world unit maps to
   * width / worldWidth CSS pixels, so the scene scales with the canvas.
   */
  beginFrame(worldWidth?: number): void;
  onResize(cb: () => void): () => void;
  dispose(): void;
}

export function setupCanvas(canvas: HTMLCanvasElement): CanvasHandle {
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D context is not available in this browser.');

  let width = 0;
  let height = 0;
  let dpr = 1;
  const listeners = new Set<() => void>();

  const sync = () => {
    dpr = window.devicePixelRatio || 1;
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    canvas.width = Math.max(1, Math.round(width * dpr));
    canvas.height = Math.max(1, Math.round(height * dpr));
    listeners.forEach((cb) => cb());
  };

  const observer = new ResizeObserver(sync);
  observer.observe(canvas);
  sync();

  return {
    canvas,
    ctx,
    get width() { return width; },
    get height() { return height; },
    beginFrame(worldWidth) {
      const s = worldWidth ? (width / worldWidth) * dpr : dpr;
      ctx.setTransform(s, 0, 0, s, 0, 0);
    },
    onResize(cb) {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    dispose() {
      observer.disconnect();
      listeners.clear();
    },
  };
}
