# Physics Playground

Small physics games that run in the browser. The home page (`index.html`) lists every game so you can pick one to play.

## Games

### Swell Escape — `games/swell-escape/`

A ball bounces inside a closed shape that has one small opening. Each bounce reflects at the correct angle. Every hit makes the wall swell at that spot, and repeat hits on the same area make the swelling grow faster, until the ball gets out. The wall never folds or crosses itself.

- Make a random shape, draw your own closed loop, or pick a preset (circle, square, hexagon, star, heart).
- Tap the wall to move the opening. Tap inside the shape to drop the ball there.
- Sliders for ball speed, swelling per hit, growth on repeat hits, swelling width, opening width, and ball size.

### Block Push Lab — `games/block-push-lab/`

An interactive physics simulator of two blocks in contact, one light and one heavy.

**Collision counter**: a heavy block slides into a small block near a wall, on a frictionless floor with perfectly elastic collisions. The page counts every hit. With a mass ratio of 100^n, the total count gives the first digits of π (3, 31, 314, 3141, 31415).

**Steady push**: you push the small block, and it pushes the big one. The page shows:
- the force needed to get both moving: `F ≥ μ·g·(m + M)`
- the contact force passed to the big block: `F × M ÷ (m + M)`
- the resulting acceleration: `F ÷ (m + M) − μ·g`

## Run

There's no build step. Open `index.html` in a browser, or serve the folder:

```bash
npx serve .
```

## Adding a game

1. Create `games/<game-name>/index.html` as a self-contained page.
2. Add a link at the top back to the home page: `<a href="../../index.html">← All games</a>`.
3. Add a card for it in the root `index.html` and update the game count.
