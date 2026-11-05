"""Stand-alone 3D objects for stories (runs inside bpy). Each builder makes the object standing on z=0,
centred on x=0, in world units (the host is ~2.15 tall). Add a new @prop function when a story needs one.
Variants: a builder may take `frame` (int) for simple animation cycles, e.g. legs on a bomb.
"""
import math
from .blib import R, mat, empty, sphere, box, cyl, cone, torus, cut_sphere

PROPS = {}


def prop(fn):
    PROPS[fn.__name__] = fn
    return fn


@prop
def bomb(frame=0, legs=False, angry=False):
    body = mat('#1d1d24', 0.3)
    root = empty()
    sphere((0, 0, 0.55 + (0.25 if legs else 0)), 0.5, body, parent=root)
    z0 = 0.55 + (0.25 if legs else 0)
    cyl((0.22, 0, z0 + 0.45), 0.13, 0.16, mat('#4a4a55', 0.4), rot=(0, R(28), 0), parent=root)
    cyl((0.33, 0, z0 + 0.62), 0.02, 0.25, mat('#c9a26b', 0.7), rot=(0, R(40), 0), parent=root)
    sphere((0.42, 0, z0 + 0.73), 0.07, mat('#ffcf3f', 0.3, emit=12), parent=root)
    if legs or angry:
        for sx in (-1, 1):
            sphere((sx * 0.17, -0.44, z0 + 0.05), 1, mat('#ffffff', 0.3), scale=(0.1, 0.05, 0.11), parent=root)
            sphere((sx * 0.15, -0.49, z0 + 0.03), 0.045, mat('#111111', 0.3), parent=root)
            box((sx * 0.17, -0.47, z0 + 0.2), (0.16, 0.03, 0.035), mat('#0d0d0d'), rot=(0, R(sx * 22), 0), parent=root)
    if legs:
        s = math.sin(frame / 4 * 2 * math.pi)
        for sx, ph in ((-1, s), (1, -s)):
            j = empty((sx * 0.18, 0, 0.35), (R(35 * ph), 0, 0), parent=root)
            cyl((0, 0, -0.15), 0.035, 0.3, mat('#111111'), parent=j)
            sphere((0, -0.06, -0.32), 1, mat('#e8322f', 0.4), scale=(0.08, 0.13, 0.06), parent=j)
    return root


@prop
def ambulance():
    root = empty()
    box((0, 0, 0.75), (2.4, 1.1, 1.0), mat('#f7f7f7', 0.4), parent=root, bevel=0.08)
    box((-0.8, -0.56, 0.95), (0.6, 0.02, 0.4), mat('#8fd3ff', 0.1), parent=root)
    box((0.3, -0.56, 0.75), (0.6, 0.02, 0.18), mat('#e63946', 0.4), parent=root)
    box((0.3, -0.56, 0.75), (0.18, 0.02, 0.6), mat('#e63946', 0.4), parent=root)
    box((0, 0, 1.33), (0.5, 0.3, 0.15), mat('#2f80ed', 0.2, emit=4), parent=root)
    for x in (-0.75, 0.75):
        cyl((x, -0.4, 0.28), 0.28, 0.2, mat('#1c1c1c', 0.7), rot=(R(90), 0, 0), parent=root)
    return root


@prop
def chair():
    w = mat('#7a4e2d', 0.6)
    root = empty()
    box((0, 0, 0.55), (0.7, 0.6, 0.08), w, parent=root, bevel=0.02)
    for x in (-0.3, 0.3):
        for y in (-0.25, 0.25):
            box((x, y, 0.27), (0.06, 0.06, 0.55), w, parent=root)
    box((0, 0.28, 1.0), (0.7, 0.06, 0.8), w, parent=root, bevel=0.02)
    return root


@prop
def shelter():
    c = mat('#9aa3ad', 0.8)
    root = empty()
    box((0, 0, 1.4), (2.6, 1.6, 2.8), c, parent=root, bevel=0.05)
    box((0, -0.81, 0.75), (0.8, 0.02, 1.5), mat('#3a3f45', 0.6), parent=root)
    box((0, -0.82, 3.05), (2.8, 0.05, 0.45), mat('#ffd23f', 0.4), parent=root, bevel=0.02)
    return root


