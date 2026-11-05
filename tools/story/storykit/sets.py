"""Background worlds rendered once per story as a still plate (runs inside bpy).
The host and props stand on the plane y=0, z=0; the renderer records where that plane lands on screen.
Add a new @set function for a new world. `tone` tints the sky: day | dusk | night | dark.
"""
import math
import random
import bpy
from .blib import R, mat, empty, sphere, box, cyl, cone, torus, lights, world_color, hexrgb

SETS = {}
SKY = {'day': ('#7cc4f5', '#e8f6ff'), 'dusk': ('#3b2a6b', '#ff9e6d'), 'night': ('#070b1f', '#1d2a55'),
       'dark': ('#050507', '#15161c')}


def setfn(fn):
    SETS[fn.__name__] = fn
    return fn


def _ground(color, size=80, rough=0.85):
    box((0, 20, -0.05), (size, size, 0.1), mat(color, rough))


def _sun(tone, strength=3.0):
    d = bpy.data.lights.new('sun', 'SUN')
    d.energy = {'day': strength, 'dusk': strength * 0.7, 'night': 0.25, 'dark': 0.1}[tone]
    d.color = hexrgb('#ffe2b8' if tone == 'dusk' else '#fff6e8')[:3]
    d.angle = R(8)
    o = bpy.data.objects.new('sun', d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (R(50), R(-25), R(35))


@setfn
def studio(tone='day', color='#2b5cd6'):
    world_color('#0c0f1a', '#1b2240')
    c = mat(color, 0.7)
    _ground('#20263f', rough=0.4)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=9, depth=20, location=(0, 9, 10))
    o = bpy.context.object
    o.data.materials.append(c)
    for x in (-3.2, 3.2):
        torus((x, 4.5, 3.2), 1.0, 0.06, mat('#ffd166', 0.3, emit=8), rot=(R(90), 0, 0))
    lights(energy=1.2)


@setfn
def park(tone='day', color='#5cbf4a'):
    world_color(*SKY[tone])
    _ground(color)
    rnd = random.Random(4)
    for (x, y, r) in ((-9, 26, 9), (8, 30, 11), (0, 40, 12)):
        sphere((x, y, -r * 0.55), r, mat('#4aa83f', 0.9))
    box((0, 3.0, 0.0), (40, 2.2, 0.02), mat('#d8c39a', 0.9))  # path
    from .props import tree
    for (x, y, k) in ((-4.6, 5, 0), (4.2, 7, 1), (-2.2, 12, 2), (6.5, 14, 0), (-7.5, 11, 1)):
        t = tree(k)
        t.location = (x, y, 0)
    for i in range(30):
        x, y = rnd.uniform(-8, 8), rnd.uniform(1, 9)
        sphere((x, y, 0.04), 0.06, mat(rnd.choice(['#ffffff', '#ffd23f', '#ff7eb6']), 0.6))
    _sun(tone)
    lights(energy=0.5)


