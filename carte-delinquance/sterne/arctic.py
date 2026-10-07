"""Démo 3D « Arctique » : banquise, icebergs, montagnes enneigées, soleil polaire bas,
oiseau rouge vif stylisé (la sterne) suivi par la caméra. Blender 4.5 / Cycles.
Usage : FRAMES=0,75 bl/bin/python arctic.py <out_dir> <f0> <f1> [samples] [scale%]"""
import bpy, bmesh, math, sys, os, numpy as np
from scipy.ndimage import zoom
from scipy.spatial import Voronoi
from mathutils import Vector, Euler

out, f0, f1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 32
SCALE = int(sys.argv[5]) if len(sys.argv) > 5 else 100
FPS, DUR = 30, 5.0
rng = np.random.default_rng(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; col = sc.collection

def mat(name, base, rough, sss=0.0, sss_rad=(0.5, 0.8, 1.0), emit=None, emit_s=0.0, attr=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = sss_rad
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = emit_s
    if attr:
        a = nt.nodes.new("ShaderNodeVertexColor"); a.layer_name = attr; nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
    return m
SNOW = mat("snow", (0.97, 0.99, 1.0), 0.6, sss=0.12, sss_rad=(0.4, 0.7, 1.0))
ICE = mat("ice", (0.30, 0.72, 1.0), 0.12, sss=0.5, sss_rad=(0.2, 0.6, 1.4))
RED = mat("bird", (0.75, 0.0, 0.0), 0.38)
MOUNT = mat("mount", (1, 1, 1), 0.7, attr="c")

def obj_from(name, verts, faces, m, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.data.materials.append(m); return o

# ------------------------------------------------------------------ eau
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 60, 0)); water = bpy.context.object; water.scale = (300, 300, 1)
wm = bpy.data.materials.new("water"); wm.use_nodes = True; nt = wm.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.005, 0.035, 0.075, 1); b.inputs["Roughness"].default_value = 0.07
tx = nt.nodes.new("ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = 40; tx.inputs["Detail"].default_value = 4
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
nt.links.new(tx.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"]); water.data.materials.append(wm)

# ------------------------------------------------------------------ banquise : plaques de Voronoï, légèrement rétrécies (chenaux d'eau)
BERGS = [(-4.5, 22, 3.2, 5.5), (5.5, 30, 2.6, 4.2), (-1.0, 42, 4.0, 7.0), (9.0, 48, 3.0, 5.0), (-10, 36, 2.4, 4.0)]
pts = np.column_stack([rng.uniform(-30, 30, 900), rng.uniform(-6, 70, 900)])
vor = Voronoi(pts)
verts, faces = [], []
for i, ri in enumerate(vor.point_region):
    reg = vor.regions[ri]
    if -1 in reg or len(reg) < 3: continue
    poly = vor.vertices[reg]; c = pts[i]
    if np.abs(poly - c).max() > 5: continue
    if any(math.hypot(c[0] - bx, c[1] - by) < r + 0.8 for bx, by, r, _ in BERGS): continue
    if abs(c[0] - 0.0) < 1.6 and c[1] < 20: continue                     # chenal libre devant la caméra
    k = rng.uniform(0.72, 0.9); poly = c + (poly - c)*k
    dense = []                                                          # bords irréguliers
    for j in range(len(poly)):
        a_, b_ = poly[j], poly[(j + 1) % len(poly)]
        for q in range(3): m_ = a_ + (b_ - a_)*q/3; dense.append(m_ + rng.normal(0, 0.06, 2))
    poly = np.array(dense)
    th = rng.uniform(0.05, 0.12); n = len(poly); base = len(verts)
    for x, y in poly: verts.append((x, y, th))
    for x, y in poly: verts.append((x, y, -0.05))
    faces.append(list(range(base, base + n)))
    for j in range(n): a, b2 = base + j, base + (j + 1) % n; faces.append([a, b2, b2 + n, a + n])
floes = obj_from("floes", verts, faces, SNOW)
bev = floes.modifiers.new("bev", "BEVEL"); bev.width = 0.04; bev.segments = 2

# ------------------------------------------------------------------ icebergs facettés (low-poly)
for k, (bx, by, r, h) in enumerate(BERGS):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(bx, by, 0)); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data); rr = np.random.default_rng(50 + k)
    for v in bm.verts:
        v.co *= 1 + rr.uniform(-0.18, 0.18)
        if v.co.z > 0.35: v.co.z = 0.35 + (v.co.z - 0.35)*rr.uniform(0.6, 1.8)
        if v.co.z < -0.2: v.co.z = -0.2
    bm.to_mesh(o.data); bm.free()
    o.scale = (r, r*rr.uniform(0.7, 1.1), h); o.rotation_euler[2] = rr.uniform(0, 6.28)
    o.data.materials.append(ICE)
    # calotte de neige sur le dessus
    sn = o.copy(); sn.data = o.data.copy(); col.objects.link(sn); sn.data.materials.clear(); sn.data.materials.append(SNOW)
    sn.scale = (r*1.01, o.scale[1]*1.01, h*1.002); sn.location.z = 0.02
    bm = bmesh.new(); bm.from_mesh(sn.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < 0.55], context="FACES"); bm.to_mesh(sn.data); bm.free()

