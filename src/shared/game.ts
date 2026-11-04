/**
 * Contract every game folder exports from meta.ts. The home page discovers these
 * automatically, so adding a folder under src/games is all it takes to list a game.
 */
export interface Preview {
  /** Advance the preview by dt seconds. */
  step(dt: number): void;
  /** Draw into a CSS-pixel canvas of the given size. */
  draw(ctx: CanvasRenderingContext2D, width: number, height: number): void;
}

export interface GameMeta {
  /** Must match the folder name; used in the URL /games/<id>/. */
  id: string;
  title: string;
  /** One or two sentences shown on the home page card. */
  description: string;
  tags: string[];
  /** Lower comes first on the home page. */
  order: number;
  /** Lazily loaded so the home page stays light. */
  loadPreview?: () => Promise<{ createPreview: () => Preview }>;
}
