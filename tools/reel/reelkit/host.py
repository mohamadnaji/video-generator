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
