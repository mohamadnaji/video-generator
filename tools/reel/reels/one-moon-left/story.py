"""One Moon Left — Slingshot Planets, Reverse / mystery format, Mission control theme.

Opens on the ending (one moon still flying, seven gone), rewinds, Prof. Bounce bets on the fastest
moon, slow-motion replay, then the why: circle speed, crash below 0.47×, escape above 1.41× (√2).
Every number on screen comes from reelkit.sims.slingshot (the port of the game's sim.ts).

  python reels/one-moon-left/story.py sheet [secs…]
  python reels/one-moon-left/story.py video
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from PIL import ImageDraw  # noqa: E402

from reelkit import sims  # noqa: E402,F401
from reelkit.draw import W, back_out, chip, ease, font, rgba, text  # noqa: E402
from reelkit.reel import Reel, main  # noqa: E402
from reelkit.sims import slingshot as sim  # noqa: E402
from reelkit.theme import THEMES  # noqa: E402

NAME = 'one-moon-left'
TH = THEMES['mission-control']

# ------------------------------------------------------------------ the experiment (real sim numbers)
P = {}
R = 230
SPEEDS = [0.25, 0.35, 0.45, 1.00, 1.50, 1.70, 2.00, 2.40]
BET = 2.40
HZ = 60
moons = [sim.tangential_launch(P, R, s) for s in SPEEDS]
HIST = []  # HIST[k][i] = (x, y, status) at sim time k / HZ
sim.run(P, moons, 70, fps=HZ, record=lambda t, ms: HIST.append([(m.x, m.y, m.status) for m in ms]))
END_T = [m.end_t for m in moons]
FATE = [m.status for m in moons]
CRASH_BELOW = 0.47   # bisection over the sim: tangential launches below 0.465× hit the star
ESCAPE_AT = 1.41     # √2 × circle speed: energy turns positive
assert FATE == ['crashed'] * 3 + ['orbit'] + ['escaped'] * 4, FATE
LAST_END = max(t for t in END_T if t)

# ------------------------------------------------------------------ script
STORY = {
    # af_heart is kokoro's most natural voice; full sentences (not fragments) keep the delivery fluent.
    'voices': {'host': {'voice': 'am_puck', 'speed': 1.08}, 'narrator': {'voice': 'af_heart', 'speed': 1.08}},
    'music_level': 0.7,
    'scenes': [
        {'id': 'cold', 'music': 'mystery', 'lead': 0.3, 'tail': 0.3, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': 'We launched eight moons from the same spot, and only one of them survived.', 'caption': '8 moons, same spot. Only ONE survived.'},
            {'id': 'b', 'by': 'narrator', 'text': "So what made that one special? Let's rewind and find out.", 'caption': "What made it special? Let's rewind.", 'gap': 0.25},
        ]},
        {'id': 'rewind', 'music': 'none', 'lead': 0, 'tail': 0, 'min_dur': 2.0, 'lines': []},
        {'id': 'bet', 'music': 'upbeat', 'lead': 0.2, 'tail': 0.3, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': 'Each moon got a different speed, compared to the perfect orbit speed.',
             'caption': 'Different speeds. 1× = perfect orbit speed.'},
            {'id': 'b', 'by': 'host', 'text': 'Easy! The fastest moon wins. Speed beats gravity!', 'caption': 'Easy! The FASTEST moon wins!', 'gap': 0.25},
        ]},
        {'id': 'replay', 'music': 'tense', 'lead': 0.2, 'tail': 0.3, 'min_dur': 7.5, 'lines': [
            {'id': 'a', 'by': 'host', 'text': 'Go, go, go! Wait, where is it going?', 'caption': 'Go, go, go! Wait... where is it going?', 'gap': 0.0},
            {'id': 'b', 'by': 'narrator', 'text': 'The fast moons were too quick for the star to hold, so they flew away. The slow ones fell right in.', 'caption': 'Too fast: flew away. Too slow: fell in.', 'gap': 0.4},
        ]},
        {'id': 'why', 'music': 'calm', 'lead': 0.2, 'tail': 0.3, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': 'The survivor launched at exactly orbit speed, so gravity bent its path into a perfect circle.',
             'caption': 'Exactly orbit speed = a perfect circle.'},
            {'id': 'b', 'by': 'narrator', 'text': 'Slower than about half that speed, you crash. Faster than one point four times, you fly away forever.',
             'caption': 'Below 0.47×: crash. Above 1.41×: fly away.', 'gap': 0.25},
            {'id': 'c', 'by': 'host', 'text': "So the fastest moon wasn't the winner? I need a new bet!", 'caption': 'The fastest LOST? I need a new bet!', 'gap': 0.25},
        ]},
        {'id': 'end', 'music': 'happy', 'lead': 0.2, 'tail': 0.6, 'lines': [
            {'id': 'a', 'by': 'narrator', 'text': 'That magic number is the square root of two, and rockets leaving Earth follow the exact same rule.',
             'caption': '1.41 = √2. Rockets leaving Earth use the same rule.'},
            {'id': 'b', 'by': 'narrator', 'text': 'Which speed would you choose? Tell us in the comments!', 'caption': 'Which speed would YOU pick? Comment below!', 'gap': 0.25},
        ]},
    ],
}

SFX = [
    ('cold', 0.1, 'rise', 0.5),
    ('cold', 'b+0.9', 'ding'),
    ('rewind', 0.0, 'scratch'),
    ('rewind', 0.2, 'whoosh'),
    ('bet', 'b+0.2', 'pop'),
    ('why', 'a+0.3', 'ding'),
    ('why', 'c+0.6', 'trombone', 0.7),
    ('end', 'b.end+0.1', 'fanfare', 0.6),
]
# crash / escape sounds land exactly when the slow-motion replay reaches each fate
SLOW = 0.45
REPLAY_LEAD = 0.6  # seconds of the replay before launch
for i, t in enumerate(END_T):
    if t:
        SFX.append(('replay', REPLAY_LEAD + t / SLOW, 'boom' if FATE[i] == 'crashed' else 'whoosh', 0.55 if FATE[i] == 'crashed' else 0.4))


# ------------------------------------------------------------------ sim time for each scene
def sim_time(sid, lt, ctx):
    """Maps scene time to experiment time. The cold open shows the end; the rewind runs it backwards."""
    cold_t0 = 12.0
    if sid == 'cold':
        return cold_t0 + lt
    if sid == 'rewind':
        k = ease(lt / ctx.dur('rewind'))
        return (cold_t0 + ctx.dur('cold')) * (1 - k)
    if sid == 'bet':
        return 0.0
    if sid == 'replay':
        slow_end = REPLAY_LEAD + (LAST_END + 0.2) / SLOW
        if lt < REPLAY_LEAD:
            return 0.0
        if lt < slow_end:
            return (lt - REPLAY_LEAD) * SLOW
        return (LAST_END + 0.2) + (lt - slow_end)
    base = sim_time('replay', ctx.dur('replay'), ctx)
    if sid == 'why':
        return base + lt
    return base + ctx.dur('why') + lt


def snapshot(st):
    k = max(0, min(len(HIST) - 1, int(st * HZ)))
    return k, HIST[k]


def fate_known(i, st):
    return END_T[i] is not None and st >= END_T[i]


# ------------------------------------------------------------------ drawing
STAGE = (40, 300, 1040, 1300)          # square space window
CX, CY = (STAGE[0] + STAGE[2]) / 2, (STAGE[1] + STAGE[3]) / 2
SCALE = 470 / sim.SYSTEM_R
MONO = TH['mono']


def X(x):
    return CX + x * SCALE


def Y(y):
    return CY + y * SCALE


STARS = [((math.sin(i * 12.9898) * 43758.5453) % 1, (math.sin(i * 78.233) * 12345.678) % 1, 1 + (i % 4 == 0)) for i in range(220)]


def moon_color(i, st, sid):
    if fate_known(i, st):
        return TH['danger'] if FATE[i] == 'crashed' else TH['escape']
    if FATE[i] == 'orbit' and sid in ('cold', 'why', 'end'):
        return TH['ok']
    return TH['moon']


def draw_stage(img, sid, st, lt, ctx):
    d = ImageDraw.Draw(img, 'RGBA')
    x0, y0, x1, y1 = STAGE
    d.rounded_rectangle(STAGE, 28, fill=TH['panel'], outline=TH['grid'], width=3)
    for u, v, s in STARS:
        px, py = x0 + 20 + u * (x1 - x0 - 40), y0 + 20 + v * (y1 - y0 - 40)
        d.rectangle((px, py, px + s, py + s), fill=rgba(TH['ink'], 0.35))
    # system edge
    r_edge = sim.SYSTEM_R * SCALE
    for a in range(0, 360, 6):
        a0, a1 = math.radians(a), math.radians(a + 3)
        d.line((CX + r_edge * math.cos(a0), CY + r_edge * math.sin(a0), CX + r_edge * math.cos(a1), CY + r_edge * math.sin(a1)), fill=rgba(TH['muted'], 0.35), width=2)
    # perfect circle guide in the explanation
    if sid in ('why', 'end'):
        k = ease(lt / 0.8) if sid == 'why' else 1
        rr = R * SCALE
        d.arc((CX - rr, CY - rr, CX + rr, CY + rr), -90, -90 + 360 * k, fill=rgba(TH['ok'], 0.45), width=4)
    # star with glow
    sr = sim.STAR_R * SCALE * 1.15
    for g in range(10, 0, -1):
        rr = sr * (1 + g * 0.28)
        d.ellipse((CX - rr, CY - rr, CX + rr, CY + rr), fill=rgba(TH['sun'], 0.05))
    d.ellipse((CX - sr, CY - sr, CX + sr, CY + sr), fill=TH['sun'])
    # launch pad
    lx, ly = X(0), Y(-R)
    d.line((lx, ly - 30, lx, ly - 12), fill=TH['accent'], width=4)
    if sid not in ('why', 'end', 'bet'):
        text(d, (lx, ly - 48), 'LAUNCH PAD', font(MONO, 22), TH['accent'])

    k, snap = snapshot(st)
    # trails (last ~0.7 s of flight)
    for i, (x, y, status) in enumerate(snap):
        col = moon_color(i, st, sid)
        tail = 42 if FATE[i] == 'orbit' else 30
        pts = []
        for j in range(max(0, k - tail), k + 1):
            hx, hy, hs = HIST[j][i]
            if END_T[i] is not None and j / HZ > END_T[i]:
                break
            pts.append((X(hx), Y(hy)))
        for n in range(1, len(pts)):
            d.line((pts[n - 1], pts[n]), fill=rgba(col, 0.15 + 0.75 * n / len(pts)), width=5 if FATE[i] == 'orbit' else 4)
    # moons and fates
    for i, (x, y, status) in enumerate(snap):
        col = moon_color(i, st, sid)
        if fate_known(i, st):
            age = st - END_T[i]
            if FATE[i] == 'crashed' and age < 0.9:
                ex, ey = HIST[int(END_T[i] * HZ)][i][:2]
                rr = 10 + age * 70
                d.ellipse((X(ex) - rr, Y(ey) - rr, X(ex) + rr, Y(ey) + rr), outline=rgba(TH['danger'], 1 - age / 0.9), width=5)
            continue
        rad = 13 if FATE[i] == 'orbit' and sid in ('cold', 'why', 'end') else 10
        if rad == 13:
            d.ellipse((X(x) - 26, Y(y) - 26, X(x) + 26, Y(y) + 26), fill=rgba(TH['ok'], 0.22))
        d.ellipse((X(x) - rad, Y(y) - rad, X(x) + rad, Y(y) + rad), fill=col)
    return d


def scoreboard(d, sid, st, lt):
    """Row of eight chips under the stage: launch speeds and their fates."""
    y = 1365
    f = font(MONO, 30)
    n = len(SPEEDS)
    gap = (W - 60) / n
    hidden = sid == 'cold' or (sid == 'rewind' and lt < 0.9)
    for i, s in enumerate(SPEEDS):
        x = 30 + gap * (i + 0.5)
        known = fate_known(i, st) or (sid in ('why', 'end') and FATE[i] == 'orbit') or (sid == 'cold' and FATE[i] == 'orbit')
        if known and FATE[i] == 'crashed':
            bg, fg = TH['danger'], TH['bg']
        elif known and FATE[i] == 'escaped':
            bg, fg = TH['escape'], TH['bg']
        elif known:
            bg, fg = TH['ok'], TH['bg']
        else:
            bg, fg = TH['panel'], TH['ink']
        label = '?' if hidden else f'{s:.2f}×'
        chip(d, x, y, label, f, fg, bg, pad=(10, 12), radius=14, outline=TH['accent'] if (s == BET and sid in ('bet', 'replay')) else None)
        if known:
            tag = {'crashed': 'CRASHED', 'escaped': 'FLEW OFF', 'orbit': 'SURVIVED'}[FATE[i]]
            text(d, (x, y + 46), tag, font(MONO, 21), bg)
    if sid in ('bet', 'replay'):
        bx = 30 + gap * (SPEEDS.index(BET) + 0.5)
        text(d, (bx, y - 46), 'PROF\'S BET', font(MONO, 22), TH['accent'])


def zone_bar(d, lt):
    """Speed line 0×–2.5×: crash zone, stay zone, escape zone, with each moon's mark."""
    y, x0, x1 = 1365, 70, 1010
    vmax = 2.5
    k = ease(lt / 0.6)
    xs = lambda v: x0 + (x1 - x0) * v / vmax  # noqa: E731
    d.rounded_rectangle((x0 - 20, y - 70, x1 + 20, y + 70), 18, fill=rgba(TH['panel'], k))
    zones = [(0, CRASH_BELOW, TH['danger'], 'CRASH'), (CRASH_BELOW, ESCAPE_AT, TH['ok'], 'ORBITS'), (ESCAPE_AT, vmax, TH['escape'], 'FLIES AWAY')]
    for a, b, col, lab in zones:
        d.rectangle((xs(a), y - 10, xs(b), y + 10), fill=rgba(col, k))
        text(d, ((xs(a) + xs(b)) / 2, y - 42), lab, font(MONO, 28), rgba(col, k))
    for v in (CRASH_BELOW, ESCAPE_AT):
        text(d, (xs(v), y + 42), f'{v:.2f}×', font(MONO, 28), rgba(TH['ink'], k))
    for i, s in enumerate(SPEEDS):
        col = TH['ok'] if FATE[i] == 'orbit' else TH['danger'] if FATE[i] == 'crashed' else TH['escape']
        d.ellipse((xs(s) - 9, y - 9, xs(s) + 9, y + 9), fill=rgba(TH['bg'], k), outline=rgba(col, k), width=4)


