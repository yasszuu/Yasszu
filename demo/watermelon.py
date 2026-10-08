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
ap.add_argument("--dump", default=None, help="simulate only and write motion JSON")
ap.add_argument("--from-frame", type=int, default=1)
ap.add_argument("--post", type=int, default=95, help="frames after the burst")
ap.add_argument("--side", type=float, default=1.0, help="throw from the right (1) or left (-1)")
args = ap.parse_args(sys.argv[1:])

random.seed(4)
FPS = 30
ARRIVE = 26                      # melon reaches the apex of its throw
# cuts get denser as their number grows so even 100 cuts stay snappy
CUT_GAP = 3 if args.cuts <= 10 else 2 if args.cuts <= 30 else 1
CUT_START, CUT_LEN = ARRIVE + 2, CUT_GAP
CUT_FRAMES = [CUT_START + i * CUT_GAP for i in range(args.cuts)]
RELEASE = CUT_FRAMES[-1] + CUT_LEN + 3
END = RELEASE + args.post
FULL_CUTS = 6        # cuts beyond this only split the biggest pieces they cross
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
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 6.5
vor.inputs["Randomness"].default_value = 1.0
elong = nt.nodes.new("ShaderNodeVectorMath"); elong.operation = "MULTIPLY"
nt.links.new(p, elong.inputs[0]); elong.inputs[1].default_value = (1.0, 1.0, 0.55)
nt.links.new(elong.outputs[0], vor.inputs["Vector"])
seed = math_node(nt, "LESS_THAN", vor.outputs["Distance"], 0.12)
inband = math_node(nt, "MULTIPLY", math_node(nt, "GREATER_THAN", r, 0.3),
                   math_node(nt, "LESS_THAN", r, 0.76))
seedf = math_node(nt, "MULTIPLY", seed, inband)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(seedf, mix.inputs["Factor"])
nt.links.new(col, mix.inputs[6]); mix.inputs[7].default_value = (0.004, 0.003, 0.002, 1)
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
cam.data.clip_start = 0.05
scn.camera = cam

# title
bpy.ops.object.text_add(location=(0, 0.0, 4.85), rotation=(math.radians(90), 0, 0))
txt = bpy.context.object
txt.data.body = f"{args.cuts} Cut" + ("s" if args.cuts > 1 else "")
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

planes = []   # filled while splitting: (point, normal) in melon space
base = [Vector((1, 0, 0.15)), Vector((0.3, 1, -0.2)), Vector((0.1, 0.25, 1)),
        Vector((-0.8, 0.6, 0.45)), Vector((0.7, 0.55, -0.6)), Vector((-0.5, -0.7, 0.5))]

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

def crosses(pc, co, no):
    d = [(v.co - co).dot(no) for v in pc.verts]
    return min(d) < -0.01 and max(d) > 0.01

def centroid(pc):
    return sum((v.co for v in pc.verts), Vector()) / len(pc.verts)

# each piece carries the side (+1/-1) it ended up on for every cut that split it,
# which is what opens the incisions later
pieces = [(bm, {})]
for i in range(args.cuts):
    if i < FULL_CUTS:
        n = (base[i] if i < len(base) else rand_unit()).normalized()
        co = n * random.uniform(-0.18, 0.18)
        targets = [p for p in pieces if crosses(p[0], co, n)]
    else:
        # a plane through the biggest remaining chunk, splitting up to 3 big pieces it crosses
        pieces.sort(key=lambda p: -p[0].calc_volume())
        n = rand_unit()
        co = centroid(pieces[0][0]) + rand_unit() * 0.03
        targets = [p for p in pieces if crosses(p[0], co, n)][:3]
    planes.append((co, n))
    for p in targets:
        pieces.remove(p)
        for keep_pos in (True, False):
            h = half(p[0], co, n, keep_pos)
            if h is not None:
                pieces.append((h, {**p[1], i: 1.0 if keep_pos else -1.0}))
        p[0].free()
