"""Watermelon "N Cuts" physics animation, built entirely with bpy.

Usage: python watermelon.py [--still FRAME ...] [--out DIR] [--res W H] [--samples N]
"""
import argparse, math, os, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix

ap = argparse.ArgumentParser()
ap.add_argument("--cuts", type=int, default=5)
ap.add_argument("--still", type=int, nargs="*", default=None)
ap.add_argument("--out", default="render")
ap.add_argument("--res", type=int, nargs=2, default=[540, 960])
ap.add_argument("--samples", type=int, default=24)
ap.add_argument("--blend", default=None)
ap.add_argument("--from-frame", type=int, default=1)
args = ap.parse_args(sys.argv[1:])

random.seed(4)
FPS = 30
END = 150
CUT_START, CUT_LEN, CUT_GAP = 10, 9, 11
RELEASE = CUT_START + args.cuts * CUT_GAP + 6
R = 1.0                       # melon radius
SQ = Vector((1.0, 1.0, 0.9))  # ellipsoid squash
C = Vector((0, 0, 2.15))      # melon centre while hovering

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = FPS
scn.frame_start, scn.frame_end = 1, END

# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf

def simple_mat(name, col, rough=0.5, metal=0.0, emit=0.0, sss=0.0):
    m, nt, b = node_mat(name)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
    return m

def orig_coord(nt):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_type = "GEOMETRY"
    a.attribute_name = "orig"
    return a.outputs["Vector"]

def math_node(nt, op, a, b=None, c=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]

def ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    while len(els) < len(stops):
        els.new(0.5)
    for e, (p, c) in zip(els, stops):
        e.position = p
        e.color = (*c, 1)
    nt.links.new(fac, r.inputs[0])
    return r.outputs[0]

# rind: zig-zag dark stripes running pole to pole
rind, nt, b = node_mat("Rind")
p = orig_coord(nt)
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(p, sep.inputs[0])
ang = math_node(nt, "ARCTAN2", sep.outputs[1], sep.outputs[0])
zig = math_node(nt, "SINE", math_node(nt, "MULTIPLY", sep.outputs[2], 22.0))
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3.5
noise.inputs["Detail"].default_value = 6
nt.links.new(p, noise.inputs["Vector"])
warp = math_node(nt, "ADD", math_node(nt, "MULTIPLY", zig, 0.09),
                 math_node(nt, "MULTIPLY", noise.outputs["Fac"], 0.35))
stripe = math_node(nt, "SINE", math_node(nt, "MULTIPLY", math_node(nt, "ADD", ang, warp), 9.0))
col = ramp(nt, math_node(nt, "MULTIPLY_ADD", stripe, 0.5, 0.5),
           [(0.30, (0.012, 0.075, 0.012)), (0.55, (0.10, 0.36, 0.05))])
fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 40
nt.links.new(p, fine.inputs["Vector"])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
mix.inputs["Factor"].default_value = 0.25
nt.links.new(col, mix.inputs[6]); nt.links.new(fine.outputs["Color"], mix.inputs[7])
nt.links.new(mix.outputs[2], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.32
b.inputs["Coat Weight"].default_value = 0.4
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
nt.links.new(fine.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs[0], b.inputs["Normal"])

# flesh: radial gradient (red -> pale -> white -> green skin) + black seeds
flesh, nt, b = node_mat("Flesh")
p = orig_coord(nt)
div = nt.nodes.new("ShaderNodeVectorMath"); div.operation = "DIVIDE"
nt.links.new(p, div.inputs[0]); div.inputs[1].default_value = SQ
ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
nt.links.new(div.outputs[0], ln.inputs[0])
r = ln.outputs["Value"]
col = ramp(nt, r, [(0.0, (0.80, 0.03, 0.06)), (0.78, (0.85, 0.08, 0.10)),
                   (0.86, (0.95, 0.55, 0.50)), (0.885, (0.92, 0.95, 0.80)),
                   (0.955, (0.60, 0.85, 0.45)), (0.975, (0.05, 0.20, 0.04))])
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 5.5
vor.inputs["Randomness"].default_value = 1.0
nt.links.new(p, vor.inputs["Vector"])
seed = math_node(nt, "LESS_THAN", vor.outputs["Distance"], 0.07)
inband = math_node(nt, "MULTIPLY", math_node(nt, "GREATER_THAN", r, 0.35),
                   math_node(nt, "LESS_THAN", r, 0.72))
seedf = math_node(nt, "MULTIPLY", seed, inband)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(seedf, mix.inputs["Factor"])
nt.links.new(col, mix.inputs[6]); mix.inputs[7].default_value = (0.01, 0.008, 0.006, 1)
nt.links.new(mix.outputs[2], b.inputs["Base Color"])
grain = nt.nodes.new("ShaderNodeTexNoise"); grain.inputs["Scale"].default_value = 60
grain.inputs["Detail"].default_value = 8
nt.links.new(p, grain.inputs["Vector"])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs[0], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.22
b.inputs["Subsurface Weight"].default_value = 0.25
b.inputs["Subsurface Radius"].default_value = (0.4, 0.05, 0.05)
b.inputs["Coat Weight"].default_value = 0.6
b.inputs["Coat Roughness"].default_value = 0.1

# wood board
wood, nt, b = node_mat("Wood")
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.4, 6.0, 0.4)
nt.links.new(tc.outputs["Object"], mp.inputs[0])
wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = "RINGS"
wave.inputs["Scale"].default_value = 3.0; wave.inputs["Distortion"].default_value = 6
wave.inputs["Detail"].default_value = 3
nt.links.new(mp.outputs[0], wave.inputs[0])
col = ramp(nt, wave.outputs["Fac"], [(0.2, (0.42, 0.24, 0.11)), (0.8, (0.62, 0.40, 0.20))])
nt.links.new(col, b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.55

floor_mat = simple_mat("Studio", (0.055, 0.055, 0.06), rough=0.6)
cutline_mat = simple_mat("CutLine", (0.55, 0.0, 0.02), rough=0.3, emit=0.4)
steel = simple_mat("Steel", (0.85, 0.86, 0.9), rough=0.12, metal=1.0)
handle_mat = simple_mat("Handle", (0.05, 0.05, 0.06), rough=0.4)
juice_mat = simple_mat("Juice", (0.9, 0.15, 0.2), rough=0.05)
spray_mat = simple_mat("Spray", (1.0, 0.85, 0.85), rough=0.1, emit=0.3)
text_mat = simple_mat("Text", (1, 1, 1), emit=3.0)

# ---------------------------------------------------------------- world, studio
world = bpy.data.worlds.new("W"); scn.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.012, 0.014, 1)

# seamless cyclorama: floor curving up into a back wall
prof = [(-25, 0)]
yb, rad = 5.0, 4.0
for i in range(17):
    a = i / 16 * math.pi / 2
    prof.append((yb + rad * math.sin(a), rad - rad * math.cos(a)))
prof.append((yb + rad, 30))
bm = bmesh.new()
rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-30, 30)]
for i in range(len(prof) - 1):
    bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
me = bpy.data.meshes.new("Cyc"); bm.to_mesh(me); bm.free()
for poly in me.polygons:
    poly.use_smooth = True
cyc = bpy.data.objects.new("Cyc", me); scn.collection.objects.link(cyc)
me.materials.append(floor_mat)

def link(o):
    scn.collection.objects.link(o)
    return o

# board
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.09))
board = bpy.context.object; board.name = "Board"
board.scale = (3.2, 1.25, 0.18)
bpy.ops.object.transform_apply(scale=True)
bv = board.modifiers.new("bev", "BEVEL"); bv.width = 0.05; bv.segments = 4
board.data.materials.append(wood)
# handle hole
bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.35, 0, 0.09))
hole = bpy.context.object; hole.scale = (0.12, 0.3, 0.5); hole.hide_render = hole.hide_viewport = True
boo = board.modifiers.new("hole", "BOOLEAN"); boo.object = hole
board.modifiers.move(1, 0)

