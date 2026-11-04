# Physics Playground

Small physics games that run in the browser. The home page lists every game so you can pick one to play.

| Game | What it does |
| --- | --- |
| **Swell Escape** | A ball bounces inside a closed shape with one small opening. Every hit swells the wall at that spot, repeat hits make it grow faster, and the ball keeps going until it gets out. Random shapes, presets, or draw your own. |
| **Block Push Lab** | Two blocks on a floor. Count elastic collisions to get the digits of π, or push the small block and see the force it passes to the big one. |

## Getting started

Requires Node 20 or newer (see `.nvmrc`).

```bash
npm install
npm run dev        # local server with hot reload
```

| Command | What it does |
| --- | --- |
| `npm run dev` | Start the dev server |
| `npm run build` | Type-check, then build the static site into `dist/` |
| `npm run preview` | Serve the built `dist/` locally |
| `npm test` | Run unit tests once (`npm run test:watch` to keep watching) |
| `npm run lint` | Lint all code |
| `npm run check` | Type-check, lint and test (what CI runs, minus the build) |
| `npm run new:game -- <id> "<Title>"` | Create a new game from the template |

## Deploying

`npm run build` produces a plain static site in `dist/`. Asset paths are relative, so it can be served from a domain root or any subfolder, by Nginx or any static host. Copy the contents of `dist/` to the server's web root.

## Project layout

```
src/
  index.html                home page (game picker)
  home/                     home page script and styles
  games/
    registry.ts             finds every game's meta.ts automatically
    swell-escape/
      index.html            the game page
      main.ts               page wiring: buttons, sliders, input, loop
      sim.ts                simulation (pure logic, no DOM)
      shapes.ts             preset and random shapes
      render.ts             canvas drawing
      preview.ts            animated thumbnail for the home page
      meta.ts               title, description, tags, order
      palette.css           the game's colour tokens (also used by its preview)
      styles.css            game page layout
      *.test.ts             unit tests
    block-push-lab/         same structure
  shared/
    game.ts                 GameMeta and Preview contracts
    engine/                 canvas sizing, game loop, theme colours, pointer input, audio
    math/                   vectors, geometry, seeded random numbers
    ui/                     DOM helpers (element lookup, slider binding)
    styles/                 design tokens (light and dark), base styles, components
scripts/new-game.mjs        game scaffold
```

### Rules that keep it maintainable

- **One folder per game.** A game only imports its own files and `@shared/*`, never another game. ESLint enforces this.
- **Simulation is separate from the page.** `sim.ts` (and similar files) never touches the DOM, so it can be unit tested and reused by the home page preview.
- **Games register themselves.** Any `src/games/<id>/` with an `index.html` becomes the page `/games/<id>/`, and its `meta.ts` adds it to the home page. You don't need to edit a central list.
- **Colours come from tokens.** Shared tokens live in `src/shared/styles/tokens.css` with light and dark values. Each game adds its own tokens in `palette.css`, which its home page preview loads too. Canvas code reads them through `themeColors()`, so drawings follow the theme.
- **Code moves to `shared/` once a second game needs it.** Until then, it stays in the game.

## Adding a game

```bash
npm run new:game -- gravity-wells "Gravity Wells"
npm run dev    # open /games/gravity-wells/
```

This creates a working starter game with a test. It already appears on the home page. Then:

1. Write the physics in `sim.ts` and test it in `sim.test.ts`.
2. Draw it in `render.ts` and wire controls in `main.ts` and `index.html`.
3. Fill in `meta.ts` (description, tags, order) and make `preview.ts` show a short loop of the game.
4. Run `npm run check` before committing.
