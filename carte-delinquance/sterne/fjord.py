"""Démo « maquette » : fjord arctique en argile blanche, rendu Cycles (Blender 4.5, bpy).
Usage : bl/bin/python fjord.py <out_dir> <frame_start> <frame_end> [samples] [scale%]"""
import bpy, bmesh, math, sys, os, numpy as np
from scipy.ndimage import zoom
from mathutils import Vector

out, f0, f1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 48
SCALE = int(sys.argv[5]) if len(sys.argv) > 5 else 100
FPS, DUR = 30, 5.0
rng = np.random.default_rng(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ------------------------------------------------------------------ bruit (numpy)
def vnoise(shape, cells, seed):
    r = np.random.default_rng(seed).random((cells[0] + 3, cells[1] + 3))
    z = zoom(r, ((shape[0] + 3*shape[0]/cells[0])/r.shape[0], (shape[1] + 3*shape[1]/cells[1])/r.shape[1]), order=3)
    return z[:shape[0], :shape[1]]
def fbm(shape, base, octaves, seed, ridged=False):
    acc, amp, tot = np.zeros(shape), 1.0, 0.0
    for o in range(octaves):
        c = (max(2, int(base[0]*2**o)), max(2, int(base[1]*2**o)))
        n = vnoise(shape, c, seed + o)
        if ridged: n = 1 - np.abs(2*n - 1); n = n*n
        acc += n*amp; tot += amp; amp *= 0.5
    return acc/tot

# ------------------------------------------------------------------ terrain : fjord sinueux
NX, NY = 760, 1000
X0, X1, Y0, Y1 = -9.0, 9.0, -4.0, 38.0
xs = np.linspace(X0, X1, NX); ys = np.linspace(Y0, Y1, NY)
XX, YY = np.meshgrid(xs, ys)
cx = 0.9*np.sin(YY*0.16) + 0.4*np.sin(YY*0.41 + 1.3)
wid = 1.7 + 0.5*np.sin(YY*0.09 + 0.5)
d = np.abs(XX - cx) - wid
ridg = fbm((NY, NX), (6, 3), 6, 11, ridged=True)
bumps = fbm((NY, NX), (14, 7), 5, 21)
wall = np.clip(d/3.2, 0, 1); wall = wall*wall*(3 - 2*wall)
tt = wall*6 + bumps*1.2; fr = tt - np.floor(tt)
terr = (np.floor(tt) + fr**3)/6*0.3 + wall*0.7                     # strates douces
H = -0.35 + terr*(3.0 + 2.6*ridg) + np.clip(d, 0, None)*0.12 + (bumps - 0.5)*0.5*np.clip(d + 0.6, 0, 1)
H += np.clip(d - 4, 0, None)*0.5*ridg            # sommets plus hauts en retrait
mesh = bpy.data.meshes.new("terrain")
verts = np.stack([XX.ravel(), YY.ravel(), H.ravel()], 1)
ii = np.arange(NX*NY).reshape(NY, NX)
faces = np.stack([ii[:-1, :-1].ravel(), ii[:-1, 1:].ravel(), ii[1:, 1:].ravel(), ii[1:, :-1].ravel()], 1)
mesh.from_pydata(verts.tolist(), [], faces.tolist()); mesh.update()
for p in mesh.polygons: p.use_smooth = True
terrain = bpy.data.objects.new("terrain", mesh); sc.collection.objects.link(terrain)

def mat(name, col, rough, sss=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.4, 0.7, 1.0)
    return m
clay = mat("clay", (0.82, 0.84, 0.88), 0.55)
terrain.data.materials.append(clay)

# ------------------------------------------------------------------ eau : noire, très brillante, petites vagues
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, (Y0 + Y1)/2, 0))
water = bpy.context.object; water.scale = (X1 - X0, Y1 - Y0, 1)
wm = bpy.data.materials.new("water"); wm.use_nodes = True
nt = wm.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.004, 0.008, 0.016, 1); b.inputs["Roughness"].default_value = 0.04
b.inputs["IOR"].default_value = 1.33
tex = nt.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = 260; tex.inputs["Detail"].default_value = 3
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.12
nt.links.new(tex.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
water.data.materials.append(wm)

# ------------------------------------------------------------------ icebergs
ice = mat("ice", (0.9, 0.95, 1.0), 0.35, sss=0.15)
def cx_at(y): return 0.9*math.sin(y*0.16) + 0.4*math.sin(y*0.41 + 1.3)
BERGS = [(2.6, 0.55, 0.42), (5.5, -0.7, 0.3), (9.0, 0.6, 0.55), (13.5, -0.4, 0.35), (19.0, 0.3, 0.7), (25.0, -0.5, 0.5), (4.0, 1.0, 0.16), (7.2, -0.2, 0.12)]
for k, (y, off, s) in enumerate(BERGS):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1, location=(cx_at(y) + off, y, 0))
    o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = np.random.default_rng(100 + k); ph = r.random(6)*6
    for v in bm.verts:
        p = v.co
        n = 0.25*math.sin(3*p.x + ph[0])*math.sin(2.5*p.y + ph[1]) + 0.18*math.sin(5*p.z + ph[2]) + 0.1*math.sin(9*p.x + 7*p.y + ph[3])
        p *= 1 + n
        p.z = max(p.z, -0.9)*(1.0 if p.z > 0 else 0.6)
        if p.z > 0.55: p.z = 0.55 + (p.z - 0.55)*0.25          # sommet tabulaire
    bm.to_mesh(o.data); bm.free()
    o.scale = (s*(1 + r.random()*0.6), s*(0.8 + r.random()*0.5), s*(0.7 + r.random()*0.4)); o.rotation_euler[2] = r.random()*6.28
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(ice)

