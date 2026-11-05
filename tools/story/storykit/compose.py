"""Turn story.json + timing.json + cached 3D renders into 1080x1920 frames.
Plate space = the 3D set render (1296x2304); the camera crops it. Screen space = the final frame."""
import json
import math
import os
import random
import re
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import render3d

W, H, FPS = 1080, 1920, 30
CYCLES = {'run': 4, 'walk': 4}


# ------------------------------------------------------------------ small helpers
def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def back_out(x, c=1.7):
    x = max(0.0, min(1.0, x))
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def rgba(h, a=1.0):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    al = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(255 * a * al),)


@lru_cache(None)
def font(kind, size):
    pats = {'bold': ['Inter Display:Black', 'DejaVu Sans:Bold'], 'semi': ['Inter Display:ExtraBold', 'DejaVu Sans:Bold'],
            'italic': ['Inter:Bold:Italic', 'DejaVu Sans:Bold:Oblique'], 'mono': ['DejaVu Sans Mono:Bold'],
            'serif': ['DejaVu Serif:Bold']}[kind]
    for p in pats:
        try:
            f = subprocess.run(['fc-match', '-f', '%{file}', p], capture_output=True, text=True).stdout.strip()
            if f:
                return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default(size)


def parse_at(at, lines):
    """12.5 | "a" | "a.end" | "a+0.3" | "a.end-0.2" -> seconds within the scene."""
    if isinstance(at, (int, float)):
        return float(at)
    m = re.fullmatch(r'\s*([\w-]+)(\.(start|end))?\s*([+-]\s*[\d.]+)?\s*', str(at))
    if not m or m.group(1) not in lines:
        raise ValueError(f'bad "at": {at!r} (line ids: {list(lines)})')
    ln = lines[m.group(1)]
    t = ln['end'] if m.group(3) == 'end' else ln['start']
    return t + (float(m.group(4).replace(' ', '')) if m.group(4) else 0.0)


# ------------------------------------------------------------------ scene state
class Track:
    """A property timeline: initial value, then (t, value, dur) changes with smooth tweens."""

    def __init__(self, v0):
        self.v0, self.keys = v0, []

    def add(self, t, v, dur=0.0):
        self.keys.append((t, v, dur))
        self.keys.sort(key=lambda k: k[0])

    def at(self, t):
        v = self.v0
        for (t0, nv, d) in self.keys:
            if t < t0:
                break
            if d > 0 and t < t0 + d and isinstance(nv, (int, float)) and isinstance(v, (int, float)):
                return v + (nv - v) * ease((t - t0) / d)
            v = nv
        return v

    def last_change(self, t):
        lc = None
        for (t0, _, _) in self.keys:
            if t0 <= t:
                lc = t0
        return lc


