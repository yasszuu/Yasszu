"""Plans 3D de l'épisode anguille (SHOT=sargasses|riviere|abysse), style maquette, anguille = forme rouge vif qui ondule.
Usage : SHOT=... [FRAMES=0,70] bl/bin/python eel.py <out_dir> <f0> <f1> [samples] [scale%]"""
import bpy, bmesh, math, sys, os, numpy as np
from mathutils import Vector, Euler

out, f0, f1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 16
SCALE = int(sys.argv[5]) if len(sys.argv) > 5 else 50
FPS, DUR = 30, 4.6
SHOT = os.environ.get("SHOT", "sargasses")
rng = np.random.default_rng(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; col = sc.collection

def mat(name, base, rough, emit=None, emit_s=0.0, sss=0.0, transm=0.0, ior=1.45, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = emit_s
    if sss: b.inputs["Subsurface Weight"].default_value = sss
    if transm: b.inputs["Transmission Weight"].default_value = transm; b.inputs["IOR"].default_value = ior
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    return m
RED = mat("eel", (0.75, 0.0, 0.0), 0.3, emit=(1, 0, 0), emit_s={"abysse": 1.2, "riviere": 0.5, "sargasses": 0.25}[SHOT])

def obj_from(name, verts, faces, m, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.data.materials.append(m); return o
def blob(loc, r, m, sub=2, jit=0.25, seed=0, flat=1.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc); o = bpy.context.object
    rr = np.random.default_rng(seed); bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts: v.co *= 1 + rr.uniform(-jit, jit); v.co.z *= flat
    bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(m); return o
def fast_blobs(name, specs, m, sub=1, jit=0.3):
    """Beaucoup de galets / algues dans UN seul mesh (rapide) : specs = [(x, y, z, r, flat, seed)]."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1); tpl = bpy.context.object
    tv = np.array([v.co[:] for v in tpl.data.vertices]); tf = [list(p.vertices) for p in tpl.data.polygons]
    bpy.data.objects.remove(tpl, do_unlink=True)
    V, F = [], []
    for (x, y, z, r, flat, seed) in specs:
        rr = np.random.default_rng(seed); v = tv*(1 + rr.uniform(-jit, jit, (len(tv), 1)))*r; v[:, 2] *= flat
        b0 = len(V); V.extend((v + [x, y, z]).tolist()); F.extend([[b0 + i for i in f] for f in tf])
    return obj_from(name, V, F, m)
def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); objs[0].name = name; return objs[0]

# ------------------------------------------------------------------ l'anguille : courbe épaisse, effilée, qui ondule
NP, LEN = 48, 1.3
cu = bpy.data.curves.new("eelc", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.032; cu.bevel_resolution = 6; cu.use_fill_caps = True
sp = cu.splines.new("POLY"); sp.points.add(NP - 1)
for i, p in enumerate(sp.points):
    s = i/(NP - 1); p.radius = min(1, 0.7 + s*2.5) * (1 if s < 0.55 else max(0.06, 1 - ((s - 0.55)/0.45)**1.6))
eel = bpy.data.objects.new("eel", cu); col.objects.link(eel); cu.materials.append(RED)
def undulate(t, amp=0.09, speed=7.0):
    for i, p in enumerate(sp.points):
        s = i/(NP - 1)                                         # 0 = tête (avant, +Y), 1 = queue
        y = -s*LEN; x = amp*(0.25 + 0.75*s)*math.sin(2*math.pi*1.6*s - speed*t)
        p.co = (x, y, 0, 1)

# ------------------------------------------------------------------ décors
def sky(elev, rot, dust, strength=0.3):
    world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
    s = wn.nodes.new("ShaderNodeTexSky"); s.sky_type = "NISHITA"; s.sun_elevation = math.radians(elev); s.sun_rotation = math.radians(rot); s.dust_density = dust
    wn.links.new(s.outputs["Color"], wn.nodes["Background"].inputs["Color"]); wn.nodes["Background"].inputs["Strength"].default_value = strength
    return world
def sun(elev, rot, energy, color):
    l = bpy.data.lights.new("sun", "SUN"); l.energy = energy; l.color = color; l.angle = math.radians(2)
    o = bpy.data.objects.new("sun", l); col.objects.link(o); o.rotation_euler = Euler((math.radians(90 - elev), 0, math.radians(rot - 180)), "XYZ")

if SHOT == "sargasses":
    # mer tropicale calme + nappes d'algues dorées jusqu'à l'horizon
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 40, 0)); w = bpy.context.object; w.scale = (300, 300, 1)
    wm = mat("sea", (0.0, 0.05, 0.12), 0.06); nt = wm.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = 18; tx.inputs["Detail"].default_value = 3
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.1
    nt.links.new(tx.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"]); w.data.materials.append(wm)
    ALG = mat("algae", (0.42, 0.25, 0.03), 0.5, sss=0.2)
    specs = []
    for m_ in range(110):
        cx, cy = (rng.uniform(-4, 4), rng.uniform(0.5, 12)) if m_ < 45 else (rng.uniform(-14, 14), rng.uniform(1.5, 60)); n = rng.integers(90, 220); L = rng.uniform(1.0, 4.0); ang = rng.uniform(-0.4, 0.4)
        if abs(cx) < 0.55 and cy < 9: cx += 1.2*np.sign(cx + 1e-3)            # chenal libre pour l'anguille
        for k in range(n):
            u, v = rng.normal(0, L/2.5), rng.normal(0, 0.35)
            x = cx + u*math.sin(ang) + v*math.cos(ang); y = cy + u*math.cos(ang) - v*math.sin(ang)
            specs.append((x, y, 0.02, rng.uniform(0.035, 0.08), 0.6, int(rng.integers(1e6))))
    fast_blobs("algae", specs, ALG, sub=2, jit=0.15)
    world = sky(25, 160, 1.2); sun(25, 160, 3.0, (1.0, 0.95, 0.85)); EXPO = -1.7
    def eel_at(t): return Vector((0.15*math.sin(t*0.7), 0.6 + 1.1*t, 0.012)), 0.0
    def cam_at(t, p):
        k = t/DUR; return p + Vector((-1.0 + 1.4*k, -2.4, 0.95 - 0.15*k)), p + Vector((0.1, 2.2, -0.2))
elif SHOT == "riviere":
    # rivière en maquette : berges vertes, galets, eau claire ; l'anguille remonte le courant
    NX, NY = 220, 360; xs = np.linspace(-6, 6, NX); ys = np.linspace(-4, 30, NY); XX, YY = np.meshgrid(xs, ys)
    cxr = 0.6*np.sin(YY*0.18); d = np.abs(XX - cxr) - 1.1
    H = np.where(d < 0, -0.05 - 0.15*np.cos(np.clip(-d/1.1, 0, 1)*math.pi/2), 0.62*np.clip(d/0.5, 0, 1)**0.7 + 0.08*np.sin(XX*1.3)*np.sin(YY*0.9)*np.clip(d, 0, 1))
    ii = np.arange(NX*NY).reshape(NY, NX)
    tv = np.stack([XX.ravel(), YY.ravel(), H.ravel()], 1).tolist()
    tf = np.stack([ii[:-1, :-1].ravel(), ii[:-1, 1:].ravel(), ii[1:, 1:].ravel(), ii[1:, :-1].ravel()], 1).tolist()
    GR = bpy.data.materials.new("bank"); GR.use_nodes = True; gnt = GR.node_tree; gb = gnt.nodes["Principled BSDF"]; gb.inputs["Roughness"].default_value = 0.8
    sep = gnt.nodes.new("ShaderNodeSeparateXYZ"); geo = gnt.nodes.new("ShaderNodeNewGeometry"); rmp = gnt.nodes.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position = 0.12; rmp.color_ramp.elements[0].color = (0.16, 0.17, 0.14, 1)
    rmp.color_ramp.elements[1].position = 0.3; rmp.color_ramp.elements[1].color = (0.10, 0.28, 0.07, 1)
    gnt.links.new(geo.outputs["Position"], sep.inputs[0]); gnt.links.new(sep.outputs["Z"], rmp.inputs["Fac"]); gnt.links.new(rmp.outputs["Color"], gb.inputs["Base Color"])
    obj_from("banks", tv, tf, GR)
    ROCK = mat("rock", (0.45, 0.43, 0.4), 0.7)
    specs = []
    for k in range(260):
        y = rng.uniform(-3, 28); x = 0.6*math.sin(y*0.18) + rng.uniform(-1.3, 1.3)
        if abs(x - 0.6*math.sin(y*0.18)) < 0.35 and y < 8: continue
        r = rng.uniform(0.04, 0.16) if k > 30 else rng.uniform(0.18, 0.32)
        specs.append((x, y, -0.12 + r*0.3, r, 0.6, k))
    fast_blobs("rocks", specs, ROCK, sub=2, jit=0.2)
    for k in range(40):                                       # arbres low-poly sur les berges
        side = rng.choice([-1, 1]); y = rng.uniform(0, 30); x = side*rng.uniform(2.2, 5.5)
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=rng.uniform(0.4, 0.7), depth=rng.uniform(1.4, 2.4), location=(x, y, 1.4))
        tr = bpy.context.object; tr.data.materials.append(mat(f"leaf{k}", (0.05, 0.18 + rng.uniform(0, 0.08), 0.06), 0.8))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 13, 0.16)); w = bpy.context.object; w.scale = (12, 40, 1)
    WM = mat("river", (0.75, 0.92, 0.90), 0.02, transm=1.0, ior=1.33); nt = WM.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = 9; tx.inputs["Detail"].default_value = 4
    mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15
    nt.links.new(tx.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"]); w.data.materials.append(WM)
    FLOW = mp
    world = sky(30, 140, 1.0); sun(30, 140, 3.0, (1.0, 0.93, 0.82)); EXPO = -2.15
    def eel_at(t): y = 0.4 + 0.75*t; return Vector((0.6*math.sin(y*0.18) + 0.08*math.sin(t*1.5), y, 0.0)), 0.0
    def cam_at(t, p):
        k = t/DUR; return p + Vector((0.6 - 0.9*k, -1.9, 0.85)), p + Vector((-0.05, 1.8, -0.1))
else:
    # abysse : colonne d'eau bleue → noir, neige marine, l'anguille plonge
    world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True; wn = world.node_tree
    tc = wn.nodes.new("ShaderNodeTexCoord"); sp_ = wn.nodes.new("ShaderNodeSeparateXYZ"); rm = wn.nodes.new("ShaderNodeValToRGB")
    rm.color_ramp.elements[0].position = 0.3; rm.color_ramp.elements[0].color = (0.0, 0.004, 0.012, 1)
    rm.color_ramp.elements[1].position = 0.75; rm.color_ramp.elements[1].color = (0.03, 0.30, 0.50, 1)
    mapr = wn.nodes.new("ShaderNodeMapRange"); mapr.inputs["From Min"].default_value = -1; mapr.inputs["From Max"].default_value = 1
    wn.links.new(tc.outputs["Generated"], sp_.inputs[0]); wn.links.new(sp_.outputs["Z"], mapr.inputs["Value"]); wn.links.new(mapr.outputs["Result"], rm.inputs["Fac"])
    wn.links.new(rm.outputs["Color"], wn.nodes["Background"].inputs["Color"]); wn.nodes["Background"].inputs["Strength"].default_value = 1.0
    l = bpy.data.lights.new("top", "SUN"); l.energy = 0.8; l.color = (0.4, 0.7, 1.0); lo = bpy.data.objects.new("top", l); col.objects.link(lo)
    SNOW = mat("snow", (0.6, 0.8, 1), 0.5, emit=(0.6, 0.85, 1.0), emit_s=1.6)
    vv, ff = [], []
    for k in range(1800):                                     # neige marine (petits tétraèdres)
        c = np.array([rng.uniform(-1.8, 1.8), rng.uniform(-1, 9), rng.uniform(-8, 1.5)]); r = rng.uniform(0.002, 0.006); b0 = len(vv)
        for q in ([1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]): vv.append(tuple(c + r*np.array(q)))
        ff += [[b0, b0+1, b0+2], [b0, b0+3, b0+1], [b0, b0+2, b0+3], [b0+1, b0+3, b0+2]]
    obj_from("snow", vv, ff, SNOW, smooth=False)
    # rayons de lumière venant de la surface (plans émissifs dégradés)
    RAY = bpy.data.materials.new("ray"); RAY.use_nodes = True; rn = RAY.node_tree; rn.nodes.remove(rn.nodes["Principled BSDF"])
    em = rn.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.35, 0.7, 1.0, 1); em.inputs["Strength"].default_value = 2.6
    tr = rn.nodes.new("ShaderNodeBsdfTransparent"); mx = rn.nodes.new("ShaderNodeMixShader"); tcr = rn.nodes.new("ShaderNodeTexCoord")
    sx = rn.nodes.new("ShaderNodeSeparateXYZ"); gr = rn.nodes.new("ShaderNodeMapRange"); gr.inputs["From Min"].default_value = 0; gr.inputs["From Max"].default_value = 1
    gr.inputs["To Min"].default_value = 1; gr.inputs["To Max"].default_value = 0.75
    rn.links.new(tcr.outputs["Generated"], sx.inputs[0]); rn.links.new(sx.outputs["Z"], gr.inputs["Value"]); rn.links.new(gr.outputs["Result"], mx.inputs[0])
    rn.links.new(em.outputs[0], mx.inputs[1]); rn.links.new(tr.outputs[0], mx.inputs[2]); rn.links.new(mx.outputs[0], rn.nodes["Material Output"].inputs["Surface"])
    RAY.blend_method = "BLEND" if hasattr(RAY, "blend_method") else None
    for k in range(9):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(rng.uniform(-1.8, 1.8), rng.uniform(1.5, 7), -2))
        rb = bpy.context.object; rb.scale = (rng.uniform(0.05, 0.18), rng.uniform(0.05, 0.18), 14); rb.rotation_euler = (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 0)
        rb.data.materials.append(RAY); rb.visible_shadow = False
    EXPO = -0.4
    def eel_at(t): return Vector((0.2*math.sin(t*0.8), 1.4*t, -1.3*t)), -0.7
    def cam_at(t, p):
        k = t/DUR; m = p + Vector((0, -0.45, 0.42)); return m + Vector((1.7 - 0.4*k, -1.2 + 0.4*k, 2.2)), m + Vector((0, 0.1, -0.1))

# ------------------------------------------------------------------ caméra + placement
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 32; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
cam = bpy.data.objects.new("cam", cam_d); col.objects.link(cam); sc.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.0; cam_d.dof.focus_object = eel
def place(t):
    p, pitch = eel_at(t); p2, _ = eel_at(t + 0.05); d = (p2 - p).normalized()
    undulate(t)
    eel.location = p; eel.rotation_euler = (pitch*0.9 if SHOT == "abysse" else 0, 0, math.atan2(-d.x, d.y))
    c, tg = cam_at(t, p); cam.location = c; cam.rotation_euler = (c - tg).to_track_quat("Z", "Y").to_euler()
    if SHOT == "riviere": FLOW.inputs["Location"].default_value = (0, -0.6*t, 0)

# ------------------------------------------------------------------ rendu
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 4
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, SCALE
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = float(os.environ.get("EXPO", EXPO))
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 92
if SHOT == "abysse":
    sc.view_layers[0].use_pass_mist = True; world.mist_settings.start = 0.5; world.mist_settings.depth = 9; world.mist_settings.falloff = "LINEAR"
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes["Render Layers"]; comp = ct.nodes["Composite"]
    mx = ct.nodes.new("CompositorNodeMixRGB"); mx.inputs[2].default_value = (0.005, 0.04, 0.09, 1)
    ct.links.new(rl.outputs["Mist"], mx.inputs[0]); ct.links.new(rl.outputs["Image"], mx.inputs[1]); ct.links.new(mx.outputs[0], comp.inputs["Image"])
os.makedirs(out, exist_ok=True)
FR = [int(x) for x in os.environ["FRAMES"].split(",")] if os.environ.get("FRAMES") else range(f0, f1)
for f in FR:
    place(f/FPS); sc.render.filepath = os.path.join(out, f"{f:04d}.jpg"); bpy.ops.render.render(write_still=True)