# lights
def area(name, loc, size, power, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = color
    o = bpy.data.objects.new(name, l); o.location = loc
    link(o)
    d = Vector((0, 0, 1.6)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
area("Key", (-4.5, -5.5, 7.0), 5.0, 1400)
area("Fill", (6, -6, 2.5), 6.0, 350, (0.85, 0.9, 1.0))
area("Rim", (2.5, 5.5, 6.0), 3.0, 900)

# camera
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); link(cam)
cam.location = (0, -11.0, 2.5)
cam.rotation_euler = (Vector((0, 0, 2.05)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 50
scn.camera = cam

# title
bpy.ops.object.text_add(location=(0, 0.0, 4.85), rotation=(math.radians(90), 0, 0))
txt = bpy.context.object
txt.data.body = f"{args.cuts} Cuts"
txt.data.align_x = "CENTER"; txt.data.size = 0.62
txt.data.extrude = 0.0
txt.data.materials.append(text_mat)
for o in (txt,):
    o.visible_shadow = False

# ---------------------------------------------------------------- cut planes
def rand_unit():
    while True:
        v = Vector([random.uniform(-1, 1) for _ in range(3)])
        if 0.2 < v.length <= 1:
            return v.normalized()

planes = []
base = [Vector((1, 0, 0.15)), Vector((0.3, 1, -0.2)), Vector((0.1, 0.25, 1)),
        Vector((-0.8, 0.6, 0.45)), Vector((0.7, 0.55, -0.6))]
for i in range(args.cuts):
    n = (base[i] if i < len(base) else rand_unit()).normalized()
    d = random.uniform(-0.18, 0.18)
    planes.append((n * d, n))

# ---------------------------------------------------------------- melon pieces
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=R)
for v in bm.verts:
    v.co = Vector((v.co.x * SQ.x, v.co.y * SQ.y, v.co.z * SQ.z))
for f in bm.faces:
    f.smooth = True; f.material_index = 0

def half(src, co, no, keep_pos):
    h = src.copy()
    res = bmesh.ops.bisect_plane(h, geom=h.verts[:] + h.edges[:] + h.faces[:], plane_co=co,
                                 plane_no=no, clear_inner=keep_pos, clear_outer=not keep_pos)
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if len(h.verts) < 4:
        h.free(); return None
    if edges:
        new = bmesh.ops.edgeloop_fill(h, edges=edges)["faces"]
        if not new:
            new = bmesh.ops.contextual_create(h, geom=edges)["faces"]
        for f in new:
            f.smooth = False; f.material_index = 1
    return h

pieces = [bm]
for co, no in planes:
    nxt = []
    for pc in pieces:
        for side in (True, False):
            h = half(pc, co, no, side)
            if h is not None:
                nxt.append(h)
        pc.free()
    pieces = nxt
print("pieces:", len(pieces))

piece_objs = []
for i, pb in enumerate(pieces):
    bmesh.ops.recalc_face_normals(pb, faces=pb.faces[:])
    cen = sum((v.co for v in pb.verts), Vector()) / len(pb.verts)
    me = bpy.data.meshes.new(f"P{i}")
    pb.to_mesh(me); pb.free()
    at = me.attributes.new("orig", "FLOAT_VECTOR", "POINT")
    for k, v in enumerate(me.vertices):
        at.data[k].vector = v.co.copy()
    me.transform(Matrix.Translation(-cen))
    me.materials.append(rind); me.materials.append(flesh)
    o = bpy.data.objects.new(f"Piece{i}", me); link(o)
    o["off"] = cen
    piece_objs.append(o)

# ---------------------------------------------------------------- hover / rotation
def spin(f):
    """Melon local->world transform while hovering (slow turn + gentle bob)."""
    t = (f - 1) / FPS
    ang = 0.5 * t
    bob = 0.04 * math.sin(t * 2.2)
    return Matrix.Translation(C + Vector((0, 0, bob))) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(0.25, 4, "X")

for f in range(1, RELEASE + 1):
    M = spin(f)
    for o in piece_objs:
        o.matrix_world = M @ Matrix.Translation(o["off"])
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- cut lines + knife
def ell_hit(p0, d):
    a = sum((d[i] / SQ[i]) ** 2 for i in range(3))
    b = 2 * sum(p0[i] * d[i] / SQ[i] ** 2 for i in range(3))
    c = sum((p0[i] / SQ[i]) ** 2 for i in range(3)) - R * R
    return (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)

def basis(n):
    u = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized()
    return u, n.cross(u).normalized()

# knife model (local: +X radial outward, origin on the cut line, Z = plane normal)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1)
for v in bm.verts:
    x = (v.co.x + 0.5)
    v.co = Vector((-1.05 + x * 1.45, v.co.y * 0.17, v.co.z * 0.014))
    if x < 0.5 and v.co.y > 0:  # taper toward tip
        v.co.y = -0.03
kme = bpy.data.meshes.new("Blade"); bm.to_mesh(kme); bm.free()
kme.materials.append(steel)
knife = bpy.data.objects.new("Knife", kme); link(knife)
knife.rotation_mode = "QUATERNION"
prev_q = None
bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.7, location=(0.73, 0, 0), rotation=(0, math.pi / 2, 0))
hnd = bpy.context.object; hnd.data.materials.append(handle_mat); hnd.parent = knife
bv = hnd.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3

cut_curves = []
for i, (co, n) in enumerate(planes):
    u, v = basis(n)
    pts = []
    N = 96
    for k in range(N + 1):
        th = 2 * math.pi * k / N
        d = math.cos(th) * u + math.sin(th) * v
        pts.append(co + d * (ell_hit(co, d) * 1.004))
    cd = bpy.data.curves.new(f"Cut{i}", "CURVE"); cd.dimensions = "3D"
    sp = cd.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for k, pnt in enumerate(pts):
        sp.points[k].co = (*pnt, 1)
    cd.bevel_depth = 0.011; cd.bevel_resolution = 2
    cd.materials.append(cutline_mat)
    co_ = bpy.data.objects.new(f"Cut{i}", cd); link(co_)
    cut_curves.append((co_, pts, u, v, n))
    s = CUT_START + i * CUT_GAP
    cd.bevel_factor_end = 0.0; cd.keyframe_insert("bevel_factor_end", frame=s)
    cd.bevel_factor_end = 1.0; cd.keyframe_insert("bevel_factor_end", frame=s + CUT_LEN)
    co_.hide_render = True; co_.keyframe_insert("hide_render", frame=1)
    co_.hide_render = False; co_.keyframe_insert("hide_render", frame=s)
    co_.hide_render = True; co_.keyframe_insert("hide_render", frame=RELEASE + 1)

for f in range(1, RELEASE + 2):
    M = spin(f)
    for co_, *_ in cut_curves:
        co_.matrix_world = M
        co_.keyframe_insert("location", frame=f); co_.keyframe_insert("rotation_euler", frame=f)
    active = None
    for i, (co_, pts, u, v, n) in enumerate(cut_curves):
        s = CUT_START + i * CUT_GAP
        if s - 2 <= f <= s + CUT_LEN + 2:
            active = (i, co_, pts, u, v, n, s)
    if active:
        i, co_, pts, u, v, n, s = active
        t = min(max((f - s) / CUT_LEN, 0.0), 1.0)
        t = t * t * (3 - 2 * t)
        k = t * (len(pts) - 1)
        p = pts[int(k)].lerp(pts[min(int(k) + 1, len(pts) - 1)], k - int(k))
        radial = (p - planes[i][0]).normalized()
        tang = n.cross(radial)
        rot = Matrix((radial, tang, n)).transposed().to_4x4()
        knife.matrix_world = M @ Matrix.Translation(p) @ rot
        q = knife.rotation_quaternion.copy()
        if prev_q is not None and q.dot(prev_q) < 0:
            q.negate(); knife.rotation_quaternion = q
        prev_q = q
        knife.hide_render = False
    else:
        knife.hide_render = True
    knife.keyframe_insert("location", frame=f)
    knife.keyframe_insert("rotation_quaternion", frame=f)
    knife.keyframe_insert("hide_render", frame=f)
    hnd.hide_render = knife.hide_render
    hnd.keyframe_insert("hide_render", frame=f)

for o in [knife, hnd] + [c[0] for c in cut_curves]:
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT" if fc.data_path == "hide_render" else "LINEAR"

# ---------------------------------------------------------------- physics
bpy.ops.rigidbody.world_add()
rbw = scn.rigidbody_world
rbw.substeps_per_frame = 20; rbw.solver_iterations = 30
rbw.point_cache.frame_start = 1; rbw.point_cache.frame_end = END

def add_rb(o, typ, **kw):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects:
        x.select_set(False)
    o.select_set(True)
    bpy.ops.rigidbody.object_add(type=typ)
    for k, v in kw.items():
        setattr(o.rigid_body, k, v)

add_rb(board, "PASSIVE", collision_shape="BOX", friction=0.8, restitution=0.1)
add_rb(cyc, "PASSIVE", collision_shape="MESH", friction=0.7, restitution=0.1)
for o in piece_objs:
    add_rb(o, "ACTIVE", collision_shape="CONVEX_HULL", mass=0.5, friction=0.6,
           restitution=0.15, collision_margin=0.002, linear_damping=0.05, angular_damping=0.1)
    o.rigid_body.kinematic = True
    o.rigid_body.keyframe_insert("kinematic", frame=RELEASE)
    o.rigid_body.kinematic = False
    o.rigid_body.keyframe_insert("kinematic", frame=RELEASE + 1)

# outward burst
bpy.ops.object.effector_add(type="FORCE", location=C)
fld = bpy.context.object
fld.field.shape = "POINT"; fld.field.falloff_power = 0.0
for f, s in ((RELEASE, 0), (RELEASE + 1, 40), (RELEASE + 4, 40), (RELEASE + 5, 0)):
    fld.field.strength = s
    fld.field.keyframe_insert("strength", frame=f)

# ---------------------------------------------------------------- juice particles
def drop(name, mat, r):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(0, 0, -50))
    d = bpy.context.object; d.name = name; d.data.materials.append(mat)
    for p in d.data.polygons:
        p.use_smooth = True
    return d

