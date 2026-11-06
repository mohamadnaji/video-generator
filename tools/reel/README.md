# Physics reel kit

Turns a game from `src/games/` into a short vertical reel (1080×1920, 30 fps, 30–45 s) hosted by **Prof. Bounce**, with kokoro voices, karaoke captions, procedural music and sound effects. Voice and audio come from the story kit in `tools/story/storykit`, so both kits share one voice model.

```
tools/reel/
  setup.sh                 # light Python deps + kokoro model (shared with tools/story/models)
  reelkit/
    theme.py               # visual themes (add a new one per reel instead of hard-coding colours)
    draw.py                # fonts, easing, chips, karaoke captions
    host.py                # Prof. Bounce (2D, lip-synced, faces: happy smug shock worried facepalm think)
    reel.py                # timeline, contact sheet, video render (voice + music + sfx mix)
    sims/                  # Python ports of each game's sim.ts, used for every narrated number
      slingshot.py         # Slingshot Planets
  reels/<name>/story.py    # one folder per reel; out/ is generated (gitignored)
```

## Commands (run in tools/reel)

```
bash setup.sh                                   # first time on a machine
python -m reelkit.sims.slingshot                # print crash / escape thresholds from the sim
python reels/<name>/story.py voice              # speak lines, print scene lengths
python reels/<name>/story.py sheet [secs…]      # contact sheet -> reels/<name>/out/sheet.png
python reels/<name>/story.py video              # final mp4 -> reels/<name>/out/<name>.mp4
```

Edited lines are the only ones re-spoken (voice files are cached in `out/voice/`).

## Making a new reel

1. `cp -r reels/one-moon-left reels/<name>` (skip `out/`).
2. Edit only what the story needs: `NAME`, theme, the experiment at the top (launches, speeds), `STORY` scenes and lines, `SFX`, `sim_time()` (how scene time maps to sim time: freeze, slow motion, rewind), `HEADERS`, `draw()` overlays and `host()` faces.
3. If the game has no port in `reelkit/sims/`, port its `sim.ts` with the same formulas and constants first.

### story.py contract

| name | meaning |
| --- | --- |
| `STORY` | `{voices, music_level, scenes:[{id, music, lead, tail, min_dur, lines:[{id, by: host/narrator, text, caption, gap, speed}]}]}`; music moods: `calm upbeat hype happy tense mystery sad dread none` |
| `SFX` | `(scene_id, at, name[, gain])`; `at` is seconds or a line ref like `"b.end+0.2"`; names: `whoosh boom pop ding fanfare trombone drumroll scratch heartbeat rise deflate crowd` |
| `draw(img, scene_id, lt, ctx)` | paints the frame; captions and the host are drawn on top afterwards |
| `host(scene_id, lt, ctx)` | `None` (hidden) or `{x, y (feet), size, face, look}` |

Keep the host in the bottom-left corner, captions at `caption_y` (≈1545) and the stage above ≈1440 so nothing overlaps; check the sheet before rendering.
