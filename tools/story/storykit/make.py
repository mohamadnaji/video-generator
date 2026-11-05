"""Story video CLI (run from tools/story):

    python -m storykit.make stories/<name> voice          # speak lines -> out/timing.json (prints scene lengths)
    python -m storykit.make stories/<name> assets         # render missing 3D sets/poses/props (cached)
    python -m storykit.make stories/<name> sheet [t ...]  # contact sheet at global seconds -> out/sheet.png
    python -m storykit.make stories/<name> video          # full render -> out/<name>.mp4
    python -m storykit.make stories/<name> all            # voice + assets + video
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

from . import compose, render3d, voice, audio

WORKERS = int(os.environ.get('STORY_WORKERS', os.cpu_count() or 2))


def load(sdir):
    story = json.load(open(os.path.join(sdir, 'story.json')))
    story.setdefault('name', os.path.basename(os.path.normpath(sdir)))
    out = os.path.join(sdir, 'out')
    os.makedirs(out, exist_ok=True)
    return story, out


def timing_of(story, out):
    p = os.path.join(out, 'timing.json')
    if not os.path.exists(p):
        return voice.speak(story, out)
    return json.load(open(p))


def renderer(story, out):
    return compose.Renderer(story, timing_of(story, out))


def assets(story, out):
    R = renderer(story, out)
    jobs = []
    for i in range(len(story['scenes'])):
        jobs += R.scene(i).jobs()
    uniq = {render3d.key(j): j for j in jobs}
    todo = [j for j in uniq.values() if not os.path.exists(render3d.paths(j)[0])]
    print(f'3D assets: {len(uniq)} needed, {len(todo)} to render', flush=True)
    # sets are slow: give each its own worker slot first
    render3d.ensure(sorted(todo, key=lambda j: j['kind'] != 'set'), workers=WORKERS, log=os.path.join(out, 'render3d.log'))


def find(R, story, gt):
    for i, st in enumerate(R.timing['scenes']):
        if st['start'] <= gt < st['start'] + st['dur'] or i == len(story['scenes']) - 1:
            return i, min(gt - st['start'], st['dur'] - 1e-3)


def sheet(story, out, times):
    from PIL import Image, ImageDraw
    R = renderer(story, out)
    if not times:
        times = []
        for st in R.timing['scenes']:
            times.append(round(st['start'] + st['dur'] * 0.55, 2))
    ims = []
    for gt in times:
        i, t = find(R, story, gt)
        im = R.frame(R.scene(i), t).resize((270, 480))
        ImageDraw.Draw(im).text((8, 6), f'{gt:.1f}s {story["scenes"][i]["id"]}', fill=(255, 0, 255))
        ims.append(im)
    cols = min(6, len(ims))
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (cols * 270, rows * 480), 'white')
    for k, im in enumerate(ims):
        sh.paste(im, ((k % cols) * 270, (k // cols) * 480))
    p = os.path.join(out, 'sheet.png')
    sh.save(p)
    print(p)


def _render_scene(args):
    sdir, i = args
    story, out = load(sdir)
    R = renderer(story, out)
    S = R.scene(i)
    n = int(round(S.dur * compose.FPS))
    path = os.path.join(out, f'scene{i:02d}.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s',
                          f'{compose.W}x{compose.H}', '-r', str(compose.FPS), '-i', '-', '-c:v', 'libx264', '-preset',
                          'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(R.frame(S, f / compose.FPS).tobytes())
    p.stdin.close()
    p.wait()
    return path, [(S.st['start'] + t, name, g) for (t, name, g) in S.sfx]


def video(story, out, sdir):
    R = renderer(story, out)
    n = len(story['scenes'])
    with ProcessPoolExecutor(WORKERS) as ex:
        res = list(ex.map(_render_scene, [(sdir, i) for i in range(n)]))
    sfx = [e for _, evs in res for e in evs]
    audio.mix(story, R.timing, sfx, out)
    lst = os.path.join(out, 'list.txt')
    open(lst, 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p, _ in res))
    final = os.path.join(out, f"{story['name']}.mp4")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i',
                    os.path.join(out, 'mix.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a',
                    '192k', '-shortest', '-movflags', '+faststart', final], check=True)
    print(final, f"{R.timing['total']:.1f}s")


def main():
    sdir, cmd = sys.argv[1], sys.argv[2]
    story, out = load(sdir)
    if cmd in ('voice', 'all'):
        t = voice.speak(story, out)
        for s in t['scenes']:
            print(f"{s['id']}: {s['dur']:.2f}s")
        print(f"total {t['total']:.1f}s")
    if cmd in ('assets', 'all', 'video', 'sheet'):
        assets(story, out)
    if cmd == 'sheet':
        sheet(story, out, [float(x) for x in sys.argv[3:]])
    if cmd in ('video', 'all'):
        video(story, out, sdir)


if __name__ == '__main__':
    main()