juice = drop("JuiceDrop", juice_mat, 1.0)
spray = drop("SprayDrop", spray_mat, 1.0)

def emitter(obj, inst, count, start, end, vel, rnd, size, life=60):
    obj.modifiers.new("ps", "PARTICLE_SYSTEM")
    ps = obj.particle_systems[-1].settings
    ps.count = count; ps.frame_start = start; ps.frame_end = end; ps.lifetime = life
    ps.normal_factor = vel; ps.factor_random = rnd
    ps.render_type = "OBJECT"; ps.instance_object = inst
    ps.particle_size = size; ps.size_random = 0.6
    ps.use_rotations = True
    obj.show_instancer_for_render = False
    return ps

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.85, location=C)
burst = bpy.context.object; burst.name = "Burst"; burst.hide_render = False
burst.scale = SQ
emitter(burst, juice, 260, RELEASE, RELEASE + 3, 3.2, 1.6, 0.03, life=90)

# fine spray coming off the blade while cutting
emitter(knife, spray, 220, CUT_START, RELEASE - 6, 0.6, 1.2, 0.012, life=25)

for o in (cyc, board):
    o.modifiers.new("col", "COLLISION")

# ---------------------------------------------------------------- render
r = scn.render
r.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = args.samples
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 6
r.resolution_x, r.resolution_y = args.res
r.resolution_percentage = 100
r.use_motion_blur = True
r.motion_blur_shutter = 0.35
r.image_settings.file_format = "PNG"
scn.view_settings.view_transform = "AgX"
scn.view_settings.look = "AgX - Medium High Contrast"

if args.blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))

os.makedirs(args.out, exist_ok=True)
r.filepath = os.path.join(os.path.abspath(args.out), "")
if args.still is not None:
    # step the simulation forward so rigid-body state is valid
    last = max(args.still)
    for f in range(1, last + 1):
        scn.frame_set(f)
        if f in args.still:
            r.filepath = os.path.join(os.path.abspath(args.out), f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
else:
    # render frame by frame, stepping sequentially so the rigid-body sim is evaluated
    for f in range(1, END + 1):
        scn.frame_set(f)
        if f >= args.from_frame:
            r.filepath = os.path.join(os.path.abspath(args.out), f"{f:04d}.png")
            bpy.ops.render.render(write_still=True)