print("pieces:", len(pieces))
piece_sides = {}

piece_objs = []
for i, (pb, sides) in enumerate(pieces):
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
    piece_sides[o.name] = sides
    piece_objs.append(o)

# ---------------------------------------------------------------- throw / hover
THROW_FROM = Vector((0.6 * args.side, -12.5, 1.2))    # behind the camera, low and slightly right
TUMBLE_AXIS = Vector((1.0, 0.25, 0.3)).normalized()

def melon_pose(f):
    """Melon local->world transform: thrown from behind the camera, then hangs at the apex."""
    if f <= ARRIVE:
        t = (f - 1) / (ARRIVE - 1)
        e = 1 - (1 - t) ** 3                       # fast launch, slow arrival
        pos = THROW_FROM.lerp(C, e) + Vector((0, 0, 0.6 * math.sin(math.pi * e)))
        ang = 4.0 * e
    else:
        dt = (f - ARRIVE) / FPS
        pos = C + Vector((0, 0, -0.06 * dt * dt))  # slight sag at the apex
        ang = 4.0 + 0.9 * dt
    return Matrix.Translation(pos) @ Matrix.Rotation(ang, 4, TUMBLE_AXIS)

GAP = 0.034 if args.cuts <= 10 else 0.022   # width each incision opens to

def incision_offset(o, f):
    off = Vector()
    for i, sgn in piece_sides[o.name].items():
        s = CUT_FRAMES[i]
        k = min(max((f - (s + 1)) / 2.0, 0.0), 1.0)   # opens just after the blade passes
        off += planes[i][1] * (sgn * GAP * 0.5 * k)
    return off

for f in range(1, RELEASE + 1):
    M = melon_pose(f)
    for o in piece_objs:
        o.matrix_world = M @ Matrix.Translation(Vector(o["off"]) + incision_offset(o, f))
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- knife (one fast slash per cut)
def basis(n):
    u = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized()
    return u, n.cross(u).normalized()

# local: X = blade length, +Y = cutting edge / travel direction, Z = plane normal
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1)
for v in bm.verts:
    x, y = v.co.x + 0.5, v.co.y + 0.5
    v.co = Vector((-1.45 + x * 2.9, -0.24 + y * 0.24, v.co.z * 0.016))
    if x < 0.5 and y > 0.5:
        v.co.y -= 0.18                 # sloped tip
kme = bpy.data.meshes.new("Blade"); bm.to_mesh(kme); bm.free()
kme.materials.append(steel)
knife = bpy.data.objects.new("Knife", kme); link(knife)
knife.rotation_mode = "QUATERNION"
knife.cycles.use_motion_blur = CUT_LEN >= 3   # fast flurries would smear between cuts
bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.8, location=(1.85, -0.12, 0), rotation=(0, math.pi / 2, 0))
hnd = bpy.context.object; hnd.data.materials.append(handle_mat); hnd.parent = knife
bv = hnd.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3

slash_dir = [random.choice((-1, 1)) for _ in planes]
prev_q = None
for f in range(1, RELEASE + 2):
    M = melon_pose(f)
    active = None
    for i, s in enumerate(CUT_FRAMES):
        if s <= f <= s + CUT_LEN - 1:
            active = (i, s)
    if active:
        i, s = active
        co, n = planes[i]
        u, v = basis(n)
        v = v * slash_dir[i]
        t = (f - s) / 2 if CUT_LEN == 3 else (f - s + 0.5) / CUT_LEN
        p = co + v * (-2.3 + 4.6 * t)
        rot = Matrix((u, v, u.cross(v))).transposed().to_4x4()
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

BURST_AT = melon_pose(RELEASE).translation.copy()
bpy.ops.object.effector_add(type="FORCE", location=BURST_AT)
fld = bpy.context.object
fld.field.shape = "POINT"; fld.field.falloff_power = 0.0
for f, s in ((RELEASE, 0), (RELEASE + 1, 32), (RELEASE + 4, 32), (RELEASE + 5, 0)):
    fld.field.strength = s
    fld.field.keyframe_insert("strength", frame=f)

