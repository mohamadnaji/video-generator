/**
 * requestAnimationFrame loop with a clamped time step and pause support.
 * `update` gets seconds since the last frame (clamped, so a background tab
 * doesn't produce one giant step). `render` runs every frame, paused or not.
 */
export interface LoopOptions {
  update?: (dt: number) => void;
  render: () => void;
  /** Largest dt passed to update, in seconds. */
  maxDt?: number;
  startPaused?: boolean;
}

export interface Loop {
  start(): void;
  stop(): void;
  readonly paused: boolean;
  setPaused(paused: boolean): void;
  togglePaused(): boolean;
}

export function createLoop({ update, render, maxDt = 1 / 30, startPaused = false }: LoopOptions): Loop {
  let raf = 0;
  let last = 0;
  let paused = startPaused;

  const frame = (now: number) => {
    const dt = Math.min(maxDt, Math.max(0, (now - last) / 1000));
    last = now;
    if (!paused && update) update(dt);
    render();
    raf = requestAnimationFrame(frame);
  };

  return {
    start() {
      if (raf) return;
      last = performance.now();
      raf = requestAnimationFrame(frame);
    },
    stop() {
      cancelAnimationFrame(raf);
      raf = 0;
    },
    get paused() { return paused; },
    setPaused(p) { paused = p; },
    togglePaused() { paused = !paused; return paused; },
  };
}

export const prefersReducedMotion = (): boolean =>
  typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