def callouts(d, st):
    """Big words on the stage the moment moons crash or fly off."""
    f = font(TH['display'], 52)
    crashed = [i for i in range(len(SPEEDS)) if FATE[i] == 'crashed' and fate_known(i, st) and st - END_T[i] < 1.4]
    if crashed:
        text(d, (CX, CY + 110), f'{len(crashed)} CRASHED!', f, TH['danger'], stroke=6, stroke_fill=TH['bg'])
    gone = [i for i in range(len(SPEEDS)) if FATE[i] == 'escaped' and fate_known(i, st)]
    if gone and st - max(END_T[i] for i in gone) < 1.4:
        text(d, (CX, STAGE[1] + 130), f'{len(gone)} FLEW AWAY!', f, TH['escape'], stroke=6, stroke_fill=TH['bg'])


def launch_arrows(d, lt):
    """Eight launch pushes stacked above the pad, arrow length = speed, so the sizes are easy to compare."""
    lx = X(0)
    top = STAGE[1] + 45
    for i, s in enumerate(SPEEDS):
        k = ease((lt - 0.15 * i) / 0.4)
        if k <= 0:
            continue
        y = top + i * 32
        x_tip = lx - s * 150 * k
        col = TH['accent'] if s == BET and lt >= 0.2 + 0.15 * len(SPEEDS) else TH['moon']
        d.line((lx, y, x_tip + 10, y), fill=col, width=5)
        d.polygon([(x_tip, y), (x_tip + 16, y - 9), (x_tip + 16, y + 9)], fill=col)
        text(d, (x_tip - 14, y), f'{s:.2f}×', font(MONO, 27), col, anchor='rm')
    text(d, (lx + 24, top), 'LAUNCH SPEED', font(MONO, 28), TH['muted'], anchor='lm')


