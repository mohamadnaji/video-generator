"""SpendSense TikTok: "Mission 8: Black Friday" (GTA 6-style sequel to "The Down Payment").

usage: python3 render.py <workdir> [frames t1 t2 ...]
Needs <workdir>/scenes/s1..s5.png, <workdir>/logo.png, <workdir>/bf_audio.wav
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps

W, H, FPS = 1080, 1920, 30
WORK = sys.argv[1]
FD = '/mnt/skills/examples/canvas-design/canvas-fonts/'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
def F(name, s): return ImageFont.truetype(FD + name, s)
HUD = lambda s: F('BigShoulders-Bold.ttf', s)
UI = lambda s: F('InstrumentSans-Bold.ttf', s)
UIR = lambda s: F('InstrumentSans-Regular.ttf', s)

GREEN = (114, 222, 120); RED = (236, 64, 64); WHITE = (255, 255, 255); YELLOW = (255, 214, 72)
PINK = (255, 92, 170); TEAL = (94, 214, 178); BLACK = (0, 0, 0); GOLD = (255, 196, 60)

# timeline
T1, T2, T3, T4, T5, T6, T7, END = 0.0, 2.4, 8.4, 11.4, 12.6, 19.2, 22.2, 25.2
START_MONEY = 1240
BUYS = [(3.0, '75" TV', 899), (4.2, 'Console bundle', 599), (5.4, 'Headphones', 249), (6.6, 'Sneakers', 180)]

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def back(x):
    x = max(0.0, min(1.0, x)); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------- images ----------
def cover_fit(im, scale=1.0):
    im = im.convert('RGB'); sw, sh = im.size
    s = max(W / sw, H / sh) * scale
    return im.resize((int(sw * s), int(sh * s)), Image.LANCZOS)

SCN = {}
def load_scenes():
    for k in ['s1', 's2', 's3', 's4', 's5']:
        SCN[k] = cover_fit(Image.open(os.path.join(WORK, 'scenes', k + '.png')), 1.12)

def kenburns(key, p, zoom=(1.0, 1.08), focus=(0.5, 0.45)):
    big = SCN[key]; bw, bh = big.size
    z = zoom[0] + (zoom[1] - zoom[0]) * p
    cw, ch = W / z * (bw / (W * 1.12)) * 1.12 / 1.12, H / z * (bh / (H * 1.12)) * 1.12 / 1.12
    cw, ch = bw / 1.12 / z, bh / 1.12 / z
    cx = focus[0] * bw; cy = focus[1] * bh
    x0 = min(max(0, cx - cw / 2), bw - cw); y0 = min(max(0, cy - ch / 2), bh - ch)
    return big.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)

def vignette(img, strength=0.55):
    if 'vig' not in SCN:
        m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
        d.ellipse((-300, -200, W + 300, H + 200), fill=255)
        SCN['vig'] = m.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new('RGB', (W, H), (0, 0, 0))
    return Image.composite(img, Image.blend(img, dark, strength), SCN['vig'])

# ---------- text helpers ----------
def stroke_text(d, xy, s, f, fill, sw=6, anchor='mm', shadow=True):
    if shadow:
        d.text((xy[0] + 5, xy[1] + 7), s, font=f, fill=(0, 0, 0, 150), anchor=anchor, stroke_width=sw, stroke_fill=(0, 0, 0, 150))
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=BLACK)

def star(d, cx, cy, r, fill, outline=BLACK):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline, width=4)

_em = {}
def emoji(ch, size):
    if (ch, size) not in _em:
        f = ImageFont.truetype(EMOJI, 109); im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor='mm')
        _em[(ch, size)] = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
    return _em[(ch, size)]

# ---------- HUD ----------
def hud(base, money, stars, flash=0.0, t=0.0, label=None):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    # minimap
    cx, cy, r = 150, 215, 92
    d.ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), fill=(0, 0, 0, 200))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(28, 46, 40, 235), outline=(110, 200, 120), width=5)
    for k in (-40, 0, 40):
        d.line((cx - r + 15, cy + k, cx + r - 15, cy + k), fill=(70, 110, 90), width=3)
        d.line((cx + k, cy - r + 15, cx + k, cy + r - 15), fill=(70, 110, 90), width=3)
    d.polygon([(cx, cy - 18), (cx - 12, cy + 14), (cx + 12, cy + 14)], fill=WHITE)
    # money
    col = GREEN if money >= 0 else RED
    if money < 0 and int(t * 6) % 2 == 0: col = (255, 140, 140)
    s = ('-$' if money < 0 else '$') + f'{abs(int(round(money))):,}'
    stroke_text(d, (1010, 170), s, HUD(112), col, sw=7, anchor='rm')
    # stars
    for i in range(5):
        x = 1010 - 38 - (4 - i) * 72
        on = i < stars
        fill = WHITE if on else (60, 60, 60, 200)
        if on and flash > 0 and int(t * 8) % 2 == 0: fill = (255, 90, 90)
        star(d, x, 262, 30, fill)
    if label:
        stroke_text(d, (1010, 318), label, UI(30), WHITE, sw=3, anchor='rm', shadow=False)
    base.alpha_composite(L)

def banner(base, top, title, p, colors=((255, 74, 160), (255, 150, 60)), y=520, sub_col=BLACK):
    a = back(p)
    if p <= 0: return
    L = Image.new('RGBA', (W + 400, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    grad = Image.new('RGBA', (W + 400, 250))
    gd = ImageDraw.Draw(grad)
    for x in range(W + 400):
        k = x / (W + 400); c = tuple(int(colors[0][i] * (1 - k) + colors[1][i] * k) for i in range(3))
        gd.line((x, 0, x, 250), fill=c + (255,))
    L.paste(grad, (0, 40))
    d.text((300, 92), top, font=HUD(64), fill=sub_col, anchor='lm')
    stroke_text(d, (290, 190), title, HUD(150), WHITE, sw=7, anchor='lm')
    L = L.rotate(5, resample=Image.BICUBIC, expand=True)
    x = int(-200 + (1 - a) * -1200)
    base.alpha_composite(L, (x, y - L.size[1] // 2))

def caption(base, who, text, col, p, y=1330, hl=None):
    """Speaker line, word-wrapped to fit the screen; `hl` words are drawn yellow."""
    if p <= 0: return
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    f = UI(54); maxw = W - 140
    words = [(who + ':', col)] + [(w_, YELLOW if hl and w_.strip('.,!?…') == hl else WHITE) for w_ in text.split()]
    lines, cur, cw = [], [], 0
    sp = d.textlength(' ', font=f)
    for w_, c in words:
        ww = d.textlength(w_, font=f)
        if cur and cw + sp + ww > maxw:
            lines.append((cur, cw)); cur, cw = [], 0
        cw = cw + (sp if cur else 0) + ww; cur.append((w_, c, ww))
    lines.append((cur, cw))
    y0 = y - (len(lines) - 1) * 34
    for li, (ln, lw) in enumerate(lines):
        x = (W - lw) / 2; yy = y0 + li * 68
        for w_, c, ww in ln:
            d.text((x + 3, yy + 4), w_, font=f, fill=(0, 0, 0, 200), anchor='lm', stroke_width=6, stroke_fill=(0, 0, 0, 200))
            d.text((x, yy), w_, font=f, fill=c, anchor='lm', stroke_width=4, stroke_fill=BLACK)
            x += ww + sp
    a = min(1, p / 0.12)
    if a < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(L)

def pickup(base, name, amt, p, idx):
    if p <= 0 or p > 1.0: return
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    y = 400 + idx * 0 - 60 * ease(p / 0.8)
    a = 1 if p < 0.7 else max(0, 1 - (p - 0.7) / 0.3)
    stroke_text(d, (1010, y + 30), f'-${amt:,}', HUD(84), RED, sw=6, anchor='rm')
    stroke_text(d, (1010, y + 105), name.upper(), HUD(52), WHITE, sw=5, anchor='rm')
    if a < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(L)

# ---------- Sense chat card ----------
def chat(base, t):
    """t: seconds into the Sense scene (0..6.6)."""
    x0, y0, x1, y1 = 120, 900, 960, 1560
    pin = ease(t / 0.35)
    if pin <= 0: return
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle((x0 + 6, y0 + 16, x1 + 6, y1 + 16), 48, fill=(0, 0, 0, 120))
    d.rounded_rectangle((x0, y0, x1, y1), 48, fill=(20, 24, 30, 240), outline=(60, 70, 80), width=3)
    lg = SCN['logo'].resize((64, 64), Image.LANCZOS); L.alpha_composite(lg, (x0 + 36, y0 + 30))
    d.text((x0 + 118, y0 + 50), 'Sense', font=UI(40), fill=WHITE, anchor='lm')
    d.text((x0 + 118, y0 + 88), 'SpendSense AI', font=UIR(26), fill=(150, 158, 168), anchor='lm')
    d.line((x0 + 30, y0 + 128, x1 - 30, y0 + 128), fill=(50, 56, 66), width=2)

    def user(y, text, st):
        if t < st: return
        k = ease((t - st) / 0.25); f = UI(36)
        tw = d.textlength(text, font=f); bw = tw + 60
        bx1 = x1 - 36; bx0 = bx1 - bw
        d.rounded_rectangle((bx0, y, bx1, y + 74), 30, fill=(24, 120, 96, int(255 * k)))
        d.text((bx0 + 30, y + 37), text, font=f, fill=(255, 255, 255, int(255 * k)), anchor='lm')

    def sense(y, lines, st, color_first=GREEN):
        if t < st: return
        k = ease((t - st) / 0.25)
        if t - st < 0.45:  # typing dots
            d.rounded_rectangle((x0 + 36, y, x0 + 170, y + 70), 30, fill=(40, 46, 56, int(255 * k)))
            for i in range(3):
                on = int((t - st) * 10 + i) % 3 == 0
                d.ellipse((x0 + 66 + i * 30 - 8, y + 27, x0 + 66 + i * 30 + 8, y + 43), fill=(220, 220, 220) if on else (120, 120, 120))
            return
        f1, f2 = UI(38), UIR(32)
        h = 30 + 50 + 44 * (len(lines) - 1) + 26
        d.rounded_rectangle((x0 + 36, y, x1 - 70, y + h), 30, fill=(40, 46, 56))
        d.text((x0 + 66, y + 48), lines[0], font=f1, fill=color_first, anchor='lm')
        for i, ln in enumerate(lines[1:]):
            d.text((x0 + 66, y + 98 + i * 44), ln, font=f2, fill=(225, 228, 232), anchor='lm')

    user(y0 + 160, '🎙️ "Can we afford the TV?"'.replace('🎙️ ', ''), 0.35)
    sense(y0 + 256, ['Yes. $899 fits.', '$341 left after bills & savings.'], 0.75)
    user(y0 + 420, '"And the console?"', 3.1)
    sense(y0 + 516, ['Not this month.', 'Save $150/mo → yours by March 🎯'.replace(' 🎯', '')], 3.45, color_first=YELLOW)
    if pin < 1:
        L = L.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, -(1 - pin) * 200), resample=Image.BILINEAR)
        L.putalpha(L.getchannel('A').point(lambda v: int(v * pin)))
    base.alpha_composite(L)

# ---------- scenes ----------
def frame(t):
    if t < T2:                                   # hook
        p = t / (T2 - T1)
        img = vignette(kenburns('s1', p, (1.0, 1.06), (0.5, 0.42)), 0.35)
        b = img.convert('RGBA')
        hud(b, START_MONEY, 0, t=t)
        banner(b, 'MISSION 8', 'BLACK FRIDAY', t / 0.4)
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        if t > 0.5:
            stroke_text(d, (W / 2, 1350), 'OBJECTIVE: SHOP.', HUD(92), WHITE, sw=6)
            stroke_text(d, (W / 2, 1450), "DON'T GET WASTED.", HUD(92), YELLOW, sw=6)
        b.alpha_composite(L)
        return b
    if t < T3:                                   # spree
        lt = t - T2; p = lt / (T3 - T2)
        img = vignette(kenburns('s2', p, (1.0, 1.12), (0.45, 0.5)), 0.35)
        # quick punch-in on each purchase
        b = img.convert('RGBA')
        spent = 0; stars = 0
        for i, (bt, name, amt) in enumerate(BUYS):
            if t >= bt:
                k = ease((t - bt) / 0.35); spent += amt * k; stars = i + 1
        money = START_MONEY - spent
        hud(b, money, stars, flash=1 if money < 0 else 0, t=t)
        for i, (bt, name, amt) in enumerate(BUYS):
            pickup(b, name, amt, (t - bt) / 1.1, i)
        if 2.4 <= t < 4.9:
            caption(b, 'THEO', "It's 40% off. We're basically SAVING money.", (120, 200, 255), t - 2.5, hl='SAVING')
        elif t >= 5.0 and t < 7.3:
            caption(b, 'MIA', 'Babe… this was NOT on the list.', PINK, t - 5.0, hl='NOT')
        elif t >= 7.3:
            caption(b, 'MIA', '…and rent is due Monday.', PINK, t - 7.3, hl='rent')
        return b
    if t < T4:                                   # WASTED
        lt = t - T3; p = lt / (T4 - T3)
        img = kenburns('s3', p, (1.04, 1.12), (0.5, 0.5))
        g = ImageOps.grayscale(img).convert('RGB')
        g = ImageEnhance.Contrast(g).enhance(1.1)
        mix = min(1, lt / 0.5)
        img = Image.blend(img, g, mix)
        img = Image.blend(img, Image.new('RGB', (W, H), (0, 0, 0)), 0.25 * mix)
        b = img.convert('RGBA')
        if lt > 0.25:
            L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
            band_a = int(170 * min(1, (lt - 0.25) / 0.3))
            d.rectangle((0, 800, W, 1080), fill=(0, 0, 0, band_a))
            s = 1 + 0.25 * (1 - ease((lt - 0.25) / 0.5))
            f = HUD(int(230 * s))
            stroke_text(d, (W / 2, 940), 'WASTED', f, (196, 34, 34), sw=8)
            if lt > 1.0:
                stroke_text(d, (W / 2, 1180), 'RENT DUE MONDAY: -$687', HUD(70), WHITE, sw=5)
            b.alpha_composite(L)
        hud(b, START_MONEY - 1927, 4, flash=1, t=t)
        return b
    if t < T5:                                   # rewind
        lt = t - T4; p = lt / (T5 - T4)
        src = 's2' if p < 0.6 else 's1'
        img = kenburns(src, 1 - p, (1.0, 1.12), (0.45, 0.5))
        # VHS look: colour split + scanlines + shake
        r, g_, bl = img.split()
        r = r.transform((W, H), Image.AFFINE, (1, 0, -12, 0, 1, 0)); bl = bl.transform((W, H), Image.AFFINE, (1, 0, 12, 0, 1, 0))
        img = Image.merge('RGB', (r, g_, bl))
        img = Image.blend(img, Image.new('RGB', (W, H), (40, 20, 70)), 0.25)
        b = img.convert('RGBA')
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        off = int(t * 900) % 12
        for y in range(off, H, 12): d.line((0, y, W, y), fill=(0, 0, 0, 60), width=3)
        stroke_text(d, (W / 2, 900), '◀◀  RETRY MISSION', HUD(110), WHITE, sw=7)
        stroke_text(d, (W / 2, 1020), 'this time, ask Sense first', UI(50), TEAL, sw=4)
        b.alpha_composite(L)
        return b
    if t < T6:                                   # Sense
        lt = t - T5; p = lt / (T6 - T5)
        img = vignette(kenburns('s4', p, (1.0, 1.07), (0.5, 0.38)), 0.35)
        b = img.convert('RGBA')
        k = ease((lt - 1.3) / 0.6) if lt > 1.3 else 0
        money = START_MONEY - 899 * k
        hud(b, money, 0, t=t)
        chat(b, lt)
        return b
    if t < T7:                                   # MISSION PASSED
        lt = t - T6; p = lt / (T7 - T6)
        img = vignette(kenburns('s5', p, (1.0, 1.06), (0.5, 0.5)), 0.3)
        b = img.convert('RGBA')
        hud(b, START_MONEY - 899, 0, t=t)
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        if lt > 0.05:
            band = int(150 * min(1, lt / 0.3))
            d.rectangle((0, 1180, W, 1560), fill=(0, 0, 0, band))
            s = 1 + 0.3 * (1 - ease(lt / 0.4))
            stroke_text(d, (W / 2, 1300), 'MISSION PASSED', HUD(int(150 * s)), GOLD, sw=8)
        if lt > 0.6:
            stroke_text(d, (W / 2, 1430), 'TV BOUGHT · RENT PAID · 0 STARS', HUD(62), WHITE, sw=5)
        b.alpha_composite(L)
        return b
    # end card over blurred living room
    lt = t - T7
    if 'endbg' not in SCN:
        bg = kenburns('s5', 1.0, (1.06, 1.06), (0.5, 0.5)).filter(ImageFilter.GaussianBlur(28))
        SCN['endbg'] = Image.blend(bg, Image.new('RGB', (W, H), (10, 12, 16)), 0.62)
    b = SCN['endbg'].copy().convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    a = back(lt / 0.45)
    lg = SCN['logo'].resize((240, 240), Image.LANCZOS); L.alpha_composite(lg, (W // 2 - 120, 560))
    f = F('BricolageGrotesque-Bold.ttf', 120)
    w1 = d.textlength('Spend', font=f); w2 = d.textlength('Sense', font=f); x = (W - w1 - w2) / 2
    d.text((x, 940), 'Spend', font=f, fill=WHITE, anchor='lm'); d.text((x + w1, 940), 'Sense', font=f, fill=TEAL, anchor='lm')
    d.text((W / 2, 1060), 'Ask Sense before you buy.', font=UI(54), fill=WHITE, anchor='mm')
    d.text((W / 2, 1150), 'spendsense.app', font=F('BricolageGrotesque-Bold.ttf', 70), fill=(240, 192, 90), anchor='mm')
    if lt < 0.45:
        sc = 0.9 + 0.1 * a
        L = L.resize((int(W * sc), int(H * sc)), Image.BICUBIC)
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0)); c.paste(L, ((W - L.size[0]) // 2, (H - L.size[1]) // 2)); L = c
        L.putalpha(L.getchannel('A').point(lambda v: int(v * min(1, lt / 0.2))))
    b.alpha_composite(L)
    return b

def flashcut(img, t):
    """White flash on hard cuts."""
    for c in (T2, T3, T5, T6):
        if 0 <= t - c < 0.12:
            k = 1 - (t - c) / 0.12
            img = Image.blend(img, Image.new('RGB', (W, H), (255, 255, 255)), 0.55 * k)
    return img

def render_frame(t):
    return flashcut(frame(t).convert('RGB'), t)

def main():
    load_scenes()
    SCN['logo'] = Image.open(os.path.join(WORK, 'logo.png')).convert('RGBA')
    if len(sys.argv) > 2 and sys.argv[2] == 'frames':
        for s in sys.argv[3:]:
            render_frame(float(s)).save(os.path.join(WORK, f'bf_{s}.jpg'), quality=88)
        return
    n = int(END * FPS)
    tmp = os.path.join(WORK, 'bf_video.tmp.mp4')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
                          '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(render_frame(i / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, os.path.join(WORK, 'bf_video.mp4'))
    print('frames', n)

if __name__ == '__main__':
    main()
