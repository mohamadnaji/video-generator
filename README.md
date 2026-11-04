# Block Push Lab

An interactive physics simulator of two blocks in contact, one light and one heavy.

## Modes

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
