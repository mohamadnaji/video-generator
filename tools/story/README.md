# Story video kit

Turns a `story.json` into a vertical 1080×1920 3D comedy/explainer short hosted by **Ollie**, the recurring avatar: Blender (Cycles, CPU) renders the sets, Ollie's poses and the props once; Python animates camera, lip sync, captions, overlays; kokoro TTS speaks; procedural music + SFX are mixed under the voices.

```
tools/story/
  setup.sh              # pip deps + kokoro voice model -> models/
  storykit/             # the kit (don't fork per video: extend it)
    host.py             # Ollie: look, POSES, FACES, worn PROPS
    props.py            # 3D objects (@prop builders)
    sets.py             # 3D worlds (@setfn builders): studio park city room desert space void
    render3d.py         # cached Blender renders (bump VERSION after changing a builder)
    voice.py audio.py compose.py make.py
  stories/<name>/story.json   # one folder per video; out/ is generated (gitignored)
  cache/                # rendered 3D sprites/plates, shared by all stories (gitignored)
```

## Commands (run in tools/story)

```
bash setup.sh                                          # first time on a machine
python -m storykit.make stories/<name> voice           # speak lines, print scene lengths
python -m storykit.make stories/<name> sheet [secs…]   # render missing 3D + contact sheet -> out/sheet.png
python -m storykit.make stories/<name> video           # final mp4 -> out/<name>.mp4
```

Edit a line → only that line is re-spoken. Edit events → only frames re-render. 3D renders are cached in `cache/` by spec.

## story.json

Top level: `name`, `title`, `format`, `style` (`accent`, `host_name`, `labels`), `voices` (`host`/`narrator` → kokoro `voice`, `speed`), `music` default, `host` defaults, `scenes`.

Scene:

| key | meaning |
|---|---|
| `id` | unique id |
| `set`, `tone`, `color` | world from `sets.py`; tone `day dusk night dark`; `color` = main colour |
| `music` | `calm upbeat hype happy tense mystery sad dread none` |
| `camera` | `drift static push_in pull_out pan_left pan_right` |
| `enter` | `cut flash whip fade` |
| `header` | `{title, subtitle, meter:{label, from, to, unit}}` pinned at the top |
| `card` | big title overlay `{kicker, title ("\n" for lines), subtitle, y, size}` |
| `host` | `{pose, face, x (0..1 of frame), y, scale, dir: right/left, props:[…], hidden, z}` |
| `objects` | `[{id, prop, args, x, y, scale, dir, hidden, frames (anim cycle), anim: pulse/bob/shake, z}]` (`z` = draw order; host is 0.5) |
| `lines` | `[{id, by: host/narrator, text (spoken), caption (shown), speed, gap}]` |
| `events` | see below |
| `lead`, `tail`, `min_dur` | padding before first line / after last line / minimum length |

Event `at`: seconds, or a line id: `"a"`, `"a.end"`, `"a+0.4"`, `"vo.end-0.2"`. Every event can add `"sfx": "<name>"`.

| `do` | fields |
|---|---|
| `pose` | `pose`, `face`, `dir`, `props` (host) |
| `face` / `props` | change one thing |
| `move` | `target` (default host), `x`, `y`, `dir`, `dur` |
| `grow` | `target`, `scale`, `dur` |
| `show` / `hide` | `target` (pop-in on show) |
| `swap` | `target`, `args` (e.g. bomb grows legs) |
| `camera` | `zoom`, `focus` (`host` or object id), `dur` (zoom 1 resets) |
| `banner` | `text`, `color`, `y`, `size`, `angle`, `dur` |
| `tag` | `text`, `x`, `y`, `color`, `dur` |
| `card` | like scene `card`, at a time |
| `fx` | `speed_lines` (`dir`), `rain`, `confetti`, `explosion` (`x`,`y`), `shake` (`amp`), `flash`, `dim` (`level`) + `dur` |
| `sfx` | `name`, `gain`: whoosh boom pop ding fanfare trombone dial ring steps drumroll scratch heartbeat rise deflate crowd rain |

Ollie's poses: `stand talk explain point point_up proud shrug think phone cheer scared facepalm wave sit flail run walk` (run/walk animate).
Faces: `neutral happy serious angry worried sad shock smug`. Worn props: `helmet hardhat jacket red_shoes phone sunglasses soot cape crown book sign labcoat tie backpack`.
3D props: `bomb (legs, angry, frame) ambulance chair shelter tree car crate trophy coin lightbulb rocket cloud money clock`.

New pose/prop/set: add it to `host.py` / `props.py` / `sets.py`, bump `VERSION` in `render3d.py` only if you changed an existing builder.