# ------------------------------------------------------------------ lumières : contre-jour bleu froid + accent rouge (comme les références)
def area(name, loc, rot, size, col, power):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.color = col; l.energy = power
    o = bpy.data.objects.new(name, l); o.visible_glossy = name != "back"; o.location = loc; o.rotation_euler = rot; sc.collection.objects.link(o); return o
area("back", (0, 48, 7), (math.radians(-95), 0, 0), 12, (0.35, 0.6, 1.0), 26000)
red = area("red", (-1.6, 1.0, 0.5), (0, 0, 0), 0.6, (1.0, 0.1, 0.05), 28)
trk = red.constraints.new("TRACK_TO"); tg0 = bpy.data.objects.new("redtg", None); sc.collection.objects.link(tg0)
tg0.location = (cx_at(2.6) + 0.55, 2.6, 0.1); trk.target = tg0; trk.track_axis = "TRACK_NEGATIVE_Z"; trk.up_axis = "UP_Y"
area("fill", (3, -6, 7), (math.radians(55), 0, math.radians(-20)), 6, (0.5, 0.68, 1.0), 450)
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.007, 0.016, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

# ------------------------------------------------------------------ caméra : travelling bas sur l'eau + bascule de mise au point
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 22; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 1.6
focus = bpy.data.objects.new("focus", None); sc.collection.objects.link(focus); cam_d.dof.focus_object = focus
def ease(k): return k*k*(3 - 2*k)
def place(t):
    k = ease(min(max(t/DUR, 0), 1))
    y = -1.6 + 3.6*k
    cam.location = (cx_at(y) - 0.15 + 0.25*k, y, 0.16 + 0.22*k)
    tgt = Vector((cx_at(y + 8) + 0.1, y + 8, 0.35 + 0.3*k))
    cam.rotation_euler = (cam.location - tgt).to_track_quat("Z", "Y").to_euler()
    # mise au point : iceberg proche → falaises au fond
    near = Vector((cx_at(2.6) + 0.55, 2.6, 0.2)); far = Vector((cx_at(14) , 14, 1.5))
    m = ease(min(max((t - 1.6)/2.2, 0), 1)); focus.location = near.lerp(far, m)

# ------------------------------------------------------------------ rendu
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, SCALE
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -0.2
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 92
# brume de profondeur : passe Mist mélangée vers un bleu nuit
sc.view_layers[0].use_pass_mist = True; world.mist_settings.start = 5; world.mist_settings.depth = 45; world.mist_settings.falloff = "QUADRATIC"
sc.use_nodes = True; ct = sc.node_tree
rl = ct.nodes["Render Layers"]; comp = ct.nodes["Composite"]
mix = ct.nodes.new("CompositorNodeMixRGB"); mix.inputs[2].default_value = (0.012, 0.025, 0.055, 1)
mul = ct.nodes.new("CompositorNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.55
ct.links.new(rl.outputs["Mist"], mul.inputs[0]); ct.links.new(mul.outputs[0], mix.inputs[0])
ct.links.new(rl.outputs["Image"], mix.inputs[1]); ct.links.new(mix.outputs[0], comp.inputs["Image"])
os.makedirs(out, exist_ok=True)
FR = [int(x) for x in os.environ["FRAMES"].split(",")] if os.environ.get("FRAMES") else range(f0, f1)
for f in FR:
    place(f/FPS)
    sc.render.filepath = os.path.join(out, f"{f:04d}.jpg")
    bpy.ops.render.render(write_still=True)
