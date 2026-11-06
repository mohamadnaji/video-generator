"""Drawing helpers shared by every reel: fonts, colours, easing, captions, chips, banners."""
import subprocess
from functools import lru_cache

from PIL import ImageFont

W, H, FPS = 1080, 1920, 30


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def back_out(x, c=1.7):
    x = max(0.0, min(1.0, x))
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def rgba(h, a=1.0):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(255 * max(0.0, min(1.0, a))),)


@lru_cache(None)
def font(pattern, size):
    f = subprocess.run(['fc-match', '-f', '%{file}', pattern], capture_output=True, text=True).stdout.strip()
    return ImageFont.truetype(f, size) if f else ImageFont.load_default(size)


def text(d, xy, s, f, fill, anchor='mm', stroke=0, stroke_fill='#000000'):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def chip(d, x, y, s, f, fg, bg, anchor='mm', pad=(22, 12), radius=18, outline=None):
    """Rounded label. anchor: 'mm' centre, 'lm' left-middle, 'rm' right-middle."""
    l, t, r, b = d.textbbox((0, 0), s, font=f)
    w, h = r - l + pad[0] * 2, b - t + pad[1] * 2
    x0 = x - w / 2 if anchor == 'mm' else x if anchor == 'lm' else x - w
    d.rounded_rectangle((x0, y - h / 2, x0 + w, y + h / 2), radius, fill=bg, outline=outline, width=3 if outline else 0)
    d.text((x0 + w / 2, y), s, font=f, fill=fg, anchor='mm')
    return w, h


def wrap(d, words, f, max_w):
    """Greedy word wrap; returns lists of word indexes per line."""
    lines, cur, cur_w = [], [], 0
    space = d.textlength(' ', font=f)
    for i, w in enumerate(words):
        lw = d.textlength(w, font=f)
        if cur and cur_w + space + lw > max_w:
            lines.append(cur)
            cur, cur_w = [], 0
        cur_w += (space if cur else 0) + lw
        cur.append(i)
    if cur:
        lines.append(cur)
    return lines


def caption(d, line, lt, theme, y, max_w=W - 100, size=66):
    """Karaoke caption: words light up as they are spoken. `line` comes from timing.json."""
    words = [w for w, _, _ in line['words']]
    f = font(theme['display'], size)
    rows = wrap(d, words, f, max_w)
    lh = size * 1.18
    top = y - lh * (len(rows) - 1) / 2
    space = d.textlength(' ', font=f)
    for r, row in enumerate(rows):
        widths = [d.textlength(words[i], font=f) for i in row]
        x = W / 2 - (sum(widths) + space * (len(row) - 1)) / 2
        for i, wdt in zip(row, widths):
            _, a, b = line['words'][i]
            said = lt >= a
            fill = theme['caption_hi'] if a <= lt < b + 0.05 else theme['caption'] if said else rgba(theme['caption'], 0.55)
            d.text((x, top + r * lh), words[i], font=f, fill=fill, anchor='lm', stroke_width=6, stroke_fill=theme['stroke'])
            x += wdt + space
