"""Prof. Bounce, the recurring host: an orange bouncy ball with big glasses and a bow tie.
draw_prof(img, x, y, size, ...) draws him with his feet at (x, y)."""
import math

from PIL import Image, ImageDraw

from .draw import rgba

FACES = ('happy', 'smug', 'shock', 'worried', 'facepalm', 'think')


def draw_prof(img, x, y, size, theme, t, face='happy', mouth=0.0, look=0.0, bounce=True, name=True):
    """size = body diameter in px. mouth 0..1 opens the mouth (lip sync). look -1..1 shifts the eyes."""
    S = int(size * 2)
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    hop = abs(math.sin(t * 3.2)) if bounce else 0
    squash = 1 + 0.06 * math.cos(t * 6.4) if bounce else 1
    bw, bh = size * squash, size / squash
    cx, cy = S / 2, S - bh / 2 - 8 - hop * size * 0.12
    body, dark = theme['host_body'], theme['host_dark']
    # shadow
    sw = bw * (0.8 - 0.25 * hop)
    d.ellipse((cx - sw / 2, S - 14, cx + sw / 2, S - 2), fill=(0, 0, 0, 90))
    # body with a soft highlight
    d.ellipse((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), fill=body, outline=dark, width=max(3, int(size * 0.025)))
    d.ellipse((cx - bw * 0.32, cy - bh * 0.4, cx - bw * 0.08, cy - bh * 0.22), fill=(255, 255, 255, 70))
    # glasses
    er = size * 0.13
    ex = size * 0.17
    ey = cy - size * 0.1
    for sx in (-1, 1):
        gx = cx + sx * ex
        d.ellipse((gx - er, ey - er, gx + er, ey + er), fill='#ffffff', outline='#1b1b1b', width=max(3, int(size * 0.03)))
        if face == 'facepalm':
            d.line((gx - er * 0.6, ey, gx + er * 0.6, ey), fill='#1b1b1b', width=max(3, int(size * 0.03)))
        else:
            pr = er * (0.55 if face == 'shock' else 0.42)
            px = gx + look * er * 0.35
            py = ey + (er * 0.15 if face == 'worried' else 0) - (er * 0.2 if face == 'think' else 0)
            d.ellipse((px - pr, py - pr, px + pr, py + pr), fill='#1b1b1b')
    d.line((cx - ex + er, ey, cx + ex - er, ey), fill='#1b1b1b', width=max(3, int(size * 0.03)))
    # eyebrows
    bw2 = er * 1.1
    for sx in (-1, 1):
        gx = cx + sx * ex
        lift = {'shock': 0.55, 'worried': 0.35, 'smug': 0.1, 'think': 0.4}.get(face, 0.25)
        tilt = {'worried': -0.25, 'smug': 0.25 * sx * -1, 'think': 0.3 * sx}.get(face, 0)
        by = ey - er - size * lift * 0.18
        d.line((gx - bw2 / 2, by + tilt * er * sx, gx + bw2 / 2, by - tilt * er * sx), fill=dark, width=max(4, int(size * 0.04)))
    # mouth
    my = cy + size * 0.17
    mw = size * (0.16 if face in ('shock', 'worried') else 0.24)
    open_h = size * (0.04 + 0.16 * mouth) + (size * 0.08 if face == 'shock' else 0)
    if face == 'smug' and mouth < 0.15:
        d.arc((cx - mw / 2, my - size * 0.08, cx + mw / 2 + size * 0.05, my + size * 0.04), 10, 150, fill='#3a1408', width=max(3, int(size * 0.03)))
    elif face == 'worried' and mouth < 0.15:
        d.arc((cx - mw / 2, my, cx + mw / 2, my + size * 0.1), 200, 340, fill='#3a1408', width=max(3, int(size * 0.03)))
    else:
        d.rounded_rectangle((cx - mw / 2, my - open_h / 2, cx + mw / 2, my + open_h / 2), radius=int(open_h / 2), fill='#3a1408')
        if open_h > size * 0.08:
            d.ellipse((cx - mw * 0.25, my, cx + mw * 0.25, my + open_h / 2), fill='#ff6f7d')
    # bow tie
    ty = cy + size * 0.36
    tw = size * 0.11
    d.polygon([(cx, ty), (cx - tw, ty - tw * 0.6), (cx - tw, ty + tw * 0.6)], fill='#2457c5')
    d.polygon([(cx, ty), (cx + tw, ty - tw * 0.6), (cx + tw, ty + tw * 0.6)], fill='#2457c5')
    d.ellipse((cx - tw * 0.25, ty - tw * 0.25, cx + tw * 0.25, ty + tw * 0.25), fill='#173c8f')
    # facepalm hand
    if face == 'facepalm':
        hx, hy = cx + ex * 0.3, ey + er * 0.3
        d.ellipse((hx - er * 1.1, hy - er * 0.8, hx + er * 1.1, hy + er * 0.8), fill=body, outline=dark, width=max(3, int(size * 0.025)))
    img.alpha_composite(lay, (int(x - S / 2), int(y - S)))
    if name:
        from .draw import chip, font
        d2 = ImageDraw.Draw(img)
        chip(d2, x, y + 26, 'PROF. BOUNCE', font(theme['mono'], 22), theme['bg'], rgba(theme['accent']))