@setfn
def city(tone='day', color='#8d98a8'):
    world_color(*SKY[tone])
    _ground('#3a3d44', rough=0.7)
    box((0, 2.6, 0.06), (60, 2.0, 0.12), mat('#b9bec7', 0.8))  # sidewalk
    for x in range(-12, 13, 3):
        box((x + 1.3, 0.5, 0.005), (1.2, 0.12, 0.01), mat('#f2f2f2', 0.6))  # lane marks
    rnd = random.Random(7)
    win_on = mat('#ffe9a8', 0.4, emit=3 if tone in ('night', 'dusk', 'dark') else 0.4)
    x = -12
    while x < 12:
        w = rnd.uniform(2.2, 3.6)
        h = rnd.uniform(5, 13)
        y = rnd.uniform(5.5, 8)
        col = rnd.choice([color, '#b7a28c', '#7d8aa0', '#a0a7b4', '#c49a7a'])
        box((x + w / 2, y, h / 2), (w, 3, h), mat(col, 0.8), bevel=0.04)
        for wy in range(int(h // 1.3)):
            for wx in range(int(w // 0.9)):
                if rnd.random() < 0.85:
                    box((x + 0.55 + wx * 0.9, y - 1.51, 1 + wy * 1.3), (0.45, 0.02, 0.6), win_on)
        x += w + 0.25
    _sun(tone)
    lights(energy=0.6)


@setfn
def room(tone='day', color='#e9dcc7'):
    world_color('#20160f')
    _ground('#a0703f', rough=0.5)  # wood floor
    box((0, 4.2, 4), (16, 0.2, 8), mat(color, 0.9))  # back wall
    box((0, 4.05, 0.15), (16, 0.12, 0.3), mat('#ffffff', 0.6))  # skirting
    pane = mat({'day': '#cfefff', 'dusk': '#ffb385', 'night': '#16214a', 'dark': '#0b0b12'}[tone], 0.2, emit=2.5)
    box((-2.6, 4.08, 3.2), (2.4, 0.05, 2.2), pane)
    box((-2.6, 4.05, 3.2), (2.6, 0.06, 2.4), mat('#ffffff', 0.5))
    box((-2.6, 4.02, 3.2), (2.4, 0.05, 2.2), pane)
    # couch + shelf + lamp
    box((3.0, 3.3, 0.5), (3.2, 1.2, 1.0), mat('#c0504d', 0.8), bevel=0.15)
    box((3.0, 3.85, 1.2), (3.2, 0.4, 1.2), mat('#c0504d', 0.8), bevel=0.15)
    box((-5.2, 3.8, 1.6), (1.6, 0.6, 3.2), mat('#6e4a2f', 0.7), bevel=0.03)
    for i, c in enumerate(['#2e86de', '#f6b93b', '#e55039', '#78e08f']):
        box((-5.6 + i * 0.25, 3.7, 1.9), (0.18, 0.4, 0.6), mat(c, 0.6))
    cyl((5.4, 3.5, 1.0), 0.04, 2.0, mat('#333333', 0.4))
    cone((5.4, 3.5, 2.1), 0.35, 0.2, 0.45, mat('#fff1c1', 0.6, emit=3))
    lights(energy=1.0)
    d = bpy.data.lights.new('p', 'POINT')
    d.energy = 400
    d.color = hexrgb('#ffd59e')[:3]
    o = bpy.data.objects.new('p', d)
    bpy.context.scene.collection.objects.link(o)
    o.location = (5.4, 3.0, 2.0)


@setfn
def desert(tone='day', color='#e3b778'):
    world_color(*({'day': ('#3d9ee8', '#fff2d6')}.get(tone, SKY[tone])))
    _ground(color)
    for (x, y, r) in ((-10, 22, 9), (9, 26, 12), (1, 34, 13)):
        sphere((x, y, -r * 0.7), r, mat('#d9a35f', 0.9))
    cm = mat('#3e8e41', 0.7)
    for (x, y) in ((-4.5, 6), (5.5, 9)):
        cyl((x, y, 1.1), 0.25, 2.2, cm)
        sphere((x, y, 2.2), 0.25, cm)
        cyl((x + 0.45, y, 1.4), 0.15, 0.8, cm)
        cyl((x + 0.3, y, 1.05), 0.15, 0.4, cm, rot=(0, R(90), 0))
    _sun(tone, 4)
    lights(energy=0.4)


@setfn
def space(tone='dark', color='#7f8c8d'):
    world_color('#020208')
    _ground(color, rough=0.95)
    rnd = random.Random(2)
    star = mat('#ffffff', 0.5, emit=20)
    for i in range(260):
        sphere((rnd.uniform(-40, 40), 60, rnd.uniform(2, 70)), rnd.uniform(0.04, 0.12), star, seg=8)
    sphere((14, 70, 30), 9, mat('#d4734a', 0.8))
    torus((14, 70, 30), 14, 0.7, mat('#e7c08a', 0.6), rot=(R(70), R(15), 0))
    for i in range(14):
        x, y = rnd.uniform(-9, 9), rnd.uniform(2, 14)
        torus((x, y, 0.0), rnd.uniform(0.3, 0.9), 0.08, mat('#6b7576', 0.95))
    _sun('day', 2.5)
    lights(energy=0.4)


@setfn
def void(tone='dark', color='#1a1a22'):
    world_color(*SKY[tone]) if tone != 'dark' else world_color('#040406')
    _ground(color, rough=0.3)
    d = bpy.data.lights.new('spot', 'SPOT')
    d.energy = 1800
    d.spot_size = R(40)
    d.spot_blend = 0.5
    o = bpy.data.objects.new('spot', d)
    bpy.context.scene.collection.objects.link(o)
    o.location = (0, -1, 9)
    o.rotation_euler = (R(6), 0, 0)
