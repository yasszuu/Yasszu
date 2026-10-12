"""Briques communes des plans 3D Gombe (style maquette, chimpanzés = formes rouges)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector, Euler, Quaternion
rng = np.random.default_rng(7)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene
def col(): return bpy.context.scene.collection

def mat(name, base, rough=0.7, emit=None, emit_s=0.0, sss=0.0, transm=0.0, ior=1.45, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = emit_s
    if sss: b.inputs["Subsurface Weight"].default_value = sss
    if transm: b.inputs["Transmission Weight"].default_value = transm; b.inputs["IOR"].default_value = ior
    return m
def vcol_mat(name, rough=0.85, bump=0.0, bump_scale=40.0):
    """Matériau qui lit l'attribut couleur 'col' (+ léger bruit de bump)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.2
    a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = "col"; nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
    if bump:
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = bump_scale; n.inputs["Detail"].default_value = 8
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def obj_from(name, verts, faces, m=None, smooth=True, link=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me)
    if link: col().objects.link(o)
    if m: o.data.materials.append(m)
    return o
def grid_mesh(name, X, Y, H, colors=None, m=None):
    ny, nx = H.shape; ii = np.arange(nx*ny).reshape(ny, nx)
    v = np.stack([X.ravel(), Y.ravel(), H.ravel()], 1)
    f = np.stack([ii[:-1, :-1].ravel(), ii[:-1, 1:].ravel(), ii[1:, 1:].ravel(), ii[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(name); me.vertices.add(len(v)); me.vertices.foreach_set("co", v.astype(np.float32).ravel())
    me.loops.add(f.size); me.loops.foreach_set("vertex_index", f.astype(np.int32).ravel())
    me.polygons.add(len(f)); me.polygons.foreach_set("loop_start", (np.arange(len(f))*4).astype(np.int32))
    me.update(calc_edges=True); me.shade_smooth() if hasattr(me, "shade_smooth") else None
    if colors is not None:
        a = me.color_attributes.new("col", "FLOAT_COLOR", "POINT")
        c = np.concatenate([colors.reshape(-1, 3), np.ones((nx*ny, 1))], 1).astype(np.float32)
        a.data.foreach_set("color", c.ravel())
    o = bpy.data.objects.new(name, me); col().objects.link(o)
    if m: o.data.materials.append(m)
    return o

_ICO = {}
def ico(sub):
    if sub not in _ICO:
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        _ICO[sub] = (np.array([v.co[:] for v in bm.verts]), [[v.index for v in f.verts] for f in bm.faces]); bm.free()
    return _ICO[sub]
def blobs(specs, sub=2, jit=0.22):
    """specs = [(x,y,z,rx,ry,rz,seed)] -> (V,F) listes, ellipsoïdes bosselés."""
    tv, tf = ico(sub); V, F = [], []
    for (x, y, z, rx, ry, rz, seed) in specs:
        rr = np.random.default_rng(seed); v = tv*(1 + rr.uniform(-jit, jit, (len(tv), 1)))*[rx, ry, rz]
        b0 = len(V); V.extend((v + [x, y, z]).tolist()); F.extend([[b0 + i for i in f] for f in tf])
    return V, F
def tube(p0, p1, r0, r1, n=8, segs=1):
    """Tronc/branche conique entre p0 et p1 -> (V,F)."""
    p0, p1 = np.array(p0, float), np.array(p1, float); d = p1 - p0; L = np.linalg.norm(d); d /= L
    a = np.array([1, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1, 0]); u = np.cross(d, a); u /= np.linalg.norm(u); w = np.cross(d, u)
    V, F = [], []
    for s in range(segs + 1):
        k = s/segs; c = p0 + d*L*k; r = r0 + (r1 - r0)*k
        for i in range(n): t = 2*math.pi*i/n; V.append((c + r*(math.cos(t)*u + math.sin(t)*w)).tolist())
    for s in range(segs):
        for i in range(n): F.append([s*n + i, s*n + (i + 1) % n, (s + 1)*n + (i + 1) % n, (s + 1)*n + i])
    V.append(p1.tolist()); top = len(V) - 1
    for i in range(n): F.append([segs*n + i, segs*n + (i + 1) % n, top])
    return V, F
def merge(parts):
    V, F = [], []
    for v, f in parts: b0 = len(V); V.extend(v); F.extend([[b0 + i for i in ff] for ff in f])
    return V, F
def multi_obj(name, groups, link=True, smooth=True):
    """groups = [(V,F,mat)] -> un objet, un matériau par groupe."""
    V, F, MI, mats = [], [], [], []
    for k, (v, f, m) in enumerate(groups):
        b0 = len(V); V.extend(v); F.extend([[b0 + i for i in ff] for ff in f]); MI += [k]*len(f); mats.append(m)
    o = obj_from(name, V, F, None, smooth, link)
    for m in mats: o.data.materials.append(m)
    o.data.polygons.foreach_set("material_index", np.array(MI, np.int32)); o.data.update(); return o

# ------------------------------------------------------------------ végétation (variantes, tailles en mètres)
BARK = None
def leaf_mats():
    tones = [(0.02, 0.07, 0.015), (0.03, 0.09, 0.02), (0.045, 0.11, 0.022), (0.02, 0.06, 0.02), (0.06, 0.12, 0.025), (0.04, 0.085, 0.03)]
    return [leaf_mat(f"leaf{i}", t) for i, t in enumerate(tones)]
def leaf_mat(name, base, trans=0.35):
    """Feuille : diffus + translucide (lumière qui traverse), double face."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = 0.6; b.inputs["Specular IOR Level"].default_value = 0.35
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.inputs["Color"].default_value = (base[0]*1.6, base[1]*2.2, base[2]*1.2, 1)
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = trans
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m
def tree_variant(name, kind, m_leaf, m_bark, seed):
    rr = np.random.default_rng(seed); groups = []
    if kind == "broad":       # grand arbre de forêt : tronc + houppier fait de grappes
        h = rr.uniform(14, 22); cr = rr.uniform(5, 8)
        groups.append((*tube((0, 0, -0.5), (0, 0, h*0.75), 0.45, 0.25, 9, 3), m_bark))
        br = []
        for k in range(5):
            a = rr.uniform(0, 6.3); e = rr.uniform(0.35, 0.8)
            br.append(tube((0, 0, h*rr.uniform(0.45, 0.6)), (math.cos(a)*cr*0.6, math.sin(a)*cr*0.6, h*rr.uniform(0.75, 0.88)), 0.18, 0.07, 6))
        groups.append((*merge(br), m_bark))
        sp = []
        for k in range(int(rr.integers(10, 16))):
            a = rr.uniform(0, 6.3); d = cr*math.sqrt(rr.uniform(0, 1))*0.75
            r = rr.uniform(0.35, 0.55)*cr; sp.append((math.cos(a)*d, math.sin(a)*d, h*0.82 + rr.uniform(-0.12, 0.12)*h + (cr - d)*0.25, r, r, r*0.62, int(rr.integers(1e9))))
        groups.append((*blobs(sp, 2, 0.25), m_leaf))
    elif kind == "small":     # arbre de sous-étage / boisement
        h = rr.uniform(6, 10); cr = rr.uniform(2.5, 4)
        groups.append((*tube((0, 0, -0.3), (0, 0, h*0.7), 0.2, 0.12, 7, 2), m_bark))
        sp = [(rr.normal(0, cr*0.3), rr.normal(0, cr*0.3), h*0.75 + rr.normal(0, 0.8), cr*rr.uniform(0.45, 0.65), cr*rr.uniform(0.45, 0.65), cr*0.45, int(rr.integers(1e9))) for k in range(6)]
        groups.append((*blobs(sp, 2, 0.25), m_leaf))
    elif kind == "palm":      # palmier à huile
        h = rr.uniform(8, 14)
        bend = rr.normal(0, 0.6, 2); top = (bend[0], bend[1], h)
        groups.append((*tube((0, 0, -0.3), top, 0.3, 0.25, 8, 4), m_bark))
        fr = []
        for k in range(14):
            a = 2*math.pi*k/14 + rr.uniform(-0.15, 0.15); L = rr.uniform(3.5, 5); droop = rr.uniform(0.2, 0.9)
            pts = []
            for i in range(7):
                s = i/6; pts.append((top[0] + math.cos(a)*L*s, top[1] + math.sin(a)*L*s, h + 0.8*math.sin(s*2.2) - droop*L*s*s))
            for i in range(6):
                (x0, y0, z0), (x1, y1, z1) = pts[i], pts[i + 1]; wdt = 0.5*math.sin(math.pi*(i + 0.5)/6) + 0.08
                nx, ny = -math.sin(a)*wdt, math.cos(a)*wdt
                fr.append(([(x0 + nx, y0 + ny, z0), (x1 + nx, y1 + ny, z1), (x1 - nx, y1 - ny, z1), (x0 - nx, y0 - ny, z0), ((x0+x1)/2, (y0+y1)/2, (z0+z1)/2 + 0.12)],
                           [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]))
        groups.append((*merge(fr), m_leaf))
    elif kind == "leafy":     # buisson fait de vraies feuilles (cartes)
        lv = []
        for k in range(int(rr.integers(260, 380))):
            c = np.array([rr.normal(0, 0.55), rr.normal(0, 0.55), rr.uniform(0.15, 1.5)]); L = rr.uniform(0.14, 0.26); W = L*0.42
            a = rr.uniform(0, 6.3); t = rr.uniform(-0.6, 0.5); d = np.array([math.cos(a)*math.cos(t), math.sin(a)*math.cos(t), math.sin(t)])
            side = np.array([-math.sin(a), math.cos(a), 0])*W/2; tip = c + d*L
            lv.append(([c.tolist(), (c + d*L*0.45 + side).tolist(), tip.tolist(), (c + d*L*0.45 - side + [0, 0, 0.02]).tolist()], [[0, 1, 2, 3]]))
        stems = [tube((0, 0, 0), (rr.normal(0, 0.4), rr.normal(0, 0.4), rr.uniform(0.9, 1.4)), 0.02, 0.008, 5) for k in range(6)]
        groups.append((*merge(stems), m_bark)); groups.append((*merge(lv), m_leaf))
    elif kind == "bigleaf":   # plante à grandes feuilles du sous-bois (marantacées)
        lv = []; st = []
        for k in range(int(rr.integers(6, 11))):
            a = rr.uniform(0, 6.3); r = rr.uniform(0.1, 0.5); h = rr.uniform(0.6, 1.6); base = (0, 0, 0); top = (math.cos(a)*r, math.sin(a)*r, h)
            st.append(tube(base, top, 0.012, 0.008, 5))
            L = rr.uniform(0.45, 0.7); W = L*0.45; tilt = rr.uniform(-0.5, 0.2); d = np.array([math.cos(a)*math.cos(tilt), math.sin(a)*math.cos(tilt), math.sin(tilt)])
            side = np.array([-math.sin(a), math.cos(a), 0]); c = np.array(top); pts = []
            for i in range(6):
                s = i/5; w = W/2*math.sin(math.pi*s)**0.8; cc = c + d*L*s - np.array([0, 0, 0.08*s*s])
                pts += [(cc + side*w).tolist(), (cc - side*w).tolist()]
            fq = [[2*i, 2*i + 2, 2*i + 3, 2*i + 1] for i in range(5)]
            lv.append((pts, fq))
        groups.append((*merge(st), m_bark)); groups.append((*merge(lv), m_leaf))
    elif kind == "litter":    # feuilles mortes au sol
        lv = []
        for k in range(60):
            c = np.array([rr.uniform(-1, 1), rr.uniform(-1, 1), 0.01]); L = rr.uniform(0.08, 0.18); a = rr.uniform(0, 6.3)
            d = np.array([math.cos(a), math.sin(a), 0]); side = np.array([-math.sin(a), math.cos(a), 0])*L*0.25
            lv.append(([c.tolist(), (c + d*L*0.5 + side + [0, 0, 0.015]).tolist(), (c + d*L).tolist(), (c + d*L*0.5 - side + [0, 0, 0.015]).tolist()], [[0, 1, 2, 3]]))
        groups.append((*merge(lv), m_leaf))
    elif kind == "bush":
        sp = [(rr.normal(0, 0.6), rr.normal(0, 0.6), rr.uniform(0.4, 1.2), rr.uniform(0.6, 1.1), rr.uniform(0.6, 1.1), rr.uniform(0.5, 0.8), int(rr.integers(1e9))) for k in range(5)]
        groups.append((*blobs(sp, 2, 0.3), m_leaf))
    elif kind == "fern":      # fougère / plante basse en éventail
        fr = []
        for k in range(9):
            a = 2*math.pi*k/9 + rr.uniform(-0.2, 0.2); L = rr.uniform(0.7, 1.3); up = rr.uniform(0.6, 1.1)
            pts = [(math.cos(a)*L*s, math.sin(a)*L*s, up*math.sin(s*2.0)*0.8 - 0.25*s*s) for s in np.linspace(0, 1, 6)]
            for i in range(5):
                (x0, y0, z0), (x1, y1, z1) = pts[i], pts[i + 1]; wdt = 0.16*math.sin(math.pi*(i + 0.5)/5) + 0.02
                nx, ny = -math.sin(a)*wdt, math.cos(a)*wdt
                fr.append(([(x0 + nx, y0 + ny, z0), (x1 + nx, y1 + ny, z1), (x1 - nx, y1 - ny, z1), (x0 - nx, y0 - ny, z0)], [[0, 1, 2, 3]]))
        groups.append((*merge(fr), m_leaf))
    elif kind == "grass":     # touffe d'herbe sèche (savane des crêtes)
        bl = []
        for k in range(22):
            a = rr.uniform(0, 6.3); L = rr.uniform(0.5, 1.2); lean = rr.uniform(0.1, 0.5); x0, y0 = rr.normal(0, 0.08, 2)
            tip = (x0 + math.cos(a)*lean*L, y0 + math.sin(a)*lean*L, L); w = 0.025
            bl.append(([(x0 - w*math.sin(a), y0 + w*math.cos(a), 0), (x0 + w*math.sin(a), y0 - w*math.cos(a), 0), tip], [[0, 1, 2]]))
        groups.append((*merge(bl), m_leaf))
    return multi_obj(name, [g for g in groups], link=False)

def variant_collection(name, objs):
    c = bpy.data.collections.new(name)
    for i, o in enumerate(objs): o.name = f"{i:03d}_{o.name}"; c.objects.link(o)   # Collection Info trie par nom : on fige l'ordre
    return c

def scatter(name, P, S, RZ, VI, coll):
    """Instancie la collection `coll` sur les points P (N,3) via Geometry Nodes (scale S, rotation RZ, variante VI)."""
    me = bpy.data.meshes.new(name); me.vertices.add(len(P)); me.vertices.foreach_set("co", np.asarray(P, np.float32).ravel())
    for an, typ, arr in (("sc", "FLOAT", S), ("rz", "FLOAT", RZ), ("vi", "INT", VI)):
        a = me.attributes.new(an, typ, "POINT"); a.data.foreach_set("value", np.asarray(arr, np.int32 if typ == "INT" else np.float32))
    o = bpy.data.objects.new(name, me); col().objects.link(o)
    ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = coll; ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    iop = N.new("GeometryNodeInstanceOnPoints"); iop.inputs["Pick Instance"].default_value = True
    def named(n, t):
        x = N.new("GeometryNodeInputNamedAttribute"); x.data_type = t; x.inputs["Name"].default_value = n; return x.outputs["Attribute"]
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(named("rz", "FLOAT"), cmb.inputs["Z"])
    L.new(gi.outputs[0], iop.inputs["Points"]); L.new(ci.outputs[0], iop.inputs["Instance"])
    L.new(named("vi", "INT"), iop.inputs["Instance Index"]); L.new(cmb.outputs[0], iop.inputs["Rotation"]); L.new(named("sc", "FLOAT"), iop.inputs["Scale"])
    L.new(iop.outputs[0], go.inputs[0])
    md = o.modifiers.new("gn", "NODES"); md.node_group = ng
    return o

# ------------------------------------------------------------------ chimpanzé maquette (metaballs -> mesh), x = avant
def chimp(name, m, phase=0.0, scale=1.0, pose="walk", link=True):
    mb = bpy.data.metaballs.new(name + "_mb"); mb.resolution = 0.03; mb.render_resolution = 0.025; mb.threshold = 0.6
    mo = bpy.data.objects.new(name + "_mbo", mb); col().objects.link(mo)
    def ball(p, r, t="BALL"):
        e = mb.elements.new(); e.type = t; e.co = p; e.radius = r; return e
    def caps(p0, p1, r):
        p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; e = mb.elements.new(); e.type = "CAPSULE"
        e.co = (p0 + p1)/2; e.radius = r; e.size_x = d.length/2; e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized()); return e
    s = math.sin(phase*2*math.pi); c = math.cos(phase*2*math.pi)
    if pose == "walk":       # marche sur les phalanges : épaules bien plus hautes que les hanches, dos voûté, bras longs
        sh, hp = Vector((0.2, 0, 0.74)), Vector((-0.26, 0, 0.44))
        e = mb.elements.new(); e.type = "ELLIPSOID"; e.co = (sh + hp)/2 + Vector((0, 0, 0.04)); e.radius = 0.3; e.size_x = 1.3; e.size_y = 0.95; e.size_z = 0.9
        e.rotation = Euler((0, math.radians(-30), 0)).to_quaternion()
        ball(sh + Vector((0.0, 0, 0.03)), 0.26)                                    # épaules massives
        ball(hp + Vector((0.02, 0, 0.02)), 0.2)                                    # bassin
        ball(Vector((0.38, 0, 0.72)), 0.15); ball(Vector((0.49, 0, 0.66)), 0.085)  # tête basse en avant + museau
        ball(Vector((0.43, 0, 0.8)), 0.08)                                         # arcade
        ball(Vector((0.33, 0.12, 0.77)), 0.05); ball(Vector((0.33, -0.12, 0.77)), 0.05)  # oreilles
        for side, ph in ((1, 0), (-1, 0.5)):
            sw = math.sin((phase + ph)*2*math.pi); lift = max(0, math.cos((phase + ph)*2*math.pi))*0.06
            S0 = sh + Vector((0.02, side*0.2, -0.02)); hand = Vector((0.3 + 0.16*sw, side*0.22, 0.05 + lift)); elb = (S0 + hand)/2 + Vector((-0.03, side*0.03, 0))
            caps(S0, elb, 0.095); caps(elb, hand, 0.08); ball(hand + Vector((0.02, 0, 0)), 0.07)
            sw2 = math.sin((phase + ph + 0.5)*2*math.pi); lift2 = max(0, math.cos((phase + ph + 0.5)*2*math.pi))*0.05
            H0 = hp + Vector((0, side*0.14, -0.02)); foot = Vector((-0.24 + 0.14*sw2, side*0.17, 0.04 + lift2)); knee = Vector((-0.1 + 0.08*sw2, side*0.2, 0.24))
            caps(H0, knee, 0.095); caps(knee, foot, 0.07); caps(foot, foot + Vector((0.12, 0, 0)), 0.05)
    elif pose == "sit":
        e = mb.elements.new(); e.type = "ELLIPSOID"; e.co = (0, 0, 0.45); e.radius = 0.3; e.size_x = 0.85; e.size_y = 0.9; e.size_z = 1.35
        ball((0.03, 0, 0.82), 0.15); ball((0.13, 0, 0.8), 0.09)
        for side in (1, -1):
            caps((0.02, side*0.18, 0.68), (0.18, side*0.2, 0.3), 0.07); caps((0.18, side*0.2, 0.3), (0.25, side*0.15, 0.08), 0.06)
            caps((-0.05, side*0.14, 0.2), (0.25, side*0.2, 0.25), 0.09); caps((0.25, side*0.2, 0.25), (0.25, side*0.18, 0.03), 0.07)
    bpy.context.view_layer.objects.active = mo; mo.select_set(True)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg))
    bpy.data.objects.remove(mo, do_unlink=True)
    for p in me.polygons: p.use_smooth = True
    me.transform(__import__("mathutils").Matrix.Scale(scale, 4))
    o = bpy.data.objects.new(name, me)
    if link: col().objects.link(o)
    o.data.materials.append(m); return o

# ------------------------------------------------------------------ ciel / soleil / caméra / rendu
def sky(elev, rot, dust=1.0, air=1.0, strength=0.3):
    sc = bpy.context.scene; w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; wn = w.node_tree
    s = wn.nodes.new("ShaderNodeTexSky"); s.sky_type = "NISHITA"; s.sun_elevation = math.radians(elev); s.sun_rotation = math.radians(rot)
    s.dust_density = dust; s.air_density = air; s.sun_disc = True
    wn.links.new(s.outputs["Color"], wn.nodes["Background"].inputs["Color"]); wn.nodes["Background"].inputs["Strength"].default_value = strength
    return w
def sun_dir(elev, az):
    """az en degrés, 0 = est (+X), 90 = nord (+Y). Renvoie le vecteur vers le soleil."""
    e, a = math.radians(elev), math.radians(az); return Vector((math.cos(e)*math.cos(a), math.cos(e)*math.sin(a), math.sin(e)))
def sun(elev, az, energy, color, angle=2.0):
    l = bpy.data.lights.new("sun", "SUN"); l.energy = energy; l.color = color; l.angle = math.radians(angle)
    o = bpy.data.objects.new("sun", l); col().objects.link(o)
    o.rotation_euler = sun_dir(elev, az).to_track_quat("Z", "Y").to_euler(); return o
def camera(loc, target, lens=28, dof=None, fstop=2.8):
    cd = bpy.data.cameras.new("cam"); cd.lens = lens; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24; cd.clip_end = 20000; cd.clip_start = 0.1
    c = bpy.data.objects.new("cam", cd); col().objects.link(c); bpy.context.scene.camera = c
    c.location = loc; c.rotation_euler = (Vector(loc) - Vector(target)).to_track_quat("Z", "Y").to_euler()
    if dof: cd.dof.use_dof = True; cd.dof.focus_distance = dof; cd.dof.aperture_fstop = fstop
    return c
def render_setup(samples, scale, expo, mist=None, mist_col=(0.5, 0.6, 0.7), mist_fac=1.0):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples
    sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 5; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 3; sc.cycles.transparent_max_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, scale
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = expo
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 93
    if mist:
        start, depth = mist; sc.view_layers[0].use_pass_mist = True; w = sc.world; w.mist_settings.start = start; w.mist_settings.depth = depth; w.mist_settings.falloff = "QUADRATIC"
        sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes["Render Layers"]; comp = ct.nodes["Composite"]
        mf = ct.nodes.new("CompositorNodeMath"); mf.operation = "MULTIPLY"; mf.inputs[1].default_value = mist_fac; mf.use_clamp = True
        mx = ct.nodes.new("CompositorNodeMixRGB"); mx.inputs[2].default_value = (*mist_col, 1)
        sc.view_layers[0].use_pass_z = True
        gt = ct.nodes.new("CompositorNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 1e6
        sk = ct.nodes.new("CompositorNodeMath"); sk.operation = "MULTIPLY_ADD"; sk.inputs[1].default_value = -0.75; sk.inputs[2].default_value = 1.0   # ciel : 25 % de brume seulement
        ct.links.new(rl.outputs["Depth"], gt.inputs[0]); ct.links.new(gt.outputs[0], sk.inputs[0])
        m2 = ct.nodes.new("CompositorNodeMath"); m2.operation = "MULTIPLY"
        ct.links.new(rl.outputs["Mist"], mf.inputs[0]); ct.links.new(mf.outputs[0], m2.inputs[0]); ct.links.new(sk.outputs[0], m2.inputs[1]); ct.links.new(m2.outputs[0], mx.inputs[0]); ct.links.new(rl.outputs["Image"], mx.inputs[1]); ct.links.new(mx.outputs[0], comp.inputs["Image"])
