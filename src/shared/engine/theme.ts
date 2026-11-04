/**
 * Canvas code can't use CSS variables directly, so this reads the theme tokens
 * from :root and re-reads them whenever the light/dark theme changes.
 */
export type Rgb = readonly [number, number, number];

export function readTokens<K extends string>(names: readonly K[]): Record<K, string> {
  const cs = getComputedStyle(document.documentElement);
  const out = {} as Record<K, string>;
  for (const n of names) out[n] = cs.getPropertyValue(`--${n}`).trim();
  return out;
}

/** Calls `cb` when the OS colour scheme or the page's data-theme attribute changes. */
export function watchTheme(cb: () => void): () => void {
  const mq = matchMedia('(prefers-color-scheme: dark)');
  mq.addEventListener('change', cb);
  const mo = new MutationObserver(cb);
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  return () => {
    mq.removeEventListener('change', cb);
    mo.disconnect();
  };
}

/** Reactive token set: `theme.colors` always holds the current values. */
export function themeColors<K extends string>(names: readonly K[]) {
  const state = { colors: readTokens(names) };
  watchTheme(() => { state.colors = readTokens(names); });
  return state;
}

/** Parses #rgb, #rrggbb, rgb(r g b) and rgb(r, g, b). Unknown input returns black. */
export function toRgb(color: string): Rgb {
  const c = color.trim();
  const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(c);
  if (hex?.[1]) {
    const h = hex[1].length === 3 ? [...hex[1]].map((ch) => ch + ch).join('') : hex[1];
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  const fn = /^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/i.exec(c);
  if (fn) return [Number(fn[1]), Number(fn[2]), Number(fn[3])];
  return [0, 0, 0];
}

export const rgba = ([r, g, b]: Rgb, a = 1): string => `rgb(${r} ${g} ${b} / ${a})`;

export function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
  const k = Math.min(1, Math.max(0, t));
  return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k].map(Math.round) as unknown as Rgb;
}
