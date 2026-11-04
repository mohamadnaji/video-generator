/**
 * Short click sounds for collisions. Browsers only allow audio after a user
 * gesture, so call `enable()` from a click handler.
 */
export function createClicker({ frequency = 1800, minGap = 0.025, volume = 0.08 } = {}) {
  let ctx: AudioContext | null = null;
  let enabled = false;
  let last = 0;

  return {
    get enabled() { return enabled; },
    setEnabled(on: boolean) {
      enabled = on;
      if (on && !ctx) {
        try { ctx = new AudioContext(); } catch { enabled = false; }
      }
      return enabled;
    },
    click() {
      if (!enabled || !ctx) return;
      const t = ctx.currentTime;
      if (t - last < minGap) return;
      last = t;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = 'square';
      o.frequency.value = frequency;
      g.gain.setValueAtTime(volume, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.03);
      o.connect(g).connect(ctx.destination);
      o.start(t);
      o.stop(t + 0.04);
    },
  };
}
