"""Renders a gummy-animal tower simulation (tower_sim.py JSON) with Blender.

Usage: python tower_render.py sim.json --out DIR [--res W H] [--samples N] [--still F ...]
"""
import argparse, json, math, os, sys
import numpy as np
import bpy
from mathutils import Vector, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import THICK, GUMMY_COLORS, animal_geometry

ap = argparse.ArgumentParser()
ap.add_argument("sim")
ap.add_argument("--out", default="frames")
ap.add_argument("--res", type=int, nargs=2, default=[576, 1024])
ap.add_argument("--samples", type=int, default=10)
ap.add_argument("--still", type=int, nargs="*", default=None)
args = ap.parse_args(sys.argv[1:])

S = json.load(open(args.sim))
FPS, NF = S["fps"], S["frames"]
PED_TOP, PED_R = S["ped_top"], S["ped_r"]
BEVEL = 0.075

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = FPS
scn.frame_start, scn.frame_end = 1, NF

def link(o):
    scn.collection.objects.link(o)
    return o

# ------------------------------------------------------------------ materials
def principled(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"]

gummy_mats = {}
def gummy(cname):
    if cname not in gummy_mats:
        c = GUMMY_COLORS[cname]
        m, b = principled("Gummy_" + cname)
        b.inputs["Base Color"].default_value = (*c, 1)
        b.inputs["Subsurface Weight"].default_value = 1.0
        b.inputs["Subsurface Radius"].default_value = tuple(0.15 + 0.85 * v for v in c)
        b.inputs["Subsurface Scale"].default_value = 0.25
        b.inputs["Transmission Weight"].default_value = 0.35
        b.inputs["IOR"].default_value = 1.42
        b.inputs["Roughness"].default_value = 0.16
        b.inputs["Coat Weight"].default_value = 1.0
        b.inputs["Coat Roughness"].default_value = 0.06
        gummy_mats[cname] = m
    return gummy_mats[cname]

eye_mat, b = principled("Eye")
b.inputs["Base Color"].default_value = (0.01, 0.008, 0.012, 1)
b.inputs["Roughness"].default_value = 0.08
b.inputs["Coat Weight"].default_value = 1.0

ped_mat, b = principled("Pedestal")
b.inputs["Base Color"].default_value = (0.97, 0.95, 0.96, 1)
b.inputs["Roughness"].default_value = 0.25
b.inputs["Coat Weight"].default_value = 0.6

back_mat, b = principled("Backdrop")
b.inputs["Base Color"].default_value = (0.55, 0.42, 0.8, 1)      # lilac
b.inputs["Roughness"].default_value = 0.7

text_mat, b = principled("Text")
b.inputs["Base Color"].default_value = (1, 1, 1, 1)
b.inputs["Emission Color"].default_value = (1, 1, 1, 1)
b.inputs["Emission Strength"].default_value = 2.5
shadow_mat, b = principled("TextShadow")  # soft drop shadow for legibility
b.inputs["Base Color"].default_value = (0.1, 0.05, 0.15, 1)
b.inputs["Emission Color"].default_value = (0.08, 0.03, 0.12, 1)
b.inputs["Emission Strength"].default_value = 0.6

# ------------------------------------------------------------------ studio
world = bpy.data.worlds.new("W"); scn.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.66, 0.8, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.2

import bmesh
prof = [(-40, 0)]
yb, rad = 6.0, 6.0
for i in range(21):
    a = i / 20 * math.pi / 2
    prof.append((yb + rad * math.sin(a), rad - rad * math.cos(a)))
prof.append((yb + rad, 60))
bm = bmesh.new()
rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-60, 60)]
for i in range(len(prof) - 1):
    bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
me = bpy.data.meshes.new("Cyc"); bm.to_mesh(me); bm.free()
for poly in me.polygons:
    poly.use_smooth = True
me.materials.append(back_mat)
link(bpy.data.objects.new("Cyc", me))

bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=PED_R, depth=PED_TOP, location=(0, 0, PED_TOP / 2))
ped = bpy.context.object
bv = ped.modifiers.new("b", "BEVEL"); bv.width = 0.05; bv.segments = 4; bv.limit_method = "ANGLE"
ped.data.materials.append(ped_mat)
bpy.ops.object.shade_smooth()

