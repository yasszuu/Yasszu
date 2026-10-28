"""Plans 3D Gombe. SHOT=vallee|raid|kalande  ->  bl/bin/python shots.py <out.jpg> [samples] [scale%]"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from lib import *
from scipy.ndimage import gaussian_filter, distance_transform_edt
out = sys.argv[1]; SAMPLES = int(sys.argv[2]) if len(sys.argv) > 2 else 32; SCALE = int(sys.argv[3]) if len(sys.argv) > 3 else 50
SHOT = os.environ.get("SHOT", "vallee"); HERE = os.path.dirname(os.path.abspath(__file__))
sc = reset()
def sky_az(elev, az, **k): return sky(elev, 90 - az, **k)            # az : 0 = est, 90 = nord
RED = mat("chimp", (0.85, 0.0, 0.0), 0.55, emit=(1, 0, 0), emit_s=0.25)
FPS, DUR = 30, float(os.environ.get("DUR", 4.6))
WALK = {}                                                    # phases de marche pré-calculées (8 maillages)
def walk_meshes(scale):
    if scale not in WALK:
        ms = []
        for k in range(8):
            o = chimp(f"w{scale}_{k}", RED, k/8, scale, link=False); ms.append(o.data)
        WALK[scale] = ms
    return WALK[scale]
WALKERS = []                                                 # (objet, échelle, phase0, cadence, fonction position(t) -> (x, y, z, cap))
def walker(o, scale, ph, cad, fn): WALKERS.append((o, scale, ph, cad, fn))
CAMF = None
LEAVES = leaf_mats(); BARK = mat("bark", (0.12, 0.09, 0.07), 0.9); BARK2 = mat("bark2", (0.14, 0.12, 0.1), 0.85)

if SHOT in ("vallee", "kalande"):
    # ------------------------------------------------ vrai relief de Gombe (Terrarium, 15 m), lac Tanganyika à l'ouest
    H = np.load(os.path.join(HERE, "h.npy")).astype(np.float64) - 767.0
    ny, nx = H.shape; STEP = 15.0
    xs = (np.arange(nx) - nx/2)*STEP; ys = (np.arange(ny) - ny/2)*STEP; X, Y = np.meshgrid(xs, ys)
    from scipy.ndimage import label, binary_opening
    land = gaussian_filter(H, 1.5) > 3.0; lb, nl = label(land); sizes = np.bincount(lb.ravel()); sizes[0] = 0
    lake = lb != sizes.argmax(); d_sh = distance_transform_edt(lake)*STEP; d_land = distance_transform_edt(~lake)*STEP
    dsm = gaussian_filter(np.where(lake, -d_sh, d_land), 2.0)                     # distance signée lissée au rivage
    lake = dsm < 0; d_sh = np.maximum(-dsm, 0); d_land = np.maximum(dsm, 0)
    H = np.where(dsm < 30, np.minimum(H, 0.5 + dsm*0.2), H); H = np.where(lake, 0.5 + dsm*0.2, H); H = np.maximum(H, -60)
    H = np.where(H > 0, H*1.25, H)                                               # légère exagération du relief
    Hn = H + gaussian_filter(rng.normal(0, 1, H.shape), 1.2)*4*(~lake)          # micro-relief
    gy, gx = np.gradient(Hn, STEP); slope = np.hypot(gx, gy)
    valley = gaussian_filter(Hn, 3) - gaussian_filter(Hn, 14)                     # <0 = fond de vallée
    alt = np.clip(Hn/700, 0, 1)
    forest = 1/(1 + np.exp((valley + 6 - 30*(alt < 0.35))/9))                     # forêt dans les vallées et en bas de pente
    forest = np.clip(forest*(1.15 - 0.9*alt**2), 0, 1)*(~lake)*np.clip((d_land - 8)/20, 0, 1)
    forest = np.clip(forest + 0.35*gaussian_filter(rng.normal(0, 1, H.shape), 3)*forest, 0, 1)
    # couleurs du sol : sable de plage, herbe dorée des crêtes, sous-bois sombre, roche sur les pentes raides
    grass = np.array([0.2, 0.18, 0.07]) if SHOT != "kalande" else np.array([0.1, 0.11, 0.035]); grass2 = np.array([0.22, 0.24, 0.08]); dark = np.array([0.035, 0.07, 0.02])
    sand = np.array([0.55, 0.47, 0.33]); rock = np.array([0.30, 0.25, 0.20]); wet = np.array([0.12, 0.14, 0.1])
    g = (0.6*gaussian_filter(rng.uniform(0, 1, H.shape), 1) + 0.4*gaussian_filter(rng.uniform(0, 1, H.shape), 5)*2 - 0.4)[..., None]
    C = grass*(0.6 + 0.8*g) + (grass2 - grass)*np.clip(1 - alt*2, 0, 1)[..., None]
    C = C + (dark - C)*np.clip(forest*1.3, 0, 1)[..., None]
    C = C + (rock - C)*np.clip((slope - 0.9)*1.5, 0, 0.7)[..., None]
    C = C + (sand - C)*np.clip(1 - (d_land - 4)/12, 0, 1)[..., None]*(~lake)[..., None]
    C = np.where(lake[..., None], np.array([0.25, 0.22, 0.15])*np.clip(1 - d_sh/200, 0.15, 1)[..., None], C)
    terr = grid_mesh("terrain", X, Y, Hn, C, vcol_mat("terrain", 0.9, 0.25, 0.4))
    # lac
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.0)); lk = bpy.context.object; lk.scale = (60000, 60000, 1)
    WM = mat("lake", (0.015, 0.07, 0.085), 0.04, transm=0.0, spec=0.6); nt = WM.node_tree; b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexNoise"); tx.inputs["Scale"].default_value = 0.08; tx.inputs["Detail"].default_value = 6
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 3, 1); tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; bp.inputs["Distance"].default_value = 0.2
    nt.links.new(tx.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"]); lk.data.materials.append(WM)
    # rive opposée (Congo) : longue chaîne bleutée à l'horizon, 50 km à l'ouest
    xx = np.linspace(-150000, 150000, 600); far = []
    hh = 450 + 250*np.sin(xx/9000) + 150*np.sin(xx/3100 + 1) + 60*np.sin(xx/900)
    V = [(-50000 - 3000*math.sin(x/20000), x, 0) for x in xx] + [(-55000 - 3000*math.sin(x/20000), x, h) for x, h in zip(xx, hh)]
    F = [[i, i + 1, 601 + i, 600 + i] for i in range(599)]
    obj_from("congo", V, F, mat("congo", (0.12, 0.13, 0.13), 0.9))
    def shore_x(y):
        r = int((y - ys[0])/STEP); row = lake[r]; return xs[np.argmax(~row)]
    # végétation : points tirés selon la densité de forêt
    VAR = []; kinds = ["broad"]*5 + ["small"]*4 + ["palm"]*2 + ["bush"]*2
    for i, k in enumerate(kinds): VAR.append(tree_variant(f"tv{i}", k, LEAVES[i % len(LEAVES)], BARK if k != "palm" else BARK2, 100 + i))
    coll = variant_collection("trees", VAR)
    SP = 11.0; cx = np.arange(xs[0], xs[-1], SP); cy = np.arange(ys[0], ys[-1], SP); PX, PY = np.meshgrid(cx, cy)
    PX = PX + rng.uniform(-SP/2, SP/2, PX.shape); PY = PY + rng.uniform(-SP/2, SP/2, PY.shape)
    ix = np.clip(((PX - xs[0])/STEP).astype(int), 0, nx - 1); iy = np.clip(((PY - ys[0])/STEP).astype(int), 0, ny - 1)
    fp = forest[iy, ix]; wood = (~lake[iy, ix])*(d_land[iy, ix] > 30)*0.2      # arbres épars sur les crêtes
    keep = rng.uniform(0, 1, fp.shape) < np.maximum(fp*0.95, wood)
    if SHOT == "vallee": keep &= (PY > -4500) & (PY < 6500)
    if SHOT == "kalande": keep &= ~((PX > 380) & (PX < 720) & (PY > -3700) & (PY < -3380))
    PX, PY, ix, iy, fp = PX[keep], PY[keep], ix[keep], iy[keep], fp[keep]
    PZ = Hn[iy, ix] - 0.5; n = len(PX); print("arbres", n)
    vi = np.where(fp > 0.4, rng.integers(0, 11, n), rng.integers(5, 9, n)); vi = np.where((fp > 0.3) & (Hn[iy, ix] < 120) & (rng.uniform(0, 1, n) < 0.12), rng.integers(9, 11, n), vi)
    S_ = rng.uniform(0.9, 1.4, n)*(1 + 0.6*fp)
    m = fp > 0.25; bx = PX[m] + rng.normal(0, 5, m.sum()); by = PY[m] + rng.normal(0, 5, m.sum()); nb = m.sum()   # buissons de sous-étage
    bix = np.clip(((bx - xs[0])/STEP).astype(int), 0, nx - 1); biy = np.clip(((by - ys[0])/STEP).astype(int), 0, ny - 1); okb = ~lake[biy, bix]
    P = np.concatenate([np.stack([PX, PY, PZ], 1), np.stack([bx, by, Hn[biy, bix] - 0.3], 1)[okb]])
    scatter("forest", P, np.concatenate([S_, rng.uniform(2.0, 3.2, nb)[okb]]), rng.uniform(0, 6.3, len(P)), np.concatenate([vi, rng.integers(11, 13, nb)[okb]]), coll)

if SHOT == "vallee":
    # village de pêcheurs de Kasekela : cases à toit de tôle + pirogues
    ROOF = mat("roof", (0.42, 0.36, 0.3), 0.45, spec=0.8); WALL = mat("wall", (0.55, 0.45, 0.35), 0.9); BOAT = mat("boat", (0.18, 0.11, 0.07), 0.7)
    parts_w, parts_r, parts_b = [], [], []
    for k in range(16):
        y = rng.uniform(-900, 700); x = shore_x(y) + rng.uniform(15, 55); z = Hn[int((y - ys[0])/STEP), int((x - xs[0])/STEP)]
        w, l, a = rng.uniform(4, 7), rng.uniform(6, 12), rng.uniform(-0.3, 0.3)
        ca, sa = math.cos(a), math.sin(a); R2 = lambda u, v, h: (x + u*ca - v*sa, y + u*sa + v*ca, z + h)
        q = [R2(-w/2, -l/2, 0), R2(w/2, -l/2, 0), R2(w/2, l/2, 0), R2(-w/2, l/2, 0)]
        qt = [(p[0], p[1], p[2] + 3) for p in q]
        parts_w.append((q + qt, [[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]))
        parts_r.append(([R2(-w/2 - .6, -l/2 - .4, 3), R2(w/2 + .6, -l/2 - .4, 3), R2(w/2 + .6, l/2 + .4, 3), R2(-w/2 - .6, l/2 + .4, 3), R2(0, -l/2 - .4, 4.6), R2(0, l/2 + .4, 4.6)],
                        [[0, 4, 5, 3], [1, 2, 5, 4]]))
    for k in range(22):
        y = rng.uniform(-2500, 1800); x = shore_x(y) - rng.uniform(5, 70) - (k > 14)*rng.uniform(100, 900); a = rng.uniform(0, 6.3)
        sp = [(0, 0, 0.1, 4.5, 0.6, 0.35, k)]; v, f = blobs(sp, 1, 0.05)
        v = [(x + p[0]*math.cos(a) - p[1]*math.sin(a), y + p[0]*math.sin(a) + p[1]*math.cos(a), p[2]) for p in v]; parts_b.append((v, f))
    obj_from("walls", *merge(parts_w), WALL, False); obj_from("roofs", *merge(parts_r), ROOF, False); obj_from("boats", *merge(parts_b), BOAT, False)
    ys0 = 0.0; sx = shore_x(ys0)
    sky_az(9, 240, dust=2.0, air=1.0, strength=0.5); sun(9, 240, 3.2, (1.0, 0.76, 0.52), 1.0)
    cam_ = camera((sx - 800, -1500, 190), (sx + 2600, 500, 420), 20)
    def CAMF(t):
        k = d3e(t/DUR); c = Vector((sx - 800 + 260*k, -1500 + 160*k, 190 + 45*k)); tg = Vector((sx + 2600, 500 + 150*k, 420 - 30*k))
        cam_.location = c; cam_.rotation_euler = (c - tg).to_track_quat("Z", "Y").to_euler()
    render_setup(SAMPLES, SCALE, float(os.environ.get("EXPO", -1.7)), mist=(600, 40000), mist_col=(0.85, 0.66, 0.48), mist_fac=0.6)

elif SHOT == "kalande":
    # éperon herbeux au coucher du soleil, face au lac : Kalande arrive par la gauche (sud), Kasakela recule vers la droite (nord)
    def ground(x, y):
        from scipy.ndimage import map_coordinates
        return float(map_coordinates(Hn, [[(y - ys[0])/STEP], [(x - xs[0])/STEP]], order=1)[0])
    def crest(y): xx = np.arange(470, 600, 2.0); return float(xx[np.argmax([ground(x, y) for x in xx])])
    K = (crest(-3570), -3570.0); C = (crest(-3628) + 4, -3628.0)                 # caméra sur la crête, regarde vers le nord le long de l'arête
    GV = [tree_variant(f"g{i}", "grass", leaf_mat(f"gr{i}", t, 0.4), BARK, 300 + i) for i, t in enumerate([(0.45, 0.33, 0.1), (0.5, 0.4, 0.14), (0.33, 0.3, 0.1), (0.55, 0.36, 0.12)])]
    gc = variant_collection("grass", GV); N = 160000
    rr_ = 1.5 + 160*rng.uniform(0, 1, N)**2; aa_ = rng.uniform(0, 6.3, N)
    gx_ = np.concatenate([C[0] + rr_*np.cos(aa_), C[0] + rng.uniform(-40, 40, 40000)]); gy_ = np.concatenate([C[1] + 10 + rr_*np.sin(aa_), C[1] + rng.uniform(-5, 75, 40000)]); N = len(gx_)
    from scipy.ndimage import map_coordinates
    gz = map_coordinates(Hn, [(gy_ - ys[0])/STEP, (gx_ - xs[0])/STEP], order=1)
    dc = np.hypot(gx_ - C[0], gy_ - C[1]); ok = dc > 2.0
    crx = np.interp(gy_, np.arange(-3700, -3400, 5.0), [crest(y) for y in np.arange(-3700, -3400, 5.0)]); short = np.clip(np.abs(gx_ - crx)/9, 0.3, 1)
    scatter("grassf", np.stack([gx_, gy_, gz - 0.1], 1)[ok], (rng.uniform(0.3, 0.6, N)*(0.6 + 0.8*np.clip(dc/60, 0, 1))*short)[ok], rng.uniform(0, 6.3, N)[ok], rng.integers(0, 4, N)[ok], gc)
    CH = []
    for i in range(13):        # Kalande : la troupe nombreuse arrive du sud (gauche)
        y = -3618 + i*2.1 + rng.normal(0, 0.8); x = crest(y) + rng.normal(0, 2.0)
        o = chimp(f"kal{i}", RED, rng.uniform(0, 1), 1.2); o.location = (x, y, ground(x, y) - 0.05); o.rotation_euler = (0, 0, math.pi/2 + rng.normal(0, 0.3)); CH.append(o)
        walker(o, 1.2, rng.uniform(0, 1), 1.2, lambda t, x=x, y=y, r=o.rotation_euler.z: (x, y + 1.3*t, ground(x, y + 1.3*t) - 0.05, r))
    for i in range(4):         # Kasakela : ils reculent vers le nord (droite)
        y = -3575 + i*3.0; x = crest(y) + rng.normal(0, 1.5)
        o = chimp(f"kas{i}", RED, rng.uniform(0, 1), 1.15); o.location = (x, y, ground(x, y) - 0.05); o.rotation_euler = (0, 0, math.pi/2 + 0.2 + rng.normal(0, 0.2)); CH.append(o)
        walker(o, 1.15, rng.uniform(0, 1), 1.6, lambda t, x=x, y=y, r=o.rotation_euler.z: (x, y + 2.0*t, ground(x, y + 2.0*t) - 0.05, r))
    from bpy_extras.object_utils import world_to_camera_view

    sky_az(5, 175, dust=1.2, air=1.1, strength=0.6); sun(5, 175, 2.6, (1.0, 0.5, 0.25), 0.8)
    cam_ = camera((C[0] + 3, C[1] - 6, ground(*C) + 9.5), (crest(-3592), -3592, ground(crest(-3592), -3592) - 1.0), 35, dof=40, fstop=6)
    c0 = Vector(cam_.location); tg0 = Vector((crest(-3592), -3592, ground(crest(-3592), -3592) - 1.0))
    def CAMF(t):
        k = t/DUR; c = c0 + Vector((-1.5*k, 5.0*k, -1.2*k)); tg = tg0 + Vector((0, 4.0*k, 0))
        cam_.location = c; cam_.rotation_euler = (c - tg).to_track_quat("Z", "Y").to_euler()
    bpy.context.view_layer.update()
    for o in CH[::4]: print("dim", o.dimensions[:], o.hide_render, len(o.data.vertices)); print("proj", o.name, tuple(round(v, 2) for v in o.location), tuple(round(v, 2) for v in world_to_camera_view(sc, cam_, o.location)))
    render_setup(SAMPLES, SCALE, float(os.environ.get("EXPO", -1.4)), mist=(150, 40000), mist_col=(0.95, 0.55, 0.33), mist_fac=0.7)

elif SHOT == "raid":
    # ------------------------------------------------ sous-bois : sentier, contreforts, lianes, fougères, rais de lumière
    nx_, ny_ = 260, 300; xs_ = np.linspace(-30, 30, nx_); ys_ = np.linspace(-10, 60, ny_); X, Y = np.meshgrid(xs_, ys_)
    trail = np.exp(-((X - 1.8*np.sin(Y*0.09))/1.0)**2)
    Hg = 0.6*gaussian_filter(rng.normal(0, 1, X.shape), 6) + 0.12*gaussian_filter(rng.normal(0, 1, X.shape), 1.5) + 0.02*X + 0.05*Y - 0.08*trail
    litter = np.array([0.16, 0.10, 0.05]); dirt = np.array([0.26, 0.18, 0.11]); moss = np.array([0.06, 0.1, 0.03])
    gg = gaussian_filter(rng.uniform(0, 1, X.shape), 1.0)[..., None]
    C = litter*(0.6 + 0.9*gg) + (moss - litter)*np.clip(gaussian_filter(rng.normal(0, 1, X.shape), 4)*2, 0, 1)[..., None]
    C = C + (dirt - C)*np.clip(trail*1.4, 0, 1)[..., None]
    grid_mesh("ground", X, Y, Hg, C, vcol_mat("ground", 0.95, 0.6, 6))
    from scipy.ndimage import map_coordinates
    gz = lambda x, y: float(map_coordinates(Hg, [[(y + 10)/70*(ny_ - 1)], [(x + 30)/60*(nx_ - 1)]], order=1)[0])
    CAM = (-3.2, 4.0); RAIDERS = [(1.8*math.sin(y*0.09), y) for y in [6.0 + i*2.4 for i in range(6)]]
    def seg_d(px, py, a, b):
        ax, ay = a; bx, by = b; t = max(0, min(1, ((px - ax)*(bx - ax) + (py - ay)*(by - ay))/((bx - ax)**2 + (by - ay)**2)))
        return math.hypot(px - ax - t*(bx - ax), py - ay - t*(by - ay))
    def blocked(x, y, m=1.0): return any(seg_d(x, y, CAM, (cx_, cy_ + 1)) < m + 0.08*math.hypot(cx_ - CAM[0], cy_ - CAM[1]) for cx_, cy_ in RAIDERS) or math.hypot(x - CAM[0], y - CAM[1]) < 2.5
    # grands troncs à contreforts
    tr_parts = []; TREES = []
    for k in range(26):
        while True:
            x, y = rng.uniform(-22, 22), rng.uniform(2, 58)
            if abs(x - 1.8*math.sin(y*0.09)) > 2.4 and not blocked(x, y, r_ + 1.5 if (r_ := 0.9) else 0) and all((x - a)**2 + (y - b)**2 > 16 for a, b, _ in TREES): break
        r = rng.uniform(0.35, 0.9)*(1 + 0.4*(y > 30)); TREES.append((x, y, r)); z = gz(x, y)
        tr_parts.append(tube((x, y, z - 0.5), (x + rng.normal(0, 0.3), y + rng.normal(0, 0.3), z + 34), r, r*0.6, 12, 6))
        for b in range(int(rng.integers(3, 6))):                                   # contreforts (lames)
            a = rng.uniform(0, 6.3) ; L = r*rng.uniform(2.2, 3.8); hb = r*rng.uniform(2.5, 4.5); t = 0.12*r
            ca, sa = math.cos(a), math.sin(a); nx2, ny2 = -sa*t, ca*t
            P = [(x, y, z + hb), (x + ca*L, y + sa*L, z - 0.2), (x, y, z - 0.2)]
            V = [(p[0] + nx2, p[1] + ny2, p[2]) for p in P] + [(p[0] - nx2, p[1] - ny2, p[2]) for p in P]
            tr_parts.append((V, [[0, 1, 2], [3, 5, 4], [0, 3, 4, 1], [1, 4, 5, 2]]))
    trunks = obj_from("trunks", *merge(tr_parts), mat("trunk", (0.2, 0.17, 0.13), 0.85), True)
    TB = trunks.data.materials[0]; nt = TB.node_tree; b = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 10
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (6, 6, 0.6); tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    rmp = nt.nodes.new("ShaderNodeValToRGB"); rmp.color_ramp.elements[0].color = (0.018, 0.012, 0.007, 1); rmp.color_ramp.elements[1].color = (0.07, 0.05, 0.032, 1)
    nt.links.new(nz.outputs["Fac"], rmp.inputs["Fac"]); nt.links.new(rmp.outputs["Color"], b.inputs["Base Color"])
    # canopée (couche de grappes avec trouées) -> lumière tachetée
    cp = [(rng.uniform(-40, 40), rng.uniform(-15, 75), rng.uniform(24, 34), rng.uniform(4, 8), rng.uniform(4, 8), rng.uniform(2, 3.5), k) for k in range(420)]
    cp = [c for c in cp if rng.uniform() < 0.75]
    obj_from("canopy", *blobs(cp, 2, 0.3), LEAVES[0])
    # lianes
    lines = []
    for k in range(40):
        x0, y0, r = TREES[rng.integers(len(TREES))]; x1, y1 = x0 + rng.normal(0, 6), y0 + rng.normal(0, 6); sag = rng.uniform(3, 12); z0 = rng.uniform(14, 26)
        lines.append([(x0 + (x1 - x0)*s, y0 + (y1 - y0)*s, z0 - sag*math.sin(math.pi*s) - (1 - s)*0 + (s > 0.98)*0) for s in np.linspace(0, 1, 16)])
    for k in range(30):                                                             # lianes pendantes jusqu'au sol
        x0, y0 = rng.uniform(-16, 16), rng.uniform(4, 45); z0 = 22
        if blocked(x0, y0, 0.5): continue
        lines.append([(x0 + 0.4*math.sin(s*3 + k), y0 + 0.3*math.cos(s*2 + k), z0*(1 - s) + gz(x0, y0)*s - 0.2) for s in np.linspace(0, 1, 14)])
    cu = bpy.data.curves.new("lianas", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.035; cu.bevel_resolution = 2
    for pts in lines:
        s_ = cu.splines.new("POLY"); s_.points.add(len(pts) - 1)
        for i, p in enumerate(pts): s_.points[i].co = (*p, 1)
    lo = bpy.data.objects.new("lianas", cu); col().objects.link(lo); cu.materials.append(mat("liana", (0.13, 0.11, 0.06), 0.8))
    # sous-étage : fougères, buissons feuillus, grandes feuilles, jeunes arbres, palmiers + litière
    LIT = [leaf_mat(f"lit{i}", t, 0.1) for i, t in enumerate([(0.25, 0.14, 0.05), (0.32, 0.2, 0.08), (0.18, 0.1, 0.04)])]
    U = [tree_variant(f"f{i}", "fern", LEAVES[(i + 1) % 6], BARK, 400 + i) for i in range(3)] + [tree_variant(f"b{i}", "leafy", LEAVES[(i + 3) % 6], BARK, 500 + i) for i in range(3)] \
        + [tree_variant(f"m{i}", "bigleaf", LEAVES[(i + 2) % 6], BARK, 550 + i) for i in range(2)] \
        + [tree_variant(f"s{i}", "leafy", LEAVES[i % 6], BARK, 600 + i) for i in range(1)] + [tree_variant("p0", "palm", LEAVES[2], BARK2, 700)]
    uc = variant_collection("under", U); N = 3400; P = []
    while len(P) < N:
        x, y = rng.uniform(-28, 28), rng.uniform(-6, 58)
        if abs(x - 1.8*math.sin(y*0.09)) > 1.3 + rng.uniform(0, 1.0) and not blocked(x, y, 0.7): P.append((x, y, gz(x, y) - 0.05))
    P = np.array(P); vi = rng.choice(10, N, p=[.14, .14, .12, .14, .12, .1, .09, .09, .03, .03])
    scatter("under", P, rng.uniform(0.7, 1.3, N)*np.where(vi == 8, 2.4, np.where(vi == 9, 0.6, 1)), rng.uniform(0, 6.3, N), vi, uc)
    LC = variant_collection("litter", [tree_variant(f"l{i}", "litter", LIT[i], BARK, 800 + i) for i in range(3)])
    N = 6000; lx, ly = rng.uniform(-14, 14, N), rng.uniform(-4, 40, N)
    scatter("litter", np.stack([lx, ly, [gz(a, b) + 0.005 for a, b in zip(lx, ly)]], 1), rng.uniform(0.7, 1.3, N), rng.uniform(0, 6.3, N), rng.integers(0, 3, N), LC)
    # tronc couché moussu en travers à gauche
    obj_from("log", *tube((-6, 9, gz(-6, 9) + 0.3), (-1.2, 13.5, gz(-1.2, 13.5) + 0.35), 0.45, 0.38, 12, 4), mat("mosslog", (0.08, 0.13, 0.04), 0.9))
    # brume volumique légère -> vrais rais de lumière à travers les trouées de la canopée
    FOGD = float(os.environ.get("FOG", 0.0))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 25, 15)); vb = bpy.context.object; vb.scale = (60, 80, 32); vb.hide_render = FOGD <= 0
    VM = bpy.data.materials.new("fog"); VM.use_nodes = True; vn = VM.node_tree; vn.nodes.remove(vn.nodes["Principled BSDF"])
    pv = vn.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = FOGD; pv.inputs["Color"].default_value = (0.9, 0.95, 0.85, 1)
    pv.inputs["Anisotropy"].default_value = 0.6
    vn.links.new(pv.outputs[0], vn.nodes["Material Output"].inputs["Volume"]); vb.data.materials.append(VM)
    # les 6 mâles de Kasakela, en file indienne sur le sentier
    for i in range(6):
        y = 6.0 + i*2.4; x = 1.8*math.sin(y*0.09) + rng.normal(0, 0.25)
        o = chimp(f"raid{i}", RED, i*0.37 % 1, 1.12); o.location = (x, y, gz(x, y) - 0.04)
        d = 1.8*0.09*math.cos(y*0.09); o.rotation_euler = (0, 0, -math.pi/2 + math.atan(d))
        def fn(t, y0=y + 2.6, dx=x - 1.8*math.sin(y*0.09)):
            yy = y0 - 1.0*t; xx = 1.8*math.sin(yy*0.09) + dx; d = 1.8*0.09*math.cos(yy*0.09); return xx, yy, gz(xx, yy) - 0.04, -math.pi/2 + math.atan(d)
        walker(o, 1.12, i*0.37 % 1, 1.1, fn)
    sky_az(55, 150, dust=1.0, strength=0.7); sun(55, 150, 3.8, (1.0, 0.86, 0.6), 1.5)
    # plantes de premier plan (floues) qui encadrent
    fwd = Vector((1.6 - CAM[0], 14 - CAM[1], 0)).normalized(); rgt = Vector((fwd.y, -fwd.x, 0))
    for k, (dist, off, kind, sc_) in enumerate([(1.5, -1.0, "bigleaf", 0.75), (1.7, 1.05, "fern", 0.9), (2.6, -1.7, "leafy", 0.8)]):
        p = Vector((*CAM, 0)) + fwd*dist + rgt*off; o = tree_variant(f"fg{k}", kind, LEAVES[(k + 1) % 6], BARK, 900 + k); col().objects.link(o)
        o.location = (p.x, p.y, gz(p.x, p.y) - 0.05); o.scale = (sc_,)*3; o.rotation_euler = (0, 0, rng.uniform(0, 6.3))
    cam_ = camera((*CAM, gz(*CAM) + 0.8), (1.6, 14, gz(1.6, 14) + 1.0), 24, dof=9, fstop=2.0)
    def CAMF(t):
        k = t/DUR; c = Vector((CAM[0] + 0.5*k, CAM[1] - 0.3*k, gz(*CAM) + 0.8 - 0.15*k)); tg = Vector((1.6 - 0.4*k, 14 - 3.0*k, gz(1.6, 14) + 1.0))
        cam_.location = c; cam_.rotation_euler = (c - tg).to_track_quat("Z", "Y").to_euler(); cam_.data.dof.focus_distance = 9 - 2.2*k
    render_setup(SAMPLES, SCALE, float(os.environ.get("EXPO", -0.6)), mist=(5, 75), mist_col=(0.16, 0.2, 0.13), mist_fac=float(os.environ.get("MISTF", 0.55)))

def d3e(k): return k*k*(3 - 2*k)*0.5 + k*0.5
def place(t):
    for o, scl, ph, cad, fn in WALKERS:
        x, y, z, r = fn(t); o.location = (x, y, z); o.rotation_euler = (0, 0, r)
        o.data = walk_meshes(scl)[int(((ph + cad*t) % 1)*8) % 8]
    if CAMF: CAMF(t)
FR = os.environ.get("FRAMES")
if FR:
    a, b = map(int, FR.split(",")); os.makedirs(out, exist_ok=True)
    for f in range(a, b):
        p = os.path.join(out, f"{f:04d}.jpg")
        if os.path.exists(p): continue
        place(f/FPS); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
else:
    place(float(os.environ.get("T", 0))); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
