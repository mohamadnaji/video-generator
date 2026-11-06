"""Turns a reel's story.py (scenes, lines, a draw function) into a voiced, captioned 1080x1920 mp4.

Voice and music come from the story kit (tools/story/storykit): kokoro TTS for lines, procedural
music beds and sound effects. A reel provides:

  STORY  dict: {'voices':…, 'music_level':…, 'scenes': [{'id', 'music', 'lines':[{'id','by','text','caption'}], 'lead', 'tail', 'min_dur'}]}
  SFX    list of (scene_id, at, name[, gain]); `at` is seconds or a line ref like "a.end+0.2"
  draw(img, scene_id, lt, ctx)   paints one frame (stage, labels, effects); captions and host are added after
  host(scene_id, lt, ctx)        -> None or dict(x, y, size, face, look)

and calls main(...) from its __main__.
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw

from .draw import FPS, H, W, caption

STORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'story'))
if STORY_DIR not in sys.path:
    sys.path.insert(0, STORY_DIR)
from storykit import audio, voice  # noqa: E402


def parse_at(at, lines):
    if isinstance(at, (int, float)):
        return float(at)
    m = re.fullmatch(r'\s*([\w-]+)(\.(start|end))?\s*([+-]\s*[\d.]+)?\s*', str(at))
    if not m or m.group(1) not in lines:
        raise ValueError(f'bad "at": {at!r} (line ids: {list(lines)})')
    ln = lines[m.group(1)]
    t = ln['end'] if m.group(3) == 'end' else ln['start']
    return t + (float(m.group(4).replace(' ', '')) if m.group(4) else 0.0)


class Ctx:
    """What a reel's draw/host functions get: theme, timing, and line lookups for the current scene."""

    def __init__(self, theme, timing):
        self.theme, self.timing = theme, timing
        self.scenes = {s['id']: s for s in timing['scenes']}

    def lines(self, scene_id):
        return {ln['id']: ln for ln in self.scenes[scene_id]['lines']}

    def at(self, scene_id, ref):
        return parse_at(ref, self.lines(scene_id))

    def dur(self, scene_id):
        return self.scenes[scene_id]['dur']


class Reel:
    def __init__(self, folder, story, theme, draw, host=None, sfx=(), caption_y=1545):
        self.folder, self.story, self.theme = folder, story, theme
        self.draw_fn, self.host_fn, self.sfx_list, self.caption_y = draw, host, list(sfx), caption_y
        self.out = os.path.join(folder, 'out')
        os.makedirs(self.out, exist_ok=True)
        self.timing = None

    # -------------------------------------------------------------- timeline
    def voice(self):
        self.timing = voice.speak(self.story, self.out)
        self.ctx = Ctx(self.theme, self.timing)
        for s in self.timing['scenes']:
            print(f"{s['id']:<10} start {s['start']:6.2f}  dur {s['dur']:5.2f}  lines {len(s['lines'])}")
        print(f"total {self.timing['total']:.2f} s")
        return self.timing

    def locate(self, t):
        for s in self.timing['scenes']:
            if t < s['start'] + s['dur']:
                return s, t - s['start']
        s = self.timing['scenes'][-1]
        return s, s['dur'] - 1e-3

    # -------------------------------------------------------------- frames
    def frame(self, t):
        sc, lt = self.locate(t)
        img = Image.new('RGBA', (W, H), self.theme['bg'])
        self.draw_fn(img, sc['id'], lt, self.ctx)
        speaking = next((ln for ln in sc['lines'] if ln['start'] <= lt < ln['end'] + 0.25), None)
        if self.host_fn:
            hs = self.host_fn(sc['id'], lt, self.ctx)
            if hs:
                from .host import draw_prof
                mouth = 0.0
                if speaking and speaking['by'] == 'host' and speaking['mouth'] and lt < speaking['end']:
                    k = int((lt - speaking['start']) * FPS)
                    mouth = speaking['mouth'][min(k, len(speaking['mouth']) - 1)]
                draw_prof(img, hs['x'], hs['y'], hs.get('size', 220), self.theme, t, face=hs.get('face', 'happy'),
                          mouth=mouth, look=hs.get('look', 0.0))
        if speaking:
            caption(ImageDraw.Draw(img), speaking, lt - speaking['start'], self.theme, self.caption_y)
        return img.convert('RGB')

    def sheet(self, times):
        if not times:
            n = 8
            times = [self.timing['total'] * (i + 0.5) / n for i in range(n)]
        cols, s = 4, 0.25
        tw, th = int(W * s), int(H * s)
        rows = (len(times) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * tw, rows * (th + 40)), '#222222')
        d = ImageDraw.Draw(sheet)
        for i, t in enumerate(times):
            fr = self.frame(t).resize((tw, th))
            x, y = (i % cols) * tw, (i // cols) * (th + 40)
            sheet.paste(fr, (x, y + 40))
            d.text((x + 8, y + 10), f'{t:.1f}s', fill='#ffffff')
        path = os.path.join(self.out, 'sheet.png')
        sheet.save(path)
        print(path)

    # -------------------------------------------------------------- video
    def sfx_events(self):
        out = []
        for item in self.sfx_list:
            sid, at, name = item[:3]
            gain = item[3] if len(item) > 3 else 1.0
            out.append((self.ctx.scenes[sid]['start'] + self.ctx.at(sid, at), name, gain))
        return out

    def video(self, name):
        audio.mix(self.story, self.timing, self.sfx_events(), self.out)
        path = os.path.join(self.out, f'{name}.mp4')
        n = int(self.timing['total'] * FPS)
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
               '-i', '-', '-i', os.path.join(self.out, 'mix.wav'), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
               '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(self.frame(i / FPS).tobytes())
            if i % (FPS * 5) == 0:
                print(f'frame {i}/{n}', flush=True)
        p.stdin.close()
        p.wait()
        print(path)


def main(reel, name):
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'sheet'
    reel.voice()
    if cmd == 'sheet':
        reel.sheet([float(a) for a in sys.argv[2:]])
    elif cmd == 'video':
        reel.video(name)
    elif cmd != 'voice':
        sys.exit('usage: story.py voice | sheet [secs…] | video')
