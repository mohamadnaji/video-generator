"""Marble Showdown — Marble Galton Board, Versus format, Casino theme.

Prof. Bounce vs Physics: who predicts marbles better? Prof. Bounce bets on single marbles and misses
twice (bin 7 -> lands 10, bin 10 -> lands 3). Physics predicts 1,000 marbles from last night's run, and
tonight's run lands on top of it (bin 7: 218 both nights). Why: 12 coin flips per marble.
Every number on screen comes from reelkit.sims.galton (the port of the game's sim.ts).

  python reels/marble-showdown/story.py sheet [secs…]
  python reels/marble-showdown/story.py video
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from PIL import ImageDraw  # noqa: E402

from reelkit.draw import W, back_out, chip, ease, font, rgba, text  # noqa: E402
from reelkit.reel import Reel, main  # noqa: E402
from reelkit.sims import galton as sim  # noqa: E402
from reelkit.theme import THEMES  # noqa: E402

NAME = 'marble-showdown'
TH = THEMES['casino']
MONO, DISPLAY = TH['mono'], TH['display']

# ------------------------------------------------------------------ the experiment (real sim runs)
P1 = dict(sim.DEFAULT, total=1)            # one marble at a time
P1000 = dict(sim.DEFAULT, rate=120)        # the big drop: 1,000 marbles, 120 per second
PLAY = 3.0                                 # playback speed of every drop (shown on screen)


def record(p, seed):
    frames = []

    def rec(t, b):
        frames.append(([(m.x, m.y) for m in b.marbles], list(b.counts), b.pile_scale(), b.landed))
    board = sim.run(p, seed, record=rec)
    return frames, board


DEMO, BDEMO = record(P1, 4)      # intro: one marble to show how the board works
ROUND1, B1 = record(P1, 1)       # Prof bets bin 7
ROUND2, B2 = record(P1, 26)      # Prof bets bin 10
LIVE, BLIVE = record(P1000, 13)  # tonight
_, BLAST = record(P1000, 12)     # last night (the prediction)
BOARD = sim.Board(12)
BET1, BET2 = 7, 10
LAND1, LAND2 = B1.landings[0][1] + 1, B2.landings[0][1] + 1
CENTER_LAST, CENTER_LIVE = BLAST.counts[6], BLIVE.counts[6]
MID_LAST, MID_LIVE = sum(BLAST.counts[4:9]), sum(BLIVE.counts[4:9])
assert (LAND1, LAND2) == (10, 3), (LAND1, LAND2)
assert CENTER_LAST == CENTER_LIVE == 218, (CENTER_LAST, CENTER_LIVE)
FALL1 = (len(ROUND1) - 1) / 30 / PLAY
FALL2 = (len(ROUND2) - 1) / 30 / PLAY
LIVE_DUR = (len(LIVE) - 1) / 30 / PLAY

# ------------------------------------------------------------------ script
STORY = {
    # Host: am_michael at normal speed with full, conversational sentences sounds the most natural.
    'voices': {'host': {'voice': 'am_michael', 'speed': 1.05}, 'narrator': {'voice': 'af_heart', 'speed': 1.08}},
    'music_level': 0.65,
    'scenes': [
        {'id': 'intro', 'music': 'mystery', 'lead': 0.3, 'tail': 0.2, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': 'Can you predict where a marble will land?'},
            {'id': 'b', 'by': 'narrator', 'text': 'It bounces off twelve rows of pegs, then drops into one of thirteen bins.',
             'caption': 'It bounces off 12 rows of pegs into 1 of 13 bins.', 'gap': 0.2},
        ]},
        {'id': 'r1', 'music': 'upbeat', 'lead': 0.2, 'tail': 0.3, 'lines': [
            {'id': 'a', 'by': 'host', 'text': "Oh, that's easy. Right in the middle, bin seven.", 'caption': "That's easy. Right in the middle: bin 7."},
            {'id': 'b', 'by': 'narrator', 'text': "Bin ten. That's a miss.", 'caption': 'Bin 10. MISS!', 'gap': FALL1 + 0.5},
        ]},
        {'id': 'r2', 'music': 'upbeat', 'lead': 0.2, 'tail': 0.2, 'lines': [
            {'id': 'a', 'by': 'host', 'text': "Okay, it likes bin ten. I'll take ten again.", 'caption': "It likes bin 10. I'll take 10 again."},
            {'id': 'b', 'by': 'host', 'text': "Wait, bin three? That's not fair at all.", 'caption': "Wait, bin 3? That's not fair!", 'gap': FALL2 + 0.4},
        ]},
        {'id': 'phys', 'music': 'tense', 'lead': 0.2, 'tail': 0.0, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': "Physics won't guess one marble. It predicts a thousand, using last night's run.",
             'caption': "Physics predicts 1,000 marbles from last night's run."},
            {'id': 'b', 'by': 'host', 'text': "With brand new marbles? There's no way that matches.", 'caption': 'Brand new marbles? No way that matches.', 'gap': 1.0},
        ]},
        {'id': 'reveal', 'music': 'happy', 'lead': 0.2, 'tail': 0.6, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': 'Last night, bin seven got two hundred eighteen marbles. Tonight? Exactly two hundred eighteen.',
             'caption': 'Bin 7 last night: 218. Tonight: exactly 218.'},
        ]},
        {'id': 'why', 'music': 'calm', 'lead': 0.2, 'tail': 0.3, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': "Every peg is a coin flip, and a mix of lefts and rights is far more likely than all lefts. That's a bell curve.",
             'caption': 'Every peg = a coin flip. Mixed flips win, so: BELL CURVE.'},
        ]},
        {'id': 'end', 'music': 'happy', 'lead': 0.2, 'tail': 0.35, 'lines': [
            {'id': 'a', 'by': 'host', 'text': "Fine, physics wins. But I'm keeping my lucky bin.", 'caption': "Fine, physics wins. I'm keeping my lucky bin!"},
            {'id': 'b', 'by': 'narrator', 'text': 'Which bin would you pick? Comment below!', 'caption': 'Which bin would YOU pick? Comment below!', 'gap': 0.2},
        ]},
    ],
}

SFX = [
    ('intro', 0.1, 'rise', 0.4),
    ('r1', 0.0, 'drumroll', 0.4),
    ('r1', 'a.end', 'pop'),
    ('r1', 'a.end+%.2f' % (0.2 + FALL1), 'trombone', 0.6),
    ('r2', 'a.end', 'pop'),
    ('r2', 'a.end+%.2f' % (0.2 + FALL2), 'trombone', 0.6),
    ('phys', 'a.end+0.2', 'rise', 0.5),
    ('reveal', 'a.end-0.3', 'ding'),
    ('reveal', 'a.end', 'crowd', 0.6),
    ('end', 'b.end+0.1', 'fanfare', 0.6),
]


def fit_drop(reel):
    """After voicing: stretch the physics round so the whole 1,000-marble drop plays out."""
    t = reel.ctx.at('phys', 'a.end+0.2') + LIVE_DUR + 0.25
    for sc in STORY['scenes']:
        if sc['id'] == 'phys':
            sc['min_dur'] = t
    reel.voice()


# ------------------------------------------------------------------ which board state each scene shows
def state(sid, lt, ctx):
    """-> (frames, frame index, show-prediction) for the scene time."""
    def idx(frames, t0):
        return max(0, min(len(frames) - 1, int((lt - t0) * 30 * PLAY))) if lt >= t0 else -1
    if sid == 'intro':
        return DEMO, idx(DEMO, ctx.at('intro', 'a.end-0.6'))
    if sid == 'r1':
        return ROUND1, idx(ROUND1, ctx.at('r1', 'a.end+0.2'))
    if sid == 'r2':
        return ROUND2, idx(ROUND2, ctx.at('r2', 'a.end+0.2'))
    if sid == 'phys':
        return LIVE, idx(LIVE, ctx.at('phys', 'a.end+0.2'))
    if sid in ('reveal', 'why', 'end'):
        return LIVE, len(LIVE) - 1
    return None, -1


def live_started_dur(ctx):
    return ctx.dur('phys') - ctx.at('phys', 'a.end+0.2')


# ------------------------------------------------------------------ drawing
STAGE = (40, 320, 1040, 1420)
BIN_SQUASH = 0.45   # bins drawn shorter than in the game so the pegs and marbles can be bigger
WORLD_W = BOARD.width + 0.5
WORLD_H = BOARD.bin_top + sim.BIN_DEPTH * BIN_SQUASH + 1.6
S = min((STAGE[2] - STAGE[0]) / WORLD_W, (STAGE[3] - STAGE[1] - 30) / WORLD_H)
OX = (STAGE[0] + STAGE[2]) / 2 - BOARD.width * S / 2
OY = STAGE[1] + 34


def X(x):
    return OX + x * S


def Y(y):
    if y > BOARD.bin_top:
        y = BOARD.bin_top + (y - BOARD.bin_top) * BIN_SQUASH
    return OY + y * S


def H(h):  # pile height in world units -> pixels
    return h * BIN_SQUASH * S


def bin_x(b):  # bin number 1..13 -> centre x
    return X(b - 0.5)


def draw_board(d, frames, k, prediction, pulse_bins=()):
    # felt panel
    d.rounded_rectangle(STAGE, 30, fill=TH['panel'], outline=TH['accent'], width=4)
    # funnel
    d.line((X(BOARD.width / 2 - 2.2), Y(-0.4), X(BOARD.width / 2 - 0.35), Y(0.45)), fill=TH['muted'], width=5)
    d.line((X(BOARD.width / 2 + 2.2), Y(-0.4), X(BOARD.width / 2 + 0.35), Y(0.45)), fill=TH['muted'], width=5)
    for px, py in BOARD.pegs:
        r = max(3, sim.PEG_R * S)
        d.ellipse((X(px) - r, Y(py) - r, X(px) + r, Y(py) + r), fill=TH['peg'])
    for i in range(BOARD.bins + 1):
        d.line((X(i), Y(BOARD.bin_top), X(i), Y(BOARD.floor)), fill=TH['grid'], width=4)
    d.line((X(0), Y(BOARD.floor), X(BOARD.width), Y(BOARD.floor)), fill=TH['muted'], width=4)
    for b in range(1, BOARD.bins + 1):
        col = TH['accent'] if b in pulse_bins else TH['muted']
        text(d, (bin_x(b), Y(BOARD.floor) + 34), str(b), font(MONO, 32), col)
    counts, scale, marbles = [0] * BOARD.bins, None, []
    if frames is not None and k >= 0:
        marbles, counts, scale, _ = frames[k]
    if prediction:
        # last night's pile as a gold outline, on its own scale (both runs squeeze piles the same way)
        ps = BLAST.pile_scale()
        pts = []
        for i, c in enumerate(BLAST.counts):
            h = H(c * ps)
            pts += [(X(i), Y(BOARD.floor) - h), (X(i + 1), Y(BOARD.floor) - h)]
        for a, b in zip(pts, pts[1:]):
            d.line((a, b), fill=rgba(TH['accent'], prediction), width=6)
    # piles
    if scale is not None:
        for i, c in enumerate(counts):
            if not c:
                continue
            h = H(c * scale)
            if c <= 6:
                rad = sim.MARBLE_R * S
                for j in range(c):
                    cx = X(i + 0.5) + (j % 2 - 0.5) * rad * 2.1
                    cy = Y(BOARD.floor) - rad - (j // 2) * rad * 2 * BIN_SQUASH
                    d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=pile_color(i))
            else:
                d.rectangle((X(i + 0.08), Y(BOARD.floor) - h, X(i + 0.92), Y(BOARD.floor)), fill=pile_color(i))
    r = max(4, sim.MARBLE_R * S)
    for mx, my in marbles:
        d.ellipse((X(mx) - r, Y(my) - r, X(mx) + r, Y(my) + r), fill=TH['marble'])


def pile_color(i):
    """Gold in the middle bins, coral toward the edges."""
    k = min(1.0, abs(i - 6) / 5)
    a, b = TH['pile'].lstrip('#'), TH['pile_edge'].lstrip('#')
    ca = [int(a[j:j + 2], 16) for j in (0, 2, 4)]
    cb = [int(b[j:j + 2], 16) for j in (0, 2, 4)]
    return tuple(int(x + (y - x) * k) for x, y in zip(ca, cb))


def bet_chip(d, b, label, lt0):
    """A casino chip on bin b's number with PROF's label, popping in."""
    k = back_out(lt0 / 0.35) if lt0 >= 0 else 0
    if k <= 0:
        return
    x, y, r = bin_x(b), Y(BOARD.floor) + 34, 34 * k
    d.ellipse((x - r, y - r, x + r, y + r), fill=TH['chip_red'], outline=TH['ink'], width=4)
    d.ellipse((x - r * 0.65, y - r * 0.65, x + r * 0.65, y + r * 0.65), outline=TH['ink'], width=2)
    text(d, (x, y), str(b), font(DISPLAY, int(28 * k) + 1), TH['ink'])
    chip(d, x, y + 58, f"{label}'S BET", font(MONO, 22), TH['bg'], TH['host_body'], pad=(10, 4))


def stamp(d, s, col, lt0, y=None):
    """Big word stamped on the board (MISS!, MATCH!)."""
    if lt0 < 0:
        return
    k = back_out(lt0 / 0.3)
    text(d, (W / 2, y or (STAGE[1] + 260)), s, font(DISPLAY, int(110 * k) + 1), col, stroke=8, stroke_fill=TH['bg'])


def scoreboard(d, sid, lt, ctx):
    phys = 1 if sid in ('why', 'end') or (sid == 'reveal' and lt >= ctx.at('reveal', 'a.end')) else 0
    f = font(DISPLAY, 46)
    chip(d, W / 2 - 40, 230, 'PROF  0', f, TH['bg'], TH['host_body'], anchor='rm', pad=(24, 6))
    chip(d, W / 2 + 40, 230, f'{phys}  PHYSICS', f, TH['bg'], TH['accent'], anchor='lm', pad=(24, 6))
    text(d, (W / 2, 230), 'vs', font(DISPLAY, 40), TH['ink'])


TITLES = {'intro': 'CAN YOU PREDICT IT?', 'r1': 'ROUND 1 · PROF', 'r2': 'ROUND 2 · PROF', 'phys': 'ROUND 3 · PHYSICS',
          'reveal': 'THE RESULT', 'why': 'WHY IT WORKS', 'end': 'PHYSICS WINS'}


def draw(img, sid, lt, ctx):
    d = ImageDraw.Draw(img, 'RGBA')
    # felt texture dots
    for i in range(140):
        u, v = (math.sin(i * 12.9898) * 43758.5453) % 1, (math.sin(i * 78.233) * 12345.678) % 1
        d.ellipse((u * W, v * 1920, u * W + 3, v * 1920 + 3), fill=rgba(TH['grid'], 0.6))
    pop = back_out(lt / 0.35)
    text(d, (W / 2, 120), TITLES[sid], font(DISPLAY, int(78 * (0.85 + 0.15 * pop))), TH['ink'], stroke=4, stroke_fill=TH['bg'])
    if sid != 'intro':
        scoreboard(d, sid, lt, ctx)

    frames, k = state(sid, lt, ctx)
    pred = 0.0
    if sid == 'phys':
        pred = ease((lt - 1.0) / 0.6)
    elif sid in ('reveal', 'why', 'end'):
        pred = 1.0
    pulse = ()
    if sid == 'r1':
        pulse = (BET1,) if lt >= ctx.at('r1', 'a+1.2') else ()
    if sid == 'r2':
        pulse = (BET2,) if lt >= ctx.at('r2', 'a+1.0') else ()
    if sid == 'reveal':
        pulse = (7,) if lt < ctx.at('reveal', 'a.end') else (5, 6, 7, 8, 9)
    draw_board(d, frames, k, pred, pulse)

    if sid == 'intro':
        if lt >= ctx.at('intro', 'b+0.6'):
            chip(d, W / 2, Y(BOARD.peg_top + 5 * 0.866), '12 ROWS OF PEGS', font(DISPLAY, 40), TH['bg'], TH['peg'], pad=(18, 6))
        if lt >= ctx.at('intro', 'b+2.4'):
            chip(d, W / 2, Y(BOARD.bin_top) + 70, '13 BINS', font(DISPLAY, 40), TH['bg'], TH['accent'], pad=(18, 6))
    if sid in ('intro', 'r1', 'r2', 'phys'):
        chip(d, STAGE[0] + 24, STAGE[1] + 40, f'▶ {PLAY:g}× SPEED', font(MONO, 24), TH['ink'], rgba(TH['bg'], 0.8), anchor='lm', pad=(14, 8))
    if sid == 'r1':
        bet_chip(d, BET1, 'PROF', lt - ctx.at('r1', 'a+1.2'))
        landed = lt - ctx.at('r1', 'a.end+0.2') - FALL1
        if landed >= 0:
            chip(d, bin_x(LAND1), Y(BOARD.bin_top) - 40, f'LANDED: {LAND1}', font(MONO, 26), TH['bg'], TH['marble'], pad=(12, 6))
            stamp(d, 'MISS!', TH['danger'], landed)
    if sid == 'r2':
        bet_chip(d, BET2, 'PROF', lt - ctx.at('r2', 'a+1.0'))
        landed = lt - ctx.at('r2', 'a.end+0.2') - FALL2
        if landed >= 0:
            chip(d, bin_x(LAND2), Y(BOARD.bin_top) - 40, f'LANDED: {LAND2}', font(MONO, 26), TH['bg'], TH['marble'], pad=(12, 6))
            stamp(d, 'MISS!', TH['danger'], landed)
    if sid == 'phys' and pred > 0:
        chip(d, STAGE[2] - 24, STAGE[1] + 40, "— LAST NIGHT'S RUN", font(MONO, 24), TH['accent'], rgba(TH['bg'], 0.8), anchor='rm', pad=(14, 8))
        if k >= 0:
            chip(d, W / 2, STAGE[1] + 100, f'TONIGHT: {LIVE[k][3]:,} / 1,000', font(MONO, 30), TH['bg'], TH['marble'], pad=(16, 8))
    if sid == 'reveal':
        lt_a = lt - ctx.at('reveal', 'a')
        x7 = bin_x(7)
        top7 = Y(BOARD.floor) - H(CENTER_LIVE * BLIVE.pile_scale())
        if lt_a >= 0:
            chip(d, x7 - 150, top7 - 70, f'LAST NIGHT {CENTER_LAST}', font(MONO, 26), TH['bg'], TH['accent'], pad=(12, 6))
        if lt >= ctx.at('reveal', 'a.end-1.6'):
            chip(d, x7 + 150, top7 - 70, f'TONIGHT {CENTER_LIVE}', font(MONO, 26), TH['bg'], TH['marble'], pad=(12, 6))
            stamp(d, 'MATCH!', TH['ok'], lt - ctx.at('reveal', 'a.end-1.6'), y=STAGE[1] + 200)
        if lt >= ctx.at('reveal', 'a.end'):
            chip(d, W / 2, STAGE[1] + 320, f'MIDDLE 5 BINS: {MID_LAST / 10:.0f}% · {MID_LIVE / 10:.0f}%', font(MONO, 28), TH['bg'], TH['accent'], pad=(14, 8))
    if sid == 'why':
        # a marble's 12 coin flips, as L/R tiles
        flips = 'LRRLRLLRLRRL'
        n = min(12, int((lt / max(0.1, ctx.at('why', 'a.end'))) * 14))
        x0 = W / 2 - 6 * 62 + 31
        for i in range(n):
            col = TH['danger'] if flips[i] == 'L' else TH['moon']
            d.rounded_rectangle((x0 + i * 62 - 26, STAGE[1] + 70, x0 + i * 62 + 26, STAGE[1] + 130), 10, fill=col)
            text(d, (x0 + i * 62, STAGE[1] + 100), flips[i], font(DISPLAY, 34), TH['bg'])
        if lt >= ctx.at('why', 'a.end-2.2'):
            text(d, (W / 2, STAGE[1] + 190), 'BELL CURVE', font(DISPLAY, 64), TH['accent'], stroke=6, stroke_fill=TH['bg'])


def host(sid, lt, ctx):
    face, look = 'happy', 0.4
    if sid == 'intro':
        face = 'think'
    elif sid == 'r1':
        landed = lt - ctx.at('r1', 'a.end+0.2') - FALL1
        face = 'shock' if landed >= 0 else 'smug'
    elif sid == 'r2':
        landed = lt - ctx.at('r2', 'a.end+0.2') - FALL2
        face = 'smug' if landed < 0 else 'shock'
    elif sid == 'phys':
        face = 'smug' if lt < ctx.at('phys', 'b.end+1.5') else 'worried'
    elif sid in ('reveal', 'why'):
        face = 'shock' if sid == 'reveal' else 'think'
    elif sid == 'end':
        face = 'facepalm' if lt < ctx.at('end', 'a+1.2') else 'happy'
    return {'x': 150, 'y': 1872, 'size': 165, 'face': face, 'look': look}


if __name__ == '__main__':
    main(Reel(HERE, STORY, TH, draw, host, SFX, caption_y=1548), NAME, after_voice=fit_drop)