# ------------------------------------------------------------------ montagnes enneigées au loin (roche sur les pentes raides)
NX, NY = 260, 90
xs = np.linspace(-120, 120, NX); ys = np.linspace(85, 140, NY); XX, YY = np.meshgrid(xs, ys)
def vn(shape, cells, seed):
    r = np.random.default_rng(seed).random((cells[0] + 3, cells[1] + 3))
    z = zoom(r, ((shape[0] + 3*shape[0]/cells[0])/r.shape[0], (shape[1] + 3*shape[1]/cells[1])/r.shape[1]), order=3); return z[:shape[0], :shape[1]]
rid = sum((1 - np.abs(2*vn((NY, NX), (3*2**o, 10*2**o), 70 + o) - 1))**2*0.5**o for o in range(5))/1.9
Hm = rid*34*np.clip((YY - 85)/12, 0, 1) - 1
gy, gx = np.gradient(Hm, ys, xs); slope = np.hypot(gx, gy)
ii = np.arange(NX*NY).reshape(NY, NX)
mv = np.stack([XX.ravel(), YY.ravel(), Hm.ravel()], 1).tolist()
mf = np.stack([ii[:-1, :-1].ravel(), ii[:-1, 1:].ravel(), ii[1:, 1:].ravel(), ii[1:, :-1].ravel()], 1).tolist()
mo = obj_from("mount", mv, mf, MOUNT)
ca = mo.data.color_attributes.new("c", "FLOAT_COLOR", "POINT")
rock = np.clip((slope - 1.0)/0.6, 0, 1).ravel()
for i, d in enumerate(ca.data): r_ = rock[i]; d.color = (0.93 - 0.68*r_, 0.95 - 0.68*r_, 1.0 - 0.7*r_, 1)

# ------------------------------------------------------------------ l'oiseau rouge (forme simple : corps, tête, bec, queue fourchue, ailes)
bird = bpy.data.objects.new("bird", None); col.objects.link(bird)
def part(prim, loc, scale, rot=(0, 0, 0), parent=bird, **kw):
    getattr(bpy.ops.mesh, prim)(location=(0, 0, 0), **kw); o = bpy.context.object
    o.scale = scale; o.location = loc; o.rotation_euler = rot; o.parent = parent; o.data.materials.append(RED)
    for p in o.data.polygons: p.use_smooth = True
    return o
part("primitive_uv_sphere_add", (0, 0, 0), (0.07, 0.24, 0.07), segments=24, ring_count=12)
part("primitive_uv_sphere_add", (0, 0.2, 0.03), (0.055, 0.06, 0.055), segments=20, ring_count=10)
part("primitive_cone_add", (0, 0.3, 0.025), (0.018, 0.018, 0.07), rot=(math.radians(-90), 0, 0), vertices=12)
for s in (-1, 1): part("primitive_cone_add", (0.025*s, -0.32, 0.0), (0.012, 0.012, 0.13), rot=(math.radians(90), 0, math.radians(-12*s)), vertices=10)
WINGS = []
for s in (-1, 1):
    pivot = bpy.data.objects.new(f"wp{s}", None); col.objects.link(pivot); pivot.parent = bird; pivot.location = (0.05*s, 0.02, 0.03)
    # aile effilée : quadrilatère extrudé
    v = [(0, 0.08, 0), (0, -0.08, 0), (0.36*s, -0.13, 0), (0.42*s, -0.04, 0)]
    w = obj_from(f"wing{s}", [(x, y, 0.008) for x, y, _ in v] + [(x, y, -0.008) for x, y, _ in v],
                 [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]], RED)
    w.parent = pivot; WINGS.append((pivot, s))

