"""The recurring host ("Ollie"): built from primitives, posed by joint angles (runs inside bpy).

Pose angles are degrees. Arms/legs: 'out' swings sideways (away from the body, 180 = straight up),
'fwd' swings toward the character's front. Elbows/knees use the same two axes, relative to the parent.
facing: 0 = looks at camera, 90 = profile looking screen-right (compositor mirrors for left).
"""
from .blib import (R, mat, empty, sphere, box, cyl, cone, torus, cut_sphere, limb)

LOOK = dict(skin='#f2c29b', shirt='#1f9e89', pants='#2b3a67', shoe='#f4f1ea', sole='#d64545',
            hair='#3b2416', glasses='#1b1b1f', eye='#ffffff', pupil='#151515', brow='#2a1a10')

# ----------------------------------------------------------------------------- poses
_ST = dict(facing=12, spine=0, head=0,
           a_sh=(8, 0), a_el=(0, 10), b_sh=(8, 0), b_el=(0, 10),
           a_hip=(4, 0), a_kn=(0, 0), b_hip=(4, 0), b_kn=(0, 0), lift=0.0)


def P(**kw):
    p = dict(_ST)
    p.update(kw)
    return p


def _run(i, n=4):
    import math
    ph = i / n * 2 * math.pi
    s = math.sin(ph)
    return P(facing=90, spine=-12, head=6,
             a_sh=(0, 55 * s), a_el=(0, 85), b_sh=(0, -55 * s), b_el=(0, 85),
             a_hip=(0, 45 * -s), a_kn=(0, -(30 + 45 * max(0, s))), b_hip=(0, 45 * s), b_kn=(0, -(30 + 45 * max(0, -s))),
             lift=0.06 * abs(math.cos(ph)))


def _walk(i, n=4):
    import math
    s = math.sin(i / n * 2 * math.pi)
    return P(facing=90, spine=-3, a_sh=(0, 22 * s), a_el=(0, 20), b_sh=(0, -22 * s), b_el=(0, 20),
             a_hip=(0, 22 * -s), a_kn=(0, -12 * max(0, s)), b_hip=(0, 22 * s), b_kn=(0, -12 * max(0, -s)))


POSES = {
    'stand': P(),
    'talk': P(b_sh=(28, 30), b_el=(0, 70)),
    'explain': P(a_sh=(30, 25), a_el=(0, 60), b_sh=(30, 25), b_el=(0, 60)),
    'point': P(facing=25, b_sh=(85, 10), b_el=(0, 5)),
    'point_up': P(b_sh=(165, 0), b_el=(0, 0), head=-6),
    'proud': P(a_sh=(40, -10), a_el=(-95, 0), b_sh=(40, -10), b_el=(-95, 0), head=-5),
    'shrug': P(a_sh=(35, 0), a_el=(-100, 30), b_sh=(35, 0), b_el=(-100, 30), head=8),
    'think': P(b_sh=(15, 35), b_el=(0, 140), head=10, a_sh=(20, 30), a_el=(0, 80)),
    'phone': P(b_sh=(15, 20), b_el=(0, 150), head=6),
    'cheer': P(a_sh=(160, 0), a_el=(10, 0), b_sh=(160, 0), b_el=(10, 0), head=-8),
    'scared': P(a_sh=(120, 20), a_el=(60, 0), b_sh=(120, 20), b_el=(60, 0), spine=6, a_hip=(10, 0), b_hip=(10, 0)),
    'facepalm': P(b_sh=(20, 40), b_el=(0, 150), head=14, spine=8),
    'wave': P(b_sh=(130, 0), b_el=(40, 0)),
    'sit': P(facing=35, a_hip=(0, 88), a_kn=(0, -88), b_hip=(0, 88), b_kn=(0, -88), spine=6, head=12,
             a_sh=(5, 25), a_el=(0, 40), b_sh=(5, 25), b_el=(0, 40), lift=-0.42),
    'flail': P(a_sh=(150, 30), a_el=(40, 0), b_sh=(140, -30), b_el=(-30, 0), a_hip=(25, 10), b_hip=(5, -15), head=-10),
}
for _i in range(4):
    POSES[f'run{_i}'] = _run(_i)
    POSES[f'walk{_i}'] = _walk(_i)

FACES = {  # brow angle (deg, + = inner end up), brow height, eye openness, pupil offset
    'neutral': (0, 0.0, 1.0, (0, 0)), 'happy': (8, 0.02, 0.85, (0, 0)), 'serious': (-12, -0.01, 0.9, (0, 0)),
    'angry': (-25, -0.02, 0.8, (0, 0)), 'worried': (22, 0.01, 1.0, (0, 0.01)), 'sad': (25, -0.01, 0.6, (0, -0.012)),
    'shock': (5, 0.05, 1.35, (0, 0)), 'smug': (-6, 0.0, 0.55, (0.012, 0)),
}
MOUTH = {'neutral': 'smile', 'happy': 'grin', 'serious': 'flat', 'angry': 'frown', 'worried': 'wavy',
         'sad': 'frown', 'shock': 'o', 'smug': 'smirk'}