@prop
def tree(kind=0):
    root = empty()
    cyl((0, 0, 0.8), 0.13, 1.6, mat('#6b4423', 0.8), parent=root)
    g = mat(['#3fa34d', '#2d8a3e', '#58b368'][kind % 3], 0.7)
    for (x, z, r) in ((0, 2.0, 0.75), (-0.45, 1.65, 0.5), (0.45, 1.7, 0.55), (0.1, 2.5, 0.5)):
        sphere((x, 0, z), r, g, parent=root)
    return root


@prop
def car(color='#e74c3c'):
    root = empty()
    box((0, 0, 0.55), (2.6, 1.2, 0.6), mat(color, 0.3), parent=root, bevel=0.12)
    box((-0.1, 0, 1.05), (1.4, 1.1, 0.55), mat(color, 0.3), parent=root, bevel=0.15)
    box((-0.1, -0.56, 1.05), (1.2, 0.02, 0.4), mat('#8fd3ff', 0.1), parent=root)
    for x in (-0.85, 0.85):
        cyl((x, -0.45, 0.3), 0.3, 0.25, mat('#1c1c1c', 0.7), rot=(R(90), 0, 0), parent=root)
    return root


@prop
def crate():
    root = empty()
    box((0, 0, 0.4), (0.8, 0.8, 0.8), mat('#c58b4a', 0.7), parent=root, bevel=0.03)
    return root


@prop
def trophy():
    g = mat('#f1c40f', 0.2, metal=0.9)
    root = empty()
    box((0, 0, 0.1), (0.4, 0.4, 0.2), mat('#2c2c2c', 0.4), parent=root, bevel=0.02)
    cyl((0, 0, 0.35), 0.05, 0.3, g, parent=root)
    cut_sphere((0, 0, 0.75), 0.25, g, keep_above=-0.9, scale=(1, 1, 1.2), rot=(R(180), 0, 0), parent=root)
    return root


@prop
def coin():
    root = empty()
    cyl((0, 0, 0.35), 0.35, 0.08, mat('#f1c40f', 0.25, metal=0.9), rot=(R(90), 0, 0), parent=root)
    return root


@prop
def lightbulb():
    root = empty()
    sphere((0, 0, 0.55), 0.3, mat('#fff3a0', 0.1, emit=6), parent=root)
    cyl((0, 0, 0.18), 0.13, 0.2, mat('#9a9a9a', 0.3, metal=0.8), parent=root)
    return root


@prop
def rocket():
    root = empty()
    cyl((0, 0, 1.0), 0.35, 1.6, mat('#ecf0f1', 0.3), parent=root)
    cone((0, 0, 2.1), 0.35, 0, 0.6, mat('#e74c3c', 0.3), parent=root)
    cyl((0, -0.34, 1.3), 0.13, 0.04, mat('#5dade2', 0.1), rot=(R(90), 0, 0), parent=root)
    for a in (0, 120, 240):
        box((0.35 * math.cos(R(a)), 0.35 * math.sin(R(a)), 0.35), (0.04, 0.3, 0.5), mat('#e74c3c', 0.3),
            rot=(0, 0, R(a + 90)), parent=root)
    return root


@prop
def cloud():
    root = empty()
    w = mat('#f4f6f8', 0.9)
    for (x, z, r) in ((0, 0.6, 0.5), (-0.5, 0.45, 0.38), (0.5, 0.45, 0.4)):
        sphere((x, 0, z), r, w, parent=root)
    return root


@prop
def money():
    root = empty()
    for i in range(5):
        box((0.02 * (i % 2), 0, 0.05 + i * 0.09), (0.9, 0.45, 0.08), mat('#2ecc71', 0.6), parent=root, bevel=0.01)
    return root


@prop
def clock():
    root = empty()
    cyl((0, 0, 0.6), 0.5, 0.12, mat('#ecf0f1', 0.4), rot=(R(90), 0, 0), parent=root)
    torus((0, 0, 0.6), 0.5, 0.05, mat('#c0392b', 0.4), rot=(R(90), 0, 0), parent=root)
    box((0, -0.08, 0.75), (0.04, 0.02, 0.32), mat('#111'), parent=root)
    box((0.1, -0.08, 0.6), (0.24, 0.02, 0.04), mat('#111'), parent=root)
    return root