# ------------------------------------------------------------------ ciel polaire (Nishita, soleil bas) + soleil
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"; sky.sun_elevation = math.radians(11); sky.sun_rotation = math.radians(200)
sky.air_density = 1.0; sky.dust_density = 0.6
wn.links.new(sky.outputs["Color"], wn.nodes["Background"].inputs["Color"]); wn.nodes["Background"].inputs["Strength"].default_value = 0.3
sl = bpy.data.lights.new("sun", "SUN"); sl.energy = 3.6; sl.color = (1.0, 0.97, 0.94); sl.angle = math.radians(2)
so = bpy.data.objects.new("sun", sl); col.objects.link(so); so.rotation_euler = Euler((math.radians(79), 0, math.radians(200 - 180)), "XYZ")

# ------------------------------------------------------------------ trajectoire de l'oiseau + caméra qui le suit
def ease(k): return k*k*(3 - 2*k)
def bird_at(t):
    y = 1.0 + 3.4*t; x = 0.6*math.sin(t*0.9); z = 1.25 + 0.15*math.sin(t*1.7)
    return Vector((x, y, z))
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 30; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
cam = bpy.data.objects.new("cam", cam_d); col.objects.link(cam); sc.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.2; cam_d.dof.focus_object = bird
def place(t):
    p = bird_at(t); p2 = bird_at(t + 0.05); d = (p2 - p).normalized()
    bird.location = p; bird.rotation_euler = (math.radians(4), -0.25*math.cos(t*0.9)*0.6, math.atan2(-d.x, d.y))
    fl = math.sin(t*2*math.pi*2.6)
    for pv, s in WINGS: pv.rotation_euler = (0, math.radians(32)*fl*s, 0)
    k = ease(min(t/DUR, 1))
    off = Vector((-1.3 + 2.0*k, -3.4 + 0.5*k, 0.75 + 0.2*k))          # orbite lente derrière l'oiseau
    cam.location = p + off
    tgt = p + Vector((0.2 - 0.4*k, 4.0, 0.15))
    cam.rotation_euler = (cam.location - tgt).to_track_quat("Z", "Y").to_euler()

# ------------------------------------------------------------------ rendu
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 5; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, SCALE
sc.view_settings.view_transform = os.environ.get("VT", "Standard"); sc.view_settings.look = "None"; sc.view_settings.exposure = float(os.environ.get("EXPO", "-1.6"))
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 92
sc.view_layers[0].use_pass_mist = True; world.mist_settings.start = 15; world.mist_settings.depth = 110; world.mist_settings.falloff = "LINEAR"
sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes["Render Layers"]; comp = ct.nodes["Composite"]
mix = ct.nodes.new("CompositorNodeMixRGB"); mix.inputs[2].default_value = (0.70, 0.82, 0.97, 1)
mul = ct.nodes.new("CompositorNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.4
ct.links.new(rl.outputs["Mist"], mul.inputs[0]); ct.links.new(mul.outputs[0], mix.inputs[0])
hs = ct.nodes.new("CompositorNodeHueSat"); hs.inputs["Saturation"].default_value = 1.15
ct.links.new(rl.outputs["Image"], mix.inputs[1]); ct.links.new(mix.outputs[0], hs.inputs["Image"]); ct.links.new(hs.outputs["Image"], comp.inputs["Image"])
os.makedirs(out, exist_ok=True)
FR = [int(x) for x in os.environ["FRAMES"].split(",")] if os.environ.get("FRAMES") else range(f0, f1)
for f in FR:
    place(f/FPS); sc.render.filepath = os.path.join(out, f"{f:04d}.jpg"); bpy.ops.render.render(write_still=True)