# camera shake on the burst
cam.keyframe_insert("location", frame=RELEASE)
base_loc = cam.location.copy()
for k, f in enumerate(range(RELEASE + 1, RELEASE + 9)):
    a = 0.05 * (1 - k / 8)
    cam.location = base_loc + Vector((random.uniform(-a, a), 0, random.uniform(-a, a)))
    cam.keyframe_insert("location", frame=f)
cam.location = base_loc
cam.keyframe_insert("location", frame=RELEASE + 9)

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
    ps.particle_size = size; ps.size_random = 0.7
    ps.use_rotations = True
    obj.show_instancer_for_render = False
    return ps

# big splash when it bursts
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.85, location=BURST_AT)
burst = bpy.context.object; burst.name = "Burst"
burst.scale = SQ
emitter(burst, juice, 320, RELEASE, RELEASE + 3, 3.0, 1.6, 0.032, life=90)

# a squirt of juice along every incision: a thin open tube lying in the cut plane,
# its outward-facing side spits droplets radially as the blade goes through
for i, (co, n) in enumerate(planes):
    rad = math.sqrt(max(R * R - co.length_squared, 0.05)) * 0.92
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=rad, radius2=rad, depth=0.03)
    tme = bpy.data.meshes.new(f"Squirt{i}"); bm.to_mesh(tme); bm.free()
    em = bpy.data.objects.new(f"Squirt{i}", tme); link(em)
    rot = n.to_track_quat("Z", "Y").to_matrix().to_4x4()
    for f in range(1, RELEASE + 2):
        em.matrix_world = melon_pose(f) @ Matrix.Translation(co) @ rot
        em.keyframe_insert("location", frame=f); em.keyframe_insert("rotation_euler", frame=f)
    s = CUT_FRAMES[i]
    scale = min(1.0, 8 / args.cuts)
    emitter(em, juice, max(15, int(90 * scale)), s + 1, s + 3, 2.4, 0.9, 0.018, life=60)
    emitter(em, spray, max(10, int(60 * scale)), s + 1, s + 2, 3.2, 1.2, 0.009, life=30)

# fine mist coming off the blade itself
emitter(knife, spray, min(800, 40 * len(planes)), CUT_START, CUT_FRAMES[-1] + CUT_LEN, 0.5, 1.2, 0.01, life=20)

for o in (cyc, board):
    o.modifiers.new("col", "COLLISION")

# ---------------------------------------------------------------- render
r = scn.render
r.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = args.samples
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 4
scn.cycles.diffuse_bounces = 2; scn.cycles.glossy_bounces = 2
scn.cycles.transmission_bounces = 2; scn.cycles.transparent_max_bounces = 4
scn.cycles.caustics_reflective = False; scn.cycles.caustics_refractive = False
scn.cycles.denoising_prefilter = "FAST"
r.use_persistent_data = True
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
if args.dump:
    import json
    track = {o.name: [] for o in piece_objs}
    for f in range(1, END + 1):
        scn.frame_set(f)
        for o in piece_objs:
            track[o.name].append(list(o.matrix_world.translation))
    throw = []
    for f in range(1, END + 1):
        throw.append(list(melon_pose(min(f, RELEASE)).translation))
    json.dump({"fps": FPS, "end": END, "arrive": ARRIVE, "cuts": CUT_FRAMES, "cut_len": CUT_LEN,
               "side": args.side,
               "release": RELEASE, "cam": list(base_loc), "melon": throw, "pieces": track},
              open(args.dump, "w"))
    sys.exit(0)
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
        out_png = os.path.join(os.path.abspath(args.out), f"{f:04d}.png")
        if f >= args.from_frame and not os.path.exists(out_png):   # resumable
            r.filepath = out_png
            bpy.ops.render.render(write_still=True)