def area(name, loc, target, size, power, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = color
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o
lights = [area("Key", (-6, -8, 12), (0, 0, 3), 7, 1300),
          area("Rim", (5, 7, 9), (0, 0, 3), 6, 2200, (1.0, 0.92, 0.95)),
          area("Fill", (8, -7, 3), (0, 0, 3), 7, 320, (0.9, 0.92, 1.0))]

# ------------------------------------------------------------------ bodies
def animal_object(i, body):
    outline, parts, eyes, nose = animal_geometry(body["name"])
    shrunk = outline.buffer(-BEVEL, join_style=1).simplify(0.004)
    if shrunk.geom_type != "Polygon":
        shrunk = max(shrunk.geoms, key=lambda g: g.area)
    cu = bpy.data.curves.new(f"A{i}", "CURVE")
    cu.dimensions = "2D"; cu.fill_mode = "BOTH"
    cu.extrude = THICK / 2 - BEVEL
    cu.bevel_depth = BEVEL; cu.bevel_resolution = 5
    sp = cu.splines.new("POLY")
    pts = list(shrunk.exterior.coords)[:-1]
    sp.points.add(len(pts) - 1)
    for k, (x, z) in enumerate(pts):
        sp.points[k].co = (x, z, 0, 1)
    sp.use_cyclic_u = True; sp.use_smooth = True
    cu.materials.append(gummy(body["color"]))
    # curve lives in its XY plane; this child-of-root rotation stands it up in world XZ
    inner = link(bpy.data.objects.new(f"A{i}_shape", cu))
    inner.rotation_euler = (math.pi / 2, 0, 0)
    root = link(bpy.data.objects.new(f"Animal{i}", None))
    inner.parent = root
    front = -THICK / 2
    for (ex, ez) in eyes:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.052, location=(ex, front + 0.012, ez), segments=16, ring_count=8)
        e = bpy.context.object; e.data.materials.append(eye_mat); e.parent = root
        e.scale = (1, 0.6, 1.15); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(nose[0], front + 0.012, nose[1]), segments=16, ring_count=8)
    n = bpy.context.object; n.data.materials.append(eye_mat); n.parent = root
    n.scale = (1.3, 0.6, 0.85); bpy.ops.object.shade_smooth()
    return root

objs = []
for i, body in enumerate(S["bodies"]):
    if body["kind"] == "animal":
        o = animal_object(i, body)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=S["event"]["radius"], segments=48, ring_count=24)
        o = bpy.context.object; o.data.materials.append(gummy(body["color"]))
        bpy.ops.object.shade_smooth()
    objs.append(o)

# jiggle: damped squash & stretch after every impact (purely visual)
jig = np.zeros((len(objs), NF))
for c in S["contacts"]:
    f0 = c["t"] * FPS
    amp = min(1.0, c["speed"] / 4.0) * 0.16
    for k in ("a", "b"):
        i = c[k]
        if not isinstance(i, int):
            continue
        fr = np.arange(NF)
        dt = (fr - f0) / FPS
        m = dt >= 0
        jig[i, m] += amp * np.exp(-dt[m] / 0.16) * np.cos(2 * np.pi * 7.0 * dt[m])
jig = np.clip(jig, -0.22, 0.22)

for i, o in enumerate(objs):
    sf = S["bodies"][i]["spawn_frame"]
    o.rotation_mode = "XYZ"
    ths = [S["records"][f].get(str(i), [0, 0, 0])[2] for f in range(NF)]
    ths = np.unwrap(ths)
    for f in range(NF):
        rec = S["records"][f].get(str(i))
        visible = rec is not None
        o.hide_render = not visible
        o.keyframe_insert("hide_render", frame=f + 1)
        for ch in o.children:
            ch.hide_render = not visible
            ch.keyframe_insert("hide_render", frame=f + 1)
        if not visible:
            continue
        o.location = (rec[0], 0, rec[1])
        o.rotation_euler = (0, ths[f], 0)
        s = jig[i, f]
        o.scale = (1 + s, 1 - s * 0.3, 1 - s)
        o.keyframe_insert("location", frame=f + 1)
        o.keyframe_insert("rotation_euler", frame=f + 1)
        o.keyframe_insert("scale", frame=f + 1)