HEADERS = {
    'cold': ('8 MOONS · SAME LAUNCH SPOT', 'ONLY 1 SURVIVED'),
    'rewind': ('BACK TO THE LAUNCH', "LET'S REWIND"),
    'bet': ('1× = PERFECT ORBIT SPEED', 'WHICH ONE SURVIVES?'),
    'replay': ('1× = PERFECT ORBIT SPEED', 'SLOW-MO REPLAY'),
    'why': ('THE ANSWER', 'WHY THIS ONE?'),
    'end': ('THE ESCAPE RULE', 'FLY AWAY = 1.41× ORBIT'),
}


def draw(img, sid, lt, ctx):
    st = sim_time(sid, lt, ctx)
    d = draw_stage(img, sid, st, lt, ctx)
    kicker, title = HEADERS[sid]
    text(d, (W / 2, 110), kicker, font(MONO, 34), TH['accent'] if kicker.startswith('1×') else TH['muted'])
    pop = back_out(lt / 0.35)
    text(d, (W / 2, 200), title, font(TH['display'], int(86 * (0.85 + 0.15 * pop))), TH['ink'], stroke=4, stroke_fill=TH['bg'])
    if sid == 'cold':
        alive = sum(1 for i in range(len(SPEEDS)) if not fate_known(i, st))
        chip(d, W / 2, 264, f'{alive} ALIVE · {len(SPEEDS) - alive} LOST', font(MONO, 30), TH['bg'], TH['accent'], pad=(18, 6))
    if sid == 'rewind':
        # tape rewind look: scanlines, flicker and a big ◀◀
        for yy in range(STAGE[1], STAGE[3], 6):
            d.line((STAGE[0], yy, STAGE[2], yy), fill=(0, 0, 0, 60))
        a = 0.6 + 0.4 * math.sin(lt * 18)
        for k2 in range(2):
            x = CX - 60 + k2 * 70
            d.polygon([(x - 10, CY - 260), (x + 50, CY - 300), (x + 50, CY - 220)], fill=rgba(TH['ink'], a))
        text(d, (CX + 140, CY - 260), f'{st:5.1f} s', font(MONO, 40), rgba(TH['ink'], a))
    if sid == 'cold':
        si = SPEEDS.index(1.0)
        sx, sy = HIST[int(st * HZ)][si][:2]
        chip(d, X(sx), Y(sy) - 54, 'WHY THIS ONE?', font(TH['display'], 34), TH['bg'], TH['ok'], pad=(16, 6))
    if sid == 'replay':
        callouts(d, st)
        speed = 'SLOW-MO 0.45×' if st < LAST_END + 0.2 else 'REAL TIME'
        chip(d, STAGE[0] + 30, STAGE[1] + 40, f'● {speed}', font(MONO, 24), TH['danger'], rgba(TH['bg'], 0.8), anchor='lm', pad=(14, 8))
        chip(d, STAGE[2] - 30, STAGE[1] + 40, f't = {st:4.2f} s', font(MONO, 24), TH['ink'], rgba(TH['bg'], 0.8), anchor='rm', pad=(14, 8))
    if sid in ('why', 'end'):
        zone_bar(d, lt if sid == 'why' else 5)
        if sid == 'why':
            sx, sy = HIST[int(st * HZ)][SPEEDS.index(1.0)][:2]
            chip(d, X(sx), Y(sy) - 52, 'SURVIVOR · 1×', font(MONO, 30), TH['bg'], TH['ok'], pad=(14, 8))
    else:
        scoreboard(d, sid, st, lt)
    if sid == 'bet':
        launch_arrows(d, lt)


def host(sid, lt, ctx):
    if sid == 'rewind':
        return None
    face = 'happy'
    look = 0.4
    if sid == 'cold':
        face, look = 'think', 0.6
    elif sid == 'bet':
        face = 'smug' if lt >= ctx.at('bet', 'b') else 'happy'
    elif sid == 'replay':
        lost = sim_time('replay', lt, ctx) >= END_T[SPEEDS.index(BET)]
        face = 'shock' if lost else 'happy'
        if lt > ctx.at('replay', 'b+1.5'):
            face = 'worried'
    elif sid == 'why':
        face = 'facepalm' if lt >= ctx.at('why', 'c.end') else 'worried' if lt >= ctx.at('why', 'c') else 'think'
    elif sid == 'end':
        face = 'happy'
    return {'x': 150, 'y': 1880, 'size': 175, 'face': face, 'look': look}


if __name__ == '__main__':
    main(Reel(HERE, STORY, TH, draw, host, SFX, caption_y=1545), NAME)