PROPS = ['helmet', 'hardhat', 'jacket', 'red_shoes', 'phone', 'sunglasses', 'soot', 'cape', 'crown', 'book', 'sign',
         'labcoat', 'tie', 'backpack']


# ----------------------------------------------------------------------------- build
def build(pose='stand', face='neutral', props=()):
    p = POSES[pose] if isinstance(pose, str) else pose
    props = set(props)
    L = dict(LOOK)
    if 'soot' in props:
        L['skin'], L['shirt'] = '#8c6a55', '#3d4a45'
    m = {k: mat(v, 0.5) for k, v in L.items()}
    if 'red_shoes' in props:
        m['shoe'] = mat('#e8322f', 0.4)
        m['sole'] = mat('#ffffff', 0.5)

    root = empty((0, 0, 0.0 + p['lift']), (0, 0, R(p['facing'])), name='root')
    hips = empty((0, 0, 0.92), (R(p['spine']), 0, 0), parent=root, name='hips')
    # pelvis + torso
    sphere((0, 0, 0.02), 1, m['pants'], scale=(0.22, 0.17, 0.12), parent=hips)
    torso_m = mat('#f4f4f2', 0.6) if 'labcoat' in props else m['shirt']
    sphere((0, 0, 0.27), 1, torso_m, scale=(0.24, 0.185, 0.3), parent=hips)
    if 'jacket' in props:
        for i, c in enumerate(['#2e6bd9', '#f39c1d', '#1fae6b']):
            torus((0, 0, 0.12 + i * 0.15), 0.215 - i * 0.012, 0.075, mat(c, 0.45), parent=hips)
    if 'tie' in props:
        box((0, -0.18, 0.36), (0.05, 0.02, 0.22), mat('#c0392b', 0.4), rot=(R(-8), 0, 0), parent=hips)
    if 'cape' in props:
        box((0, 0.22, 0.12), (0.46, 0.02, 0.75), mat('#c0392b', 0.5), rot=(R(8), 0, 0), parent=hips, bevel=0.01)
    if 'backpack' in props:
        box((0, 0.24, 0.3), (0.32, 0.16, 0.38), mat('#e67e22', 0.5), parent=hips, bevel=0.05)

    neck = empty((0, 0, 0.56), (R(p['head']), 0, 0), parent=hips, name='neck')
    _head(neck, m, face, props)

    # arms (a = screen-left, b = screen-right when facing camera)
    for side, sh, el in (('a', p['a_sh'], p['a_el']), ('b', p['b_sh'], p['b_el'])):
        sx = -1 if side == 'a' else 1
        sleeve = torso_m if 'labcoat' in props else m['shirt']
        if 'jacket' in props:
            sleeve = mat('#2e6bd9', 0.45)
        j = empty((sx * 0.27, 0, 0.47), (R(-sh[1]), R(-sx * sh[0]), 0), parent=hips, name=f'{side}_sh')
        sphere((0, 0, 0), 0.085, sleeve, parent=j)
        e = limb(j, 0.3, 0.075, sleeve, name=f'{side}_el')
        e.rotation_euler = (R(-el[1]), R(-sx * el[0]), 0)
        h = limb(e, 0.27, 0.062, m['skin'], name=f'{side}_hand')
        sphere((0, 0, -0.02), 0.075, m['skin'], parent=h)
        if side == 'b' and 'phone' in props:
            box((0, -0.05, 0.02), (0.07, 0.015, 0.14), mat('#1a1a1a', 0.3), parent=h, bevel=0.01)
            box((0, -0.06, 0.02), (0.058, 0.004, 0.12), mat('#6fd3ff', 0.2, emit=1.5), parent=h)
        if side == 'b' and 'book' in props:
            box((0.02, -0.08, -0.04), (0.2, 0.05, 0.26), mat('#8e44ad', 0.5), parent=h, bevel=0.01)
        if side == 'b' and 'sign' in props:
            cyl((0, 0, 0.25), 0.015, 0.7, mat('#8b5a2b', 0.6), parent=h)
            box((0, -0.02, 0.62), (0.6, 0.03, 0.38), mat('#fbf6e9', 0.6), parent=h, bevel=0.01)

    # legs
    for side, hp, kn in (('a', p['a_hip'], p['a_kn']), ('b', p['b_hip'], p['b_kn'])):
        sx = -1 if side == 'a' else 1
        j = empty((sx * 0.11, 0, 0.0), (R(-hp[1]), R(-sx * hp[0]), 0), parent=hips, name=f'{side}_hip')
        k = limb(j, 0.42, 0.09, m['pants'], name=f'{side}_kn')
        k.rotation_euler = (R(-kn[1]), R(-sx * kn[0]), 0)
        f = limb(k, 0.4, 0.08, m['pants'], name=f'{side}_ft')
        # shoe: sole + upper, pointing forward (-Y)
        sphere((0, -0.07, -0.02), 1, m['shoe'], scale=(0.095, 0.16, 0.075), parent=f)
        sphere((0, -0.07, -0.065), 1, m['sole'], scale=(0.1, 0.165, 0.03), parent=f)
    return root


