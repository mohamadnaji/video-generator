"""Render 3D sprites (host poses, props) and set plates, cached by spec.

    python -m storykit.render3d jobs.json      # list of job dicts, run in its own process (bpy)

Job kinds:
  {"kind": "host", "pose": "stand", "face": "happy", "props": ["helmet"]}
  {"kind": "prop", "name": "bomb", "args": {"legs": true, "frame": 2}}
  {"kind": "set",  "name": "park", "tone": "day", "color": null}
Each output is <cache>/<key>.png plus <key>.json (anchors, px_per_unit). Sprites are 400 px per world unit.
"""
import hashlib
import json
import os
import sys

PPU = 400            # sprite pixels per world unit
PLATE = (1296, 2304)  # 1.2x of 1080x1920, room for camera moves
VERSION = 4          # bump to invalidate the cache after changing the 3D builders
CACHE = os.environ.get('STORY_CACHE', os.path.join(os.path.dirname(__file__), '..', 'cache'))


def key(job):
    s = json.dumps(job, sort_keys=True) + f'v{VERSION}'
    k = job.get('name') or job.get('pose') or 'x'
    return f"{job['kind']}_{k}_{hashlib.md5(s.encode()).hexdigest()[:10]}"


def paths(job):
    k = key(job)
    return os.path.join(CACHE, k + '.png'), os.path.join(CACHE, k + '.json')


def _bbox():
    import bpy
    from mathutils import Vector
    bpy.context.view_layer.update()
    xs, zs = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            w = oe.matrix_world @ Vector(c)
            xs.append(w.x)
            zs.append(w.z)
    return min(xs), max(xs), min(zs), max(zs)


def _sprite_camera(margin=0.08):
    import bpy
    from .blib import cycles
    x0, x1, z0, z1 = _bbox()
    x0, x1, z0, z1 = x0 - margin, x1 + margin, min(z0, 0) - margin, z1 + margin
    w, h = x1 - x0, z1 - z0
    pw, ph = int(round(w * PPU)), int(round(h * PPU))
    cycles(samples=20, w=pw, h=ph, transparent=True)
    cd = bpy.data.cameras.new('cam')
    cd.type = 'ORTHO'
    cd.ortho_scale = max(w, h)
    cam = bpy.data.objects.new('cam', cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = ((x0 + x1) / 2, -30, (z0 + z1) / 2)
    cam.rotation_euler = (1.5707963, 0, 0)
    bpy.context.scene.camera = cam
    return cam


def run(job):
    import bpy
    from . import blib, host, props, sets
    png, meta = paths(job)
    if os.path.exists(png) and os.path.exists(meta):
        return
    blib.reset()
    info = {'job': job, 'ppu': PPU}
    if job['kind'] == 'host':
        root = host.build(job.get('pose', 'stand'), job.get('face', 'neutral'), job.get('props', []))
        blib.lights(energy=1.0)
        blib.world_color('#9aa4b5', strength=0.6)
        cam = _sprite_camera()
        a = host.anchors(root)
        info['anchors'] = {k: blib.project(cam, v) for k, v in a.items()}
        info['mouth_face'] = host.MOUTH.get(job.get('face', 'neutral'), 'smile')
    elif job['kind'] == 'prop':
        props.PROPS[job['name']](**job.get('args', {}))
        blib.lights(energy=1.0)
        blib.world_color('#9aa4b5', strength=0.6)
        cam = _sprite_camera()
    else:
        sets.SETS[job['name']](**{k: v for k, v in (('tone', job.get('tone')), ('color', job.get('color'))) if v})
        blib.cycles(samples=job.get('samples', 28), w=PLATE[0], h=PLATE[1], transparent=False)
        cd = bpy.data.cameras.new('cam')
        cd.lens = 34
        cd.sensor_fit = 'VERTICAL'
        cd.sensor_height = 36
        cam = bpy.data.objects.new('cam', cd)
        bpy.context.scene.collection.objects.link(cam)
        cam.location = (0, -6.2, 1.5)
        blib.look_at(cam, (0, 0, 1.2))
        bpy.context.scene.camera = cam
        g0 = blib.project(cam, (0, 0, 0))
        g1 = blib.project(cam, (1, 0, 0))
        info['ground'] = g0
        info['plate_ppu'] = g1[0] - g0[0]
    info['origin'] = blib.project(cam, (0, 0, 0))
    blib.render(png)
    info['size'] = [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y]
    json.dump(info, open(meta, 'w'), indent=1)


def ensure(jobs, workers=2, log=None):
    """Render every missing job in child processes (bpy state stays isolated)."""
    import subprocess
    os.makedirs(CACHE, exist_ok=True)
    todo = [j for j in jobs if not all(os.path.exists(p) for p in paths(j))]
    uniq = {key(j): j for j in todo}
    todo = list(uniq.values())
    if not todo:
        return
    chunks = [todo[i::workers] for i in range(workers)]
    procs = []
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for i, ch in enumerate(chunks):
        if not ch:
            continue
        jf = os.path.join(CACHE, f'_jobs{i}.json')
        json.dump(ch, open(jf, 'w'))
        out = open(log or os.devnull, 'a')
        procs.append(subprocess.Popen([sys.executable, '-m', 'storykit.render3d', jf], cwd=here, stdout=out, stderr=out))
    for p in procs:
        p.wait()
    missing = [key(j) for j in todo if not os.path.exists(paths(j)[0])]
    if missing:
        raise SystemExit(f'3D render failed for: {missing} (see log)')


if __name__ == '__main__':
    for j in json.load(open(sys.argv[1])):
        run(j)
        print('done', key(j), flush=True)
