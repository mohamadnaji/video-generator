/** Looks up an element by id and fails loudly if the HTML and code drift apart. */
export function byId<T extends HTMLElement = HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el as T;
}

export interface RangeBinding {
  readonly value: number;
  set(value: number): void;
}

/**
 * Wires an <input type=range> to its <output>. `format` renders the shown value;
 * `onInput` runs on every change. The output is filled immediately.
 */
export function bindRange(
  id: string,
  { format = String, onInput, outputId = `${id}-out` }: { format?: (v: number) => string; onInput?: (v: number) => void; outputId?: string } = {},
): RangeBinding {
  const input = byId<HTMLInputElement>(id);
  const output = document.getElementById(outputId);
  const show = () => { if (output) output.textContent = format(input.valueAsNumber); };
  input.addEventListener('input', () => { show(); onInput?.(input.valueAsNumber); });
  show();
  return {
    get value() { return input.valueAsNumber; },
    set(v) { input.value = String(v); show(); },
  };
}

export function setText(id: string, text: string): void {
  byId(id).textContent = text;
}