# ------------------------------------------------------------------ Prof. Bounce v2
def draw_prof2(img, x, y, size, theme, t, face='happy', mouth=0.0, look=0.0, speaking=False, name=True):
    """Prof. Bounce, second look: teal ball scientist with wild white hair, a bushy moustache, round gold
    glasses, a lab coat and arms that gesture. size = body diameter in px; feet at (x, y)."""
    S = int(size * 2.4)
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    body = theme.get('host2_body', '#36d6c3')
    dark = theme.get('host2_dark', '#14877b')
    ink = '#1d1430'
    w3 = max(3, int(size * 0.028))
    hop = abs(math.sin(t * 3.0)) * (0.5 if speaking else 1.0)
    sq = 1 + 0.05 * math.cos(t * 6.0)
    bw, bh = size * sq, size / sq
    cx, cy = S / 2, S - bh / 2 - 10 - hop * size * 0.08

    # shadow
    sw = bw * (0.85 - 0.2 * hop)
    d.ellipse((cx - sw / 2, S - 16, cx + sw / 2, S - 2), fill=(0, 0, 0, 110))

    # arms (behind the body), angles in degrees from straight down; positive = outwards
    wave = math.sin(t * 7.0) * (14 if speaking else 4)
    poses = {
        'happy': (35 + wave, 35 - wave), 'smug': (150, 30), 'shock': (155 + wave, 155 - wave),
        'worried': (20, 20), 'facepalm': (25, 165), 'think': (30, 140),
    }
    la, ra = poses.get(face, (35, 35))
    hand_r = size * 0.1
    for side, ang in ((-1, la), (1, ra)):
        sx, sy = cx + side * bw * 0.42, cy + bh * 0.08
        a = math.radians(ang)
        L = size * 0.42
        hx, hy = sx + side * math.sin(a) * L, sy + math.cos(a) * L
        if face == 'facepalm' and side == 1:
            hx, hy = cx + size * 0.12, cy - size * 0.12
        if face == 'think' and side == 1:
            hx, hy = cx + size * 0.18, cy + size * 0.22
        d.line((sx, sy, hx, hy), fill=theme.get('host2_coat', '#ffffff'), width=int(size * 0.13))
        d.line((sx, sy, hx, hy), fill=dark, width=max(2, int(size * 0.02)))
        d.ellipse((hx - hand_r, hy - hand_r, hx + hand_r, hy + hand_r), fill=body, outline=dark, width=w3)

    # body
    d.ellipse((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), fill=body, outline=dark, width=w3)
    d.ellipse((cx - bw * 0.36, cy - bh * 0.34, cx - bw * 0.2, cy - bh * 0.24), fill='#8ff0e4')

    # lab coat over the lower half, with lapels and a pen in the pocket
    coat = theme.get('host2_coat', '#ffffff')
    d.chord((cx - bw / 2 + w3, cy - bh / 2 + w3, cx + bw / 2 - w3, cy + bh / 2 - w3), 38, 142, fill=coat)
    ly = cy + bh * 0.3
    d.polygon([(cx, ly + bh * 0.18), (cx - bw * 0.14, ly), (cx - bw * 0.04, ly)], fill='#e6e1f2')
    d.polygon([(cx, ly + bh * 0.18), (cx + bw * 0.14, ly), (cx + bw * 0.04, ly)], fill='#e6e1f2')
    d.line((cx, ly + bh * 0.05, cx, cy + bh / 2 - w3), fill='#cfc8e3', width=max(2, int(size * 0.015)))
    px = cx + bw * 0.24
    d.rectangle((px - size * 0.06, ly + bh * 0.07, px + size * 0.06, ly + bh * 0.09), fill='#cfc8e3')
    d.line((px + size * 0.025, ly + bh * 0.0, px + size * 0.025, ly + bh * 0.08), fill='#ff4d6d', width=max(3, int(size * 0.03)))

    # wild white hair
    hair = '#f7f5ff'
    for k, (ox, oy, r) in enumerate(((-0.3, -0.5, 0.13), (-0.12, -0.6, 0.15), (0.08, -0.62, 0.15), (0.26, -0.54, 0.14), (0.4, -0.42, 0.11), (-0.43, -0.38, 0.1), (-0.5, -0.08, 0.09), (0.5, -0.08, 0.09))):
        jig = math.sin(t * 5 + k) * size * 0.008
        hx, hy, hr = cx + ox * bw, cy + oy * bh + jig, r * size
        d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=hair, outline='#d4cfe8', width=max(2, int(size * 0.015)))

    # eyes and glasses
    ey = cy - size * 0.14
    ex = size * 0.18
    er = size * 0.105
    blink = (t % 3.7) < 0.12 and face not in ('shock',)
    for sxn in (-1, 1):
        gx = cx + sxn * ex
        if blink or face == 'facepalm' and sxn == 1:
            d.line((gx - er * 0.7, ey, gx + er * 0.7, ey), fill=ink, width=w3)
        else:
            d.ellipse((gx - er, ey - er * 1.1, gx + er, ey + er * 1.1), fill='#ffffff')
            pr = er * (0.5 if face == 'shock' else 0.6)
            ppx = gx + look * er * 0.35
            ppy = ey + (er * 0.25 if face == 'worried' else 0) - (er * 0.3 if face == 'think' else 0)
            d.ellipse((ppx - pr, ppy - pr, ppx + pr, ppy + pr), fill=ink)
            d.ellipse((ppx - pr * 0.15 - pr * 0.3, ppy - pr * 0.55, ppx - pr * 0.15 + pr * 0.1, ppy - pr * 0.15), fill='#ffffff')
        gr = er * 1.3
        d.ellipse((gx - gr, ey - gr, gx + gr, ey + gr), outline=theme.get('host2_glasses', '#ffcc33'), width=w3)
    d.line((cx - ex + er * 1.3, ey, cx + ex - er * 1.3, ey), fill=theme.get('host2_glasses', '#ffcc33'), width=w3)
    # eyebrows (white, bushy)
    for sxn in (-1, 1):
        gx = cx + sxn * ex
        lift = {'shock': 0.62, 'worried': 0.42, 'think': 0.45}.get(face, 0.3)
        tilt = {'worried': -0.35 * sxn, 'smug': 0.3 * sxn, 'think': 0.35}.get(face, 0) * er
        by = ey - er * 1.3 - size * lift * 0.12
        d.line((gx - er, by + tilt, gx + er, by - tilt), fill=hair, width=max(5, int(size * 0.06)))

    # moustache, then the mouth under it
    ny = cy + size * 0.02
    d.ellipse((cx - size * 0.04, ny - size * 0.04, cx + size * 0.04, ny + size * 0.03), fill='#2a9e91')  # nose
    my = cy + size * 0.19
    mw = size * (0.13 if face in ('shock', 'worried') else 0.18)
    oh = size * (0.025 + 0.13 * mouth) + (size * 0.08 if face == 'shock' else 0)
    if face == 'smug' and mouth < 0.1:
        d.arc((cx - mw, my - size * 0.07, cx + mw, my + size * 0.05), 20, 160, fill='#4a1020', width=w3)
    elif face == 'worried' and mouth < 0.1:
        d.arc((cx - mw * 0.7, my, cx + mw * 0.7, my + size * 0.08), 200, 340, fill='#4a1020', width=w3)
    else:
        d.rounded_rectangle((cx - mw / 2, my - oh * 0.3, cx + mw / 2, my + oh), radius=int(max(1, oh / 2)), fill='#4a1020')
        if oh > size * 0.08:
            d.ellipse((cx - mw * 0.3, my + oh * 0.35, cx + mw * 0.3, my + oh), fill='#ff6f8b')
    lift = mouth * size * 0.02
    for sxn in (-1, 1):
        mx0 = cx + sxn * size * 0.1
        d.ellipse((mx0 - size * 0.12, ny + size * 0.03 - lift, mx0 + size * 0.12, ny + size * 0.12 - lift), fill=hair, outline='#d4cfe8', width=2)
    # blush
    for sxn in (-1, 1):
        bx = cx + sxn * size * 0.3
        d.ellipse((bx - size * 0.06, my - size * 0.06, bx + size * 0.06, my), fill='#f28ba6')

    if face in ('facepalm', 'think'):
        hx, hy = (cx + size * 0.14, cy - size * 0.12) if face == 'facepalm' else (cx + size * 0.12, cy + size * 0.28)
        d.ellipse((hx - hand_r * 1.2, hy - hand_r * 1.2, hx + hand_r * 1.2, hy + hand_r * 1.2), fill=body, outline=dark, width=w3)
    img.alpha_composite(lay, (int(x - S / 2), int(y - S)))
    if name:
        from .draw import chip, font
        d2 = ImageDraw.Draw(img)
        chip(d2, x, y + 24, 'PROF. BOUNCE', font(theme['mono'], 22), '#140a26', theme.get('host2_body', '#36d6c3'))
