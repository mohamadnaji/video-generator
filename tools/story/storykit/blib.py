"""Small Blender helpers shared by the host, props and sets (runs inside bpy)."""
import math
import bpy
import bmesh
from mathutils import Vector

R = math.radians
_MATS = {}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    import addon_utils
    try:
        addon_utils.enable('cycles', default_set=True)
    except Exception:
        pass


def hexrgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    lin = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        lin.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*lin, 1.0)


def mat(color, rough=0.55, metal=0.0, emit=0.0, name=None):
    key = name or f'{color}_{rough}_{metal}_{emit}'
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = hexrgb(color)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = hexrgb(color)
        p.inputs['Emission Strength'].default_value = emit
    _MATS[key] = m
    return m


def _finish(obj, m, parent=None, smooth=True):
    if m is not None:
        obj.data.materials.clear()
        obj.data.materials.append(m)
    if smooth and hasattr(obj.data, 'polygons'):
        for p in obj.data.polygons:
            p.use_smooth = True
    if parent is not None:
        obj.parent = parent
    return obj


def empty(loc=(0, 0, 0), rot=(0, 0, 0), parent=None, name='j'):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    if parent is not None:
        e.parent = parent
    return e


def sphere(loc, r, m, scale=(1, 1, 1), parent=None, seg=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object
    o.scale = scale
    return _finish(o, m, parent)


def box(loc, size, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    if bevel:
        mod = o.modifiers.new('bev', 'BEVEL')
        mod.width = bevel
        mod.segments = 4
        mod.affect = 'EDGES'
        o.modifiers.new('ws', 'WEIGHTED_NORMAL')
    return _finish(o, m, parent, smooth=bool(bevel))


def cyl(loc, r, depth, m, rot=(0, 0, 0), parent=None, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    return _finish(bpy.context.object, m, parent, smooth=True)


def cone(loc, r1, r2, depth, m, rot=(0, 0, 0), parent=None, verts=40):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    return _finish(bpy.context.object, m, parent, smooth=True)


def torus(loc, R_, r, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R_, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=48, minor_segments=16)
    return _finish(bpy.context.object, m, parent, smooth=True)


def cut_sphere(loc, r, m, keep_above=0.0, scale=(1, 1, 1), rot=(0, 0, 0), parent=None):
    """Sphere with every vertex below local z = keep_above*r removed (caps, hair, helmets)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r, location=loc, rotation=rot)
    o = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < keep_above * r], context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    mod = o.modifiers.new('sol', 'SOLIDIFY')
    mod.thickness = r * 0.06
    o.scale = scale
    return _finish(o, m, parent)


def limb(parent, length, radius, m, name='limb', taper=1.0):
    """Ellipsoid hanging down from a joint; returns the child joint at its end."""
    sphere((0, 0, -length / 2), 1, m, scale=(radius, radius * 0.95, length / 2 + radius * 0.6), parent=parent, seg=32)
    return empty((0, 0, -length), parent=parent, name=name)


def lights(key=(3.5, -6, 6), energy=1.0, warm='#fff1dc', cool='#cfe2ff'):
    def area(loc, power, size, color, target=(0, 0, 1)):
        d = bpy.data.lights.new('a', 'AREA')
        d.energy = power * energy
        d.size = size
        d.color = hexrgb(color)[:3]
        o = bpy.data.objects.new('a', d)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc
        look_at(o, target)
    area(key, 900, 4, warm)
    area((-5, -5, 3), 350, 6, cool)
    area((0, 6, 5), 600, 3, '#ffffff')


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def world_color(top, bottom=None, strength=1.0):
    w = bpy.data.worlds.new('w')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get('Background')
    bg.inputs['Strength'].default_value = strength
    if bottom is None:
        bg.inputs['Color'].default_value = hexrgb(top)
        return
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = hexrgb(bottom)
    ramp.color_ramp.elements[1].color = hexrgb(top)
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.75
    mp = nt.nodes.new('ShaderNodeMapRange')
    mp.inputs['From Min'].default_value = -1
    nt.links.new(tc.outputs['Generated' if False else 'Window'], sep.inputs[0])
    nt.links.new(sep.outputs['Y'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])


def cycles(samples=24, w=900, h=1200, transparent=True):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = samples
    try:
        s.cycles.use_denoising = True
    except Exception:
        pass
    s.cycles.max_bounces = 4
    s.render.resolution_x = w
    s.render.resolution_y = h
    s.render.resolution_percentage = 100
    s.render.film_transparent = transparent
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    try:
        s.view_settings.view_transform = 'Standard'
        s.view_settings.look = 'Medium High Contrast'
    except Exception:
        pass


def project(cam, co):
    """World point -> (x, y) pixel in the render (top-left origin)."""
    from bpy_extras.object_utils import world_to_camera_view
    s = bpy.context.scene
    bpy.context.view_layer.update()
    v = world_to_camera_view(s, cam, Vector(co))
    return [round(v.x * s.render.resolution_x, 1), round((1 - v.y) * s.render.resolution_y, 1)]


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