def _head(neck, m, face, props):
    brow_a, brow_h, eye_open, pup = FACES.get(face, FACES['neutral'])
    head = empty((0, 0, 0.34), parent=neck, name='head')
    sphere((0, 0, 0), 0.34, m['skin'], scale=(1, 0.95, 1.0), parent=head)
    for sx in (-1, 1):
        sphere((sx * 0.33, 0, -0.02), 0.07, m['skin'], scale=(0.6, 1, 1), parent=head)  # ears
    sphere((0, -0.33, -0.03), 0.055, m['skin'], parent=head)  # nose
    # hair: a cap tilted back, plus a front tuft
    hair_m = m['hair']
    if 'soot' in props:
        for k in range(9):
            a = -60 + k * 15
            cone((0.33 * __import__('math').sin(R(a)), 0.03, 0.3 * __import__('math').cos(R(a)) + 0.05), 0.07, 0.0, 0.3,
                 hair_m, rot=(0, R(a), 0), parent=head)
    else:
        cut_sphere((0, 0.03, 0.03), 0.355, hair_m, keep_above=0.42, rot=(R(38), 0, 0), parent=head)
        sphere((-0.06, -0.2, 0.27), 1, hair_m, scale=(0.17, 0.1, 0.07), rot=None, parent=head) if False else sphere((-0.06, -0.2, 0.27), 1, hair_m, scale=(0.17, 0.1, 0.07), parent=head)
    # eyes
    for sx in (-1, 1):
        sphere((sx * 0.12, -0.285, 0.05), 1, m['eye'], scale=(0.075, 0.04, 0.085 * eye_open), parent=head)
        sphere((sx * 0.12 + pup[0], -0.32, 0.05 + pup[1]), 0.034, m['pupil'], parent=head)
        box((sx * 0.12, -0.31, 0.16 + brow_h), (0.11, 0.02, 0.025), m['brow'],
            rot=(0, R(-sx * brow_a), 0), parent=head, bevel=0.008)
    glasses = 'sunglasses' in props or 'soot' not in props
    if glasses:
        gm = m['glasses']
        lens = mat('#111111', 0.15) if 'sunglasses' in props else None
        for sx in (-1, 1):
            torus((sx * 0.12, -0.33, 0.05), 0.085, 0.012, gm, rot=(R(90), 0, 0), parent=head)
            if lens:
                cyl((sx * 0.12, -0.335, 0.05), 0.08, 0.01, lens, rot=(R(90), 0, 0), parent=head)
        box((0, -0.34, 0.06), (0.07, 0.012, 0.012), gm, parent=head)
    if 'helmet' in props:
        cut_sphere((0, 0, 0.03), 0.4, mat('#c6f03a', 0.35), keep_above=0.05, parent=head)
    if 'hardhat' in props:
        cut_sphere((0, 0, 0.05), 0.38, mat('#f5c400', 0.35), keep_above=0.05, parent=head)
        cyl((0, -0.02, 0.06), 0.46, 0.025, mat('#f5c400', 0.35), parent=head)
    if 'crown' in props:
        gold = mat('#f1c40f', 0.25, metal=0.9)
        cyl((0, 0, 0.36), 0.2, 0.1, gold, parent=head)
        for k in range(6):
            import math
            a = k / 6 * 2 * math.pi
            cone((0.19 * math.cos(a), 0.19 * math.sin(a), 0.46), 0.05, 0, 0.12, gold, parent=head)
    return head


# anchor points the compositor needs (world coords, filled by sprite renderer after posing)
def anchors(root):
    import bpy
    bpy.context.view_layer.update()
    head = bpy.data.objects['head']
    mw = head.matrix_world
    from mathutils import Vector
    return dict(mouth=list(mw @ Vector((0, -0.33, -0.15))), mouth_r=list(mw @ Vector((0.09, -0.33, -0.15))),
                head=list(mw @ Vector((0, 0, 0))), hand_b=list(bpy.data.objects['b_hand'].matrix_world.translation),
                hand_a=list(bpy.data.objects['a_hand'].matrix_world.translation))
