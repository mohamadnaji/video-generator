# Physics Playground

Vite + TypeScript multi-page site of browser physics games. Read README.md for the layout.

## Conventions

- Each game lives in `src/games/<id>/` and is self-contained: import only its own files and `@shared/*`.
- Keep simulation logic in DOM-free modules (`sim.ts` etc.) with unit tests; `main.ts` only wires the page.
- Every game has `index.html`, `main.ts`, `meta.ts` (with `id` equal to the folder name), and `preview.ts` for the home card.
- New games: `npm run new:game -- <id> "<Title>"`. Don't edit a central game list; `registry.ts` discovers `meta.ts` files.
- Colours: use CSS tokens (light and dark values) and `themeColors()` in canvas code, never hard-coded theme colours.
- Look up elements with `byId()`, which throws on a missing element rather than failing silently.
- Before committing, run `npm run check` and `npx vite build`.
- When adding or changing a game, update its `meta.ts` and the games table in README.md.