for f in range(NF):
    ped.location = (S["ped_x"][f], 0, PED_TOP / 2)
    ped.keyframe_insert("location", frame=f + 1)

# ------------------------------------------------------------------ camera follows the tower
cam = link(bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")))
cam.data.lens = 50
cam.data.clip_start = 0.1
scn.camera = cam
VFOV = 2 * math.atan(18 / 50)
aspect = args.res[0] / args.res[1]
tops = np.array(S["tops"])
want = np.maximum.accumulate(tops) * 0 + tops
# frame needs: floor a bit below the pedestal up to the spawn zone above the settled top
# horizontal room: only animals still on or near the pedestal matter (not the projectile,
# not pieces that rolled away across the floor)
animal_idx = {str(i) for i, b in enumerate(S["bodies"]) if b["kind"] == "animal"}
spread = np.array([min(2.6, max([abs(v[0]) for k, v in rec.items()
                                  if k in animal_idx and v[1] > PED_TOP - 0.3] + [0])) + 0.8
                   for rec in S["records"]])
need = np.zeros(NF)
smooth = None
for f in range(NF):
    # anticipate a little, but ignore brief spikes (a piece flung up for a few frames)
    look = float(np.percentile(tops[max(0, f - 20): f + 25], 80))
    H = ((look + 0.5) - (-0.5)) / 0.8                    # floor in front + title headroom
    H = max(H, 4.4 / aspect)                             # pedestal + margins always fit
    H = max(H, 2 * max(spread[max(0, f - 10): f + 10]) / aspect)  # widen when the tower spreads
    smooth = H if smooth is None else smooth + (H - smooth) * (0.12 if H > smooth else 0.03)
    need[f] = smooth
for f in range(NF):
    H = need[f]
    d = (H / 2) / math.tan(VFOV / 2)
    zc = -0.5 + H * 0.5
    cam.location = (0, -d, zc + d * math.tan(0.16))
    cam.rotation_euler = (math.pi / 2 - 0.16, 0, 0)
    cam.keyframe_insert("location", frame=f + 1)
    cam.keyframe_insert("rotation_euler", frame=f + 1)

print("CAMERA H min/max: %.2f %.2f" % (need.min(), need.max()))
# ------------------------------------------------------------------ title (screen-space, English)
n = S["n"]
title = f"{n} Animal" + ("s" if n > 1 else "")
DIST = 3.0
half_h = DIST * math.tan(VFOV / 2)
ty = half_h * (1 - 2 * 0.165)          # a little lower than the "N Cuts" title
for nm, mat, off, z in (("TitleShadow", shadow_mat, (0.007, -0.007), -DIST - 0.01), ("Title", text_mat, (0, 0), -DIST)):
    td = bpy.data.curves.new(nm, "FONT")
    td.body = title; td.align_x = "CENTER"; td.align_y = "CENTER"; td.size = 0.175
    td.materials.append(mat)
    t = link(bpy.data.objects.new(nm, td))
    t.parent = cam
    t.location = (off[0], ty + off[1], z)
    t.rotation_euler = (0, 0, 0)
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(t, attr, False)

# ------------------------------------------------------------------ render
r = scn.render
r.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = args.samples
scn.cycles.use_denoising = True
scn.cycles.denoising_prefilter = "FAST"
scn.cycles.max_bounces = 6
scn.cycles.diffuse_bounces = 2; scn.cycles.glossy_bounces = 3
scn.cycles.transmission_bounces = 4; scn.cycles.transparent_max_bounces = 4
scn.cycles.caustics_reflective = False; scn.cycles.caustics_refractive = False
r.use_persistent_data = True
r.resolution_x, r.resolution_y = args.res
r.use_motion_blur = True
r.motion_blur_shutter = 0.35
r.image_settings.file_format = "PNG"
scn.view_settings.view_transform = "AgX"
scn.view_settings.look = "AgX - Medium High Contrast"

os.makedirs(args.out, exist_ok=True)
frames = args.still if args.still is not None else range(1, NF + 1)
for f in frames:
    out = os.path.join(os.path.abspath(args.out), f"{f:04d}.png")
    if os.path.exists(out) and args.still is None:
        continue
    scn.frame_set(f)
    r.filepath = out
    bpy.ops.render.render(write_still=True)