class Scene:
    def __init__(self, story, sc, st):
        self.sc, self.st, self.story = sc, st, story
        self.dur = st['dur']
        self.lines = {ln['id']: ln for ln in st['lines']}
        hdef = dict(story.get('host', {}))
        hdef.update(sc.get('host', {}))
        self.host = {k: Track(v) for k, v in dict(
            pose=hdef.get('pose', 'stand'), face=hdef.get('face', 'neutral'), props=tuple(hdef.get('props', [])),
            x=hdef.get('x', 0.5), y=hdef.get('y', 0.0), scale=hdef.get('scale', 1.0), dir=hdef.get('dir', 'right'),
            visible=not hdef.get('hidden', False)).items()}
        self.objs = {}
        for o in sc.get('objects', []):
            self.objs[o['id']] = dict(spec=o, tr={k: Track(v) for k, v in dict(
                x=o.get('x', 0.75), y=o.get('y', 0.0), scale=o.get('scale', 1.0), dir=o.get('dir', 'right'),
                visible=not o.get('hidden', False), args=json.dumps(o.get('args', {}), sort_keys=True)).items()})
        self.cam = {k: Track(v) for k, v in dict(zoom=1.0, fx=None, fy=None).items()}
        self.fx, self.texts, self.sfx = [], [], []
        enter = sc.get('enter', 'cut')
        if enter in ('flash', 'whip'):
            self.fx.append(dict(fx='flash', t=0, dur=0.22))
            self.sfx.append((0.0, 'whoosh', 0.8))
        elif enter == 'fade':
            self.fx.append(dict(fx='fadein', t=0, dur=0.35))
        if sc.get('card'):
            self._event(dict(sc['card'], do='card', at=sc['card'].get('at', 0)))
        for ev in sc.get('events', []):
            self._event(ev)

    def _target(self, name):
        if name in (None, 'host'):
            return self.host
        return self.objs[name]['tr']

    def _event(self, ev):
        t = parse_at(ev.get('at', 0), self.lines)
        d, do = ev.get('dur', 0.0), ev['do']
        tr = self._target(ev.get('target'))
        if do == 'pose':
            for k in ('pose', 'face', 'dir'):
                if k in ev:
                    self.host[k].add(t, ev[k])
            if 'props' in ev:
                self.host['props'].add(t, tuple(ev['props']))
        elif do == 'face':
            self.host['face'].add(t, ev['face'])
        elif do == 'props':
            tr['props'].add(t, tuple(ev['props']))
        elif do == 'move':
            for k in ('x', 'y'):
                if k in ev:
                    tr[k].add(t, ev[k], ev.get('dur', 0.6))
            if 'dir' in ev:
                tr['dir'].add(t, ev['dir'])
        elif do in ('grow', 'scale'):
            tr['scale'].add(t, ev['scale'], ev.get('dur', 0.6))
        elif do == 'show':
            tr['visible'].add(t, True)
            self.fx.append(dict(fx='popin', t=t, dur=0.3, target=ev.get('target')))
        elif do == 'hide':
            tr['visible'].add(t, False)
        elif do == 'swap':  # change a prop's builder args (e.g. legs on the bomb)
            tr['args'].add(t, json.dumps(ev['args'], sort_keys=True))
        elif do == 'camera':
            self.cam['zoom'].add(t, ev.get('zoom', 1.0), ev.get('dur', 0.4))
            self.cam['fx'].add(t, ev.get('focus', None))
        elif do == 'sfx':
            self.sfx.append((t, ev['name'], ev.get('gain', 1.0)))
        elif do in ('banner', 'tag', 'card'):
            self.texts.append(dict(ev, t=t, dur=ev.get('dur', 1.5 if do != 'card' else self.dur - t)))
        elif do == 'fx':
            self.fx.append(dict(ev, t=t, dur=ev.get('dur', 1.0)))
            if ev['fx'] == 'explosion':
                self.sfx.append((t, 'boom', 1.0))
        else:
            raise ValueError(f'unknown event do={do!r}')
        if ev.get('sfx'):
            self.sfx.append((t, ev['sfx'], 1.0))

    # ---------------------------------------------------------- 3D jobs this scene needs
    def host_job(self, t):
        pose = self.host['pose'].at(t)
        if pose in CYCLES:
            pose = f'{pose}{int(t * 10) % CYCLES[pose]}'
        return dict(kind='host', pose=pose, face=self.host['face'].at(t), props=sorted(self.host['props'].at(t)))

    def obj_job(self, oid, t):
        o = self.objs[oid]
        args = json.loads(o['tr']['args'].at(t))
        n = o['spec'].get('frames', 0)
        if n:
            args['frame'] = int(t * 10) % n
        return dict(kind='prop', name=o['spec']['prop'], args=args)

    def set_job(self):
        return dict(kind='set', name=self.sc.get('set', 'studio'), tone=self.sc.get('tone'), color=self.sc.get('color'))

    def jobs(self):
        out = [self.set_job()]
        for t in np.arange(0, self.dur, 0.1):
            out.append(self.host_job(t))
            for oid in self.objs:
                out.append(self.obj_job(oid, t))
        return out


# ------------------------------------------------------------------ assets
@lru_cache(None)
def load(jobkey_json):
    job = json.loads(jobkey_json)
    png, meta = render3d.paths(job)
    return Image.open(png).convert('RGBA'), json.load(open(meta))


@lru_cache(512)
def scaled(jobkey_json, s, flip):
    im, meta = load(jobkey_json)
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    im = im.resize((w, h), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


@lru_cache(8)
def shadow(w):
    w = max(8, int(w))
    im = Image.new('L', (w * 2, w // 2), 0)
    ImageDraw.Draw(im).ellipse([w * 0.5, w * 0.1, w * 1.5, w * 0.4], fill=120)
    im = im.filter(ImageFilter.GaussianBlur(w * 0.06))
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.putalpha(im)
    return out


# ------------------------------------------------------------------ drawing
class Renderer:
    def __init__(self, story, timing):
        self.story, self.timing = story, timing
        self.style = dict(accent='#ffd23f', caption_bg='#0b0b12cc', caption_fg='#ffffff', narrator_bg='#1a1033cc',
                          narrator_fg='#e9ddff', header_fg='#ffffff', labels=False)
        self.style.update(story.get('style', {}))

    def scene(self, i):
        return Scene(self.story, self.story['scenes'][i], self.timing['scenes'][i])

    def place_sprite(self, canvas, job, x_frac, y_units, scale, flip, plate_meta, pop=1.0, bob=0.0):
        im, meta = load(json.dumps(job, sort_keys=True))
        s = plate_meta['plate_ppu'] / meta['ppu'] * scale * pop
        s = round(s, 3)
        spr = scaled(json.dumps(job, sort_keys=True), s, flip)
        ox, oy = meta['origin']
        if flip:
            ox = im.width - ox
        gx = x_frac * plate_meta['size'][0]
        gy = plate_meta['ground'][1] - y_units * plate_meta['plate_ppu'] - bob
        if y_units < 0.05:
            sh = shadow(im.width * s * 0.6)
            canvas.alpha_composite(sh, (int(gx - sh.width / 2), int(plate_meta['ground'][1] - sh.height / 2)))
        dx, dy = int(round(gx - ox * s)), int(round(gy - oy * s))
        canvas.alpha_composite(spr, (dx, dy))

        def to_plate(p):
            px = (im.width - p[0]) if flip else p[0]
            return dx + px * s, dy + p[1] * s
        return meta, to_plate, s

    def mouth(self, canvas, meta, to_plate, s, open_amt, shape):
        a = meta['anchors']
        mx, my = to_plate(a['mouth'])
        rx, _ = to_plate(a['mouth_r'])
        w = max(10.0, abs(rx - mx) * 2.0)
        k = 4
        pw, ph = int(w * 1.6), int(w * 1.4)
        im = Image.new('RGBA', (pw * k, ph * k), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx, cy = pw * k / 2, ph * k / 2
        ww = w * k / 2
        ink = (60, 22, 22, 255)
        lw = max(3, int(w * k * 0.07))
        if open_amt > 0.12:
            hh = ww * (0.25 + 0.75 * open_amt)
            d.ellipse([cx - ww * 0.8, cy - hh * 0.5, cx + ww * 0.8, cy + hh * 0.9], fill=ink)
            d.ellipse([cx - ww * 0.45, cy + hh * 0.25, cx + ww * 0.45, cy + hh * 0.85], fill=(220, 90, 100, 255))
            d.rectangle([cx - ww * 0.55, cy - hh * 0.5, cx + ww * 0.55, cy - hh * 0.3], fill=(250, 250, 250, 255))
        elif shape == 'grin':
            d.chord([cx - ww * 0.8, cy - ww * 0.7, cx + ww * 0.8, cy + ww * 0.6], 0, 180, fill=ink)
            d.rectangle([cx - ww * 0.62, cy - ww * 0.08, cx + ww * 0.62, cy + ww * 0.05], fill=(250, 250, 250, 255))
        elif shape == 'frown':
            d.arc([cx - ww * 0.6, cy, cx + ww * 0.6, cy + ww * 0.9], 200, 340, fill=ink, width=lw)
        elif shape == 'flat':
            d.line([cx - ww * 0.45, cy, cx + ww * 0.45, cy], fill=ink, width=lw)
        elif shape == 'o':
            d.ellipse([cx - ww * 0.3, cy - ww * 0.35, cx + ww * 0.3, cy + ww * 0.45], fill=ink)
        elif shape == 'wavy':
            pts = [(cx - ww * 0.5 + i * ww * 0.25, cy + (ww * 0.08 if i % 2 else -ww * 0.08)) for i in range(5)]
            d.line(pts, fill=ink, width=lw, joint='curve')
        elif shape == 'smirk':
            d.arc([cx - ww * 0.5, cy - ww * 0.6, cx + ww * 0.7, cy + ww * 0.3], 20, 120, fill=ink, width=lw)
        else:  # smile
            d.arc([cx - ww * 0.6, cy - ww * 0.75, cx + ww * 0.6, cy + ww * 0.35], 25, 155, fill=ink, width=lw)
        im = im.resize((pw, ph), Image.LANCZOS)
        canvas.alpha_composite(im, (int(mx - pw / 2), int(my - ph / 2)))

    # ---------------------------------------------------------- one frame
    def frame(self, S, t):
        sc, story = S.sc, self.story
        set_im, pm = load(json.dumps(S.set_job(), sort_keys=True))
        canvas = set_im.copy()
        PW, PH = pm['size']
        talk = self.speaking(S, t)
        items = []
        for oid, o in S.objs.items():
            tr = o['tr']
            if tr['visible'].at(t):
                items.append(('obj', oid, o['spec'].get('z', 0)))
        if S.host['visible'].at(t):
            items.append(('host', 'host', sc.get('host', {}).get('z', 0.5)))
        items.sort(key=lambda it: it[2])
        host_face = None
        for kind, oid, _ in items:
            tr = S.host if kind == 'host' else S.objs[oid]['tr']
            pop = 1.0
            for f in S.fx:
                if f['fx'] == 'popin' and (f.get('target') or 'host') == oid and f['t'] <= t < f['t'] + f['dur']:
                    pop = max(0.05, back_out((t - f['t']) / f['dur']))
            if kind == 'host':
                job = S.host_job(t)
                lc = S.host['pose'].last_change(t)
                if lc is not None and t - lc < 0.15:
                    pop *= 1 + 0.05 * (1 - (t - lc) / 0.15)
                bob = 3 * math.sin(t * 2.4) + 9 * talk
                meta, to_plate, s = self.place_sprite(canvas, job, tr['x'].at(t), tr['y'].at(t), tr['scale'].at(t),
                                                      tr['dir'].at(t) == 'left', pm, pop, bob)
                if 'anchors' in meta:
                    self.mouth(canvas, meta, to_plate, s, talk, meta.get('mouth_face', 'smile'))
                    host_face = to_plate(meta['anchors']['head'])
            else:
                spec = S.objs[oid]['spec']
                bob = 0.0
                if spec.get('anim') == 'bob':
                    bob = 14 * math.sin(t * 3)
                sc_ = tr['scale'].at(t) * (1 + 0.04 * math.sin(t * 12) if spec.get('anim') == 'pulse' else 1)
                x = tr['x'].at(t) + (random.Random(int(t * 30)).uniform(-0.006, 0.006) if spec.get('anim') == 'shake' else 0)
                self.place_sprite(canvas, S.obj_job(oid, t), x, tr['y'].at(t), sc_, tr['dir'].at(t) == 'left', pm, pop, bob)

        # camera
        u = t / max(S.dur, 0.01)
        preset = sc.get('camera', 'drift')
        z, cx, cy = 1.0, PW / 2, PH * 0.5
        hx = S.host['x'].at(t) * PW
        if preset == 'push_in':
            z = 1.0 + 0.16 * ease(u)
            cx = PW / 2 + (hx - PW / 2) * 0.4 * ease(u)
        elif preset == 'pull_out':
            z = 1.18 - 0.18 * ease(u)
        elif preset == 'pan_left':
            z, cx = 1.12, PW / 2 + PW * 0.05 * (1 - 2 * u)
        elif preset == 'pan_right':
            z, cx = 1.12, PW / 2 - PW * 0.05 * (1 - 2 * u)
        elif preset == 'drift':
            z = 1.03 + 0.03 * u
        ez = S.cam['zoom'].at(t)
        focus = S.cam['fx'].at(t)
        if ez != 1.0 or focus:
            z = z * ez if focus is None else max(z, ez)
            fpt = None
            if focus == 'host' and host_face:
                fpt = host_face
            elif focus in S.objs:
                fpt = (S.objs[focus]['tr']['x'].at(t) * PW, pm['ground'][1] - 1.0 * pm['plate_ppu'])
            if fpt:
                k = min(1.0, (ez - 1) / 0.6) if ez > 1 else 0
                cx = cx + (fpt[0] - cx) * k
                cy = cy + (fpt[1] - cy) * k
        shake = 0
        for f in S.fx:
            if f['fx'] in ('shake', 'explosion') and f['t'] <= t < f['t'] + f['dur']:
                shake = max(shake, f.get('amp', 28) * (1 - (t - f['t']) / f['dur']))
        if shake:
            r = random.Random(int(t * 30))
            cx += r.uniform(-shake, shake)
            cy += r.uniform(-shake, shake)
        cw, ch = PW / z, PH / z
        cx = min(max(cx, cw / 2), PW - cw / 2)
        cy = min(max(cy, ch / 2), PH - ch / 2)
        out = canvas.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        out = out.convert('RGBA')
        self.overlays(out, S, t)
        return out.convert('RGB')

    def speaking(self, S, t):
        for ln in S.st['lines']:
            if ln['by'] == 'host' and ln['mouth'] and ln['start'] <= t < ln['end']:
                i = int((t - ln['start']) * FPS)
                return ln['mouth'][min(i, len(ln['mouth']) - 1)]
        return 0.0

    # ---------------------------------------------------------- screen overlays
    def overlays(self, out, S, t):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for f in S.fx:
            if f['t'] <= t < f['t'] + f['dur'] or f['fx'] in ('dim',) and t >= f['t']:
                self.effect(lay, d, f, t - f['t'], S, t)
        hd = S.sc.get('header')
        if hd:
            self.header(d, hd, t)
        for tx in S.texts:
            if tx['t'] <= t < tx['t'] + tx['dur']:
                getattr(self, tx['do'])(lay, d, tx, t - tx['t'])
        self.caption(lay, d, S, t)
        out.alpha_composite(lay)
        for f in S.fx:
            if f['fx'] in ('flash', 'fadein') and f['t'] <= t < f['t'] + f['dur']:
                a = 1 - (t - f['t']) / f['dur']
                col = (255, 255, 255) if f['fx'] == 'flash' else (0, 0, 0)
                out.alpha_composite(Image.new('RGBA', (W, H), col + (int(255 * a),)))

    def effect(self, lay, d, f, lt, S, t):
        kind = f['fx']
        if kind == 'speed_lines':
            r = random.Random(7)
            sign = -1 if f.get('dir', 'left') == 'left' else 1
            for i in range(26):
                y = r.uniform(380, 1500)
                ln = r.uniform(140, 420)
                sp = r.uniform(2200, 3600)
                x = (r.uniform(0, 3000) + lt * sp) % (W + 900) - 450
                x = x if sign > 0 else W - x
                d.line([x, y, x - sign * ln, y], fill=(255, 255, 255, 110), width=int(r.uniform(4, 10)))
        elif kind == 'rain':
            r = random.Random(3)
            for i in range(140):
                x = r.uniform(0, W)
                y = (r.uniform(0, H) + lt * 1800) % H
                d.line([x, y, x - 8, y + 34], fill=(170, 200, 255, 120), width=3)
        elif kind == 'confetti':
            r = random.Random(5)
            for i in range(120):
                x = (r.uniform(0, W) + math.sin(lt * 3 + i) * 40)
                y = -50 + (r.uniform(0, 600) + lt * r.uniform(500, 900)) % (H + 100)
                c = r.choice(['#ff4d6d', '#ffd23f', '#3ddc97', '#4cc9f0', '#b388ff'])
                s = r.uniform(10, 20)
                d.rectangle([x, y, x + s, y + s * 0.5], fill=rgba(c))
        elif kind == 'explosion':
            k = lt / f['dur']
            x, y = f.get('x', 0.5) * W, f.get('y', 0.45) * H
            R = 200 + 900 * ease(min(1, k * 2.5))
            a = int(255 * (1 - k))
            for rr, c in ((R, '#ff6a2b'), (R * 0.7, '#ffb703'), (R * 0.4, '#fff3b0')):
                pts = [(x + math.cos(i * math.pi / 9) * rr * (1 if i % 2 else 0.6),
                        y + math.sin(i * math.pi / 9) * rr * (1 if i % 2 else 0.6)) for i in range(18)]
                d.polygon(pts, fill=rgba(c, a / 255))
            if k < 0.25:
                d.rectangle([0, 0, W, H], fill=(255, 255, 230, int(200 * (1 - k * 4))))
        elif kind == 'dim':
            a = f.get('level', 0.6) * ease(lt / max(0.01, f['dur']))
            g = Image.radial_gradient('L').resize((W, H)).point(lambda v: int(min(255, v * 1.3 * a)))
            black = Image.new('RGBA', (W, H), (0, 0, 0, 255))
            black.putalpha(g)
            lay.alpha_composite(black)
        elif kind == 'spark':
            pass

    def header(self, d, hd, t):
        st = self.style
        k = back_out(t / 0.35)
        if hd.get('title'):
            f = font('bold', int(118 * (0.7 + 0.3 * k)))
            d.text((W / 2, 205), hd['title'], font=f, fill=rgba(st['header_fg']), anchor='mm',
                   stroke_width=8, stroke_fill=(0, 0, 0, 200))
        m = hd.get('meter')
        if m:
            p = m['from'] + (m['to'] - m['from']) * ease((t - 0.3) / 0.7)
            x0, y0, w, h = 130, 292, W - 260, 44
            d.rounded_rectangle([x0, y0, x0 + w, y0 + h], h / 2, fill=(0, 0, 0, 140))
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(max(0, p) / 100 * 0.33, 0.85, 0.95)
            if p > 0.5:
                d.rounded_rectangle([x0 + 5, y0 + 5, x0 + 5 + max(h - 10, (w - 10) * p / 100), y0 + h - 5], (h - 10) / 2,
                                    fill=(int(r * 255), int(g * 255), int(b * 255), 255))
            d.text((W / 2, y0 + h + 42), f"{m.get('label', '')}: {int(round(p))}{m.get('unit', '%')}", font=font('mono', 38),
                   fill=(255, 255, 255, 235), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0, 180))
        if hd.get('subtitle'):
            d.text((W / 2, 300 if not m else 410), hd['subtitle'], font=font('semi', 46), fill=(255, 255, 255, 230),
                   anchor='mm', stroke_width=5, stroke_fill=(0, 0, 0, 170))

    def banner(self, lay, d, ev, lt):
        k = back_out(lt / 0.25)
        a = 1 - ease((lt - (ev['dur'] - 0.2)) / 0.2)
        f = font('bold', ev.get('size', 120))
        tw = int(d.textlength(ev['text'], font=f)) + 80
        im = Image.new('RGBA', (tw, int(ev.get('size', 120) * 1.7)), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((tw / 2, im.height / 2), ev['text'], font=f, anchor='mm', fill=rgba(ev.get('color', self.style['accent']), a),
                                stroke_width=10, stroke_fill=(0, 0, 0, int(230 * a)))
        pulse = 1 + 0.04 * math.sin(lt * 14)
        im = im.resize((max(1, int(im.width * k * pulse)), max(1, int(im.height * k * pulse))), Image.BILINEAR)
        im = im.rotate(ev.get('angle', -6), expand=True, resample=Image.BICUBIC)
        y = ev.get('y', 0.3) * H
        lay.alpha_composite(im, (int(W / 2 - im.width / 2), int(y - im.height / 2)))

    def tag(self, lay, d, ev, lt):
        a = ease(lt / 0.2) * (1 - ease((lt - (ev['dur'] - 0.2)) / 0.2))
        f = font('mono' if ev.get('mono', True) else 'semi', ev.get('size', 42))
        x, y = ev.get('x', 0.5) * W, ev.get('y', 0.4) * H
        tw = d.textlength(ev['text'], font=f)
        pad = 20
        d.rounded_rectangle([x - tw / 2 - pad, y - 36, x + tw / 2 + pad, y + 36], 14, fill=(0, 0, 0, int(190 * a)))
        d.text((x, y), ev['text'], font=f, fill=rgba(ev.get('color', '#ffffff'), a), anchor='mm')

    def card(self, lay, d, ev, lt):
        k = back_out(lt / 0.45)
        a = ease(lt / 0.3) * (1 - ease((lt - (ev['dur'] - 0.25)) / 0.25))
        y = ev.get('y', 0.25) * H
        if ev.get('kicker'):
            d.text((W / 2, y - 150), ev['kicker'], font=font('mono', 40), fill=rgba(self.style['accent'], a), anchor='mm',
                   stroke_width=4, stroke_fill=(0, 0, 0, int(160 * a)))
        f = font('bold', int(ev.get('size', 120) * (0.8 + 0.2 * k)))
        lines = ev['title'].split('\n')
        for i, ln in enumerate(lines):
            d.text((W / 2, y + i * ev.get('size', 120) * 1.02), ln, font=f, anchor='mm', fill=(255, 255, 255, int(255 * a)),
                   stroke_width=10, stroke_fill=(0, 0, 0, int(220 * a)))
        if ev.get('subtitle') and lt > 0.4:
            b = back_out((lt - 0.4) / 0.35)
            yy = y + len(lines) * ev.get('size', 120) * 1.02 + 40
            f2 = font('bold', int(74 * b) + 1)
            tw = d.textlength(ev['subtitle'], font=f2)
            d.rounded_rectangle([W / 2 - tw / 2 - 40, yy - 62, W / 2 + tw / 2 + 40, yy + 62], 22, fill=rgba(self.style['accent'], a))
            d.text((W / 2, yy), ev['subtitle'], font=f2, anchor='mm', fill=(20, 20, 20, int(255 * a)))

    def caption(self, lay, d, S, t):
        st = self.style
        for ln in S.st['lines']:
            if not (ln['start'] - 0.05 <= t < ln['end'] + 0.35) or not ln['caption']:
                continue
            narr = ln['by'] != 'host'
            f = font('italic' if narr else 'bold', 64 if not narr else 58)
            lt = t - ln['start']
            # wrap words
            rows, cur, wcur = [], [], 0
            sp = d.textlength(' ', font=f)
            for w in ln['words']:
                ww = d.textlength(w[0], font=f)
                if cur and wcur + sp + ww > W - 190:
                    rows.append(cur)
                    cur, wcur = [], 0
                cur.append((w, ww))
                wcur += (sp if len(cur) > 1 else 0) + ww
            rows.append(cur)
            lh = 80 if not narr else 74
            bh = len(rows) * lh + 56
            y0 = 1640 - bh / 2
            pop = back_out((lt + 0.05) / 0.22)
            bw = max(sum(x[1] for x in r) + sp * (len(r) - 1) for r in rows) + 90
            bw *= pop
            d.rounded_rectangle([W / 2 - bw / 2, y0, W / 2 + bw / 2, y0 + bh], 30, fill=rgba(st['narrator_bg' if narr else 'caption_bg']))
            if st.get('labels') or narr:
                lab = (ln['by'].upper() if narr else st.get('host_name', 'HOST').upper())
                lf = font('mono', 30)
                lw = d.textlength(lab, font=lf)
                d.rounded_rectangle([W / 2 - lw / 2 - 16, y0 - 26, W / 2 + lw / 2 + 16, y0 + 18], 10, fill=rgba(st['accent']))
                d.text((W / 2, y0 - 4), lab, font=lf, fill=(20, 20, 20, 255), anchor='mm')
            y = y0 + 28 + lh / 2
            for r in rows:
                tw = sum(x[1] for x in r) + sp * (len(r) - 1)
                x = W / 2 - tw / 2
                for (w, ww) in r:
                    on = w[1] <= lt < w[2] + 0.05
                    col = st['accent'] if on else (st['narrator_fg'] if narr else st['caption_fg'])
                    d.text((x, y), w[0], font=f, fill=rgba(col), anchor='lm', stroke_width=3 if not narr else 0,
                           stroke_fill=(0, 0, 0, 200))
                    x += ww + sp
                y += lh
            break
