"""Plan 3D : la colonne d'éléphants (formes rouges) traverse les monts Gaoligong (Birmanie → Yunnan), brume du matin.
bl/bin/python lw.py <out(.jpg|dir)> [samples] [scale%]   (FRAMES=a,b pour une séquence, T=t pour une image)"""
import sys, os; sys.path.insert(0, '../gombe3d'); from lib import *
from scipy.ndimage import gaussian_filter, map_coordinates
out = sys.argv[1]; SAMPLES = int(sys.argv[2]) if len(sys.argv) > 2 else 20; SCALE = int(sys.argv[3]) if len(sys.argv) > 3 else 50
FPS, DUR = 30, 5.0
sc = reset()
RED = mat("elephant", (0.85, 0.0, 0.0), 0.55, emit=(1, 0, 0), emit_s=0.2)
def elephant(name, m, phase=0.0, link=True):
    """Éléphant d'Asie maquette (metaballs → maillage), x = avant, ~2,7 m au garrot."""
    mb = bpy.data.metaballs.new(name + "_mb"); mb.resolution = 0.07; mb.render_resolution = 0.05; mb.threshold = 0.6
    mo = bpy.data.objects.new(name + "_mbo", mb); col().objects.link(mo)
    def ball(p, r): e = mb.elements.new(); e.type = "BALL"; e.co = p; e.radius = r; return e
    def ell(p, r, s): e = mb.elements.new(); e.type = "ELLIPSOID"; e.co = p; e.radius = r; e.size_x, e.size_y, e.size_z = s; return e
    def caps(p0, p1, r):
        p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; e = mb.elements.new(); e.type = "CAPSULE"
        e.co = (p0 + p1)/2; e.radius = r; e.size_x = d.length/2; e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized()); return e
    ell((0, 0, 2.0), 1.35, (1.3, 1.05, 1.0)); ell((0, 0, 1.55), 1.0, (1.3, 1.1, 0.8))   # corps + ventre rond                                     # corps
    ball((0.7, 0, 2.35), 1.2); ball((-0.75, 0, 2.15), 1.15)                       # garrot / croupe
    ell((1.75, 0, 2.55), 0.8, (0.9, 1.0, 1.05)); ball((1.85, 0.18, 3.0), 0.48); ball((1.85, -0.18, 3.0), 0.48)    # tête (double bosse frontale)
    for s in (1, -1): ell((1.4, s*0.75, 2.5), 0.62, (0.3, 0.85, 1.0))             # oreilles (petites, Asie)
    sw = math.sin(phase*2*math.pi)*0.12
    tr = [(2.25, 0, 2.3), (2.35, 0, 1.6), (2.32 + sw, 0, 0.95), (2.4 + sw*1.5, 0, 0.45), (2.6 + sw*1.5, 0, 0.3)]
    for (a, b), r in zip(zip(tr[:-1], tr[1:]), (0.36, 0.27, 0.2, 0.15)): caps(a, b, r)
    for s in (1, -1): caps((2.1, s*0.22, 1.95), (2.45, s*0.26, 1.7), 0.07)       # petites défenses
    for side, ph in ((1, 0.0), (-1, 0.5)):
        for fx, off in ((0.85, 0.0), (-0.85, 0.5)):                                # pas latéral de l'éléphant
            s = math.sin((phase + ph + off)*2*math.pi); lift = max(0, math.cos((phase + ph + off)*2*math.pi))*0.18
            top = (fx, side*0.55, 1.7); foot = (fx + 0.35*s, side*0.52, 0.32 + lift)
            caps(top, ((top[0] + foot[0])/2 + 0.05, side*0.55, 0.95 + lift*0.5), 0.55); caps(((top[0] + foot[0])/2 + 0.05, side*0.55, 0.95 + lift*0.5), foot, 0.5); ball(foot, 0.52)
    tw = math.sin(phase*2*math.pi + 1)*0.15
    caps((-1.25, 0, 2.4), (-1.72, tw*0.3, 2.0), 0.2); caps((-1.72, tw*0.3, 2.0), (-1.78, tw, 1.3), 0.13); ball((-1.78, tw*1.05, 1.22), 0.16)   # queue attachée à la croupe
    bpy.context.view_layer.objects.active = mo
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg)); bpy.data.objects.remove(mo, do_unlink=True)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    if link: col().objects.link(o)
    o.data.materials.append(m); return o

# ------------------------------------------------ relief réel (monts Gaoligong, 25 m) : forêt de montagne, roche, herbe
H = np.load('h.npy').astype(np.float64); ny, nx = H.shape; STEP = 25.0
xs = (np.arange(nx) - nx/2)*STEP; ys = (np.arange(ny) - ny/2)*STEP; X, Y = np.meshgrid(xs, ys)
Hn = H + gaussian_filter(rng.normal(0, 1, H.shape), 1.0)*3
gy, gx = np.gradient(gaussian_filter(Hn, 1), STEP); slope = np.hypot(gx, gy)
forest = np.array([0.06, 0.12, 0.05]); grass = np.array([0.22, 0.26, 0.10]); soil = np.array([0.30, 0.20, 0.12]); rock = np.array([0.28, 0.27, 0.24])
g = gaussian_filter(rng.uniform(0, 1, H.shape), 2)[..., None]
C = forest*(0.75 + 0.5*g) + (grass - forest)*np.clip(gaussian_filter(rng.normal(0, 1, H.shape), 6)*0.8 + (Hn - 3000)/500, 0, 1)[..., None]
C = C + (rock - C)*np.clip((slope - 0.65)*2.5, 0, 0.8)[..., None]
grid_mesh("terrain", X, Y, Hn, C, vcol_mat("terrain", 0.9, 0.35, 0.6))
ground = lambda x, y: float(map_coordinates(Hn, [[y/STEP + ny/2], [x/STEP + nx/2]], order=1)[0])
# point de départ : sur une crête (relief local maximal), 2 200-3 000 m, pente douce ; marche le long de la crête
SUM = np.array([1750.0, -6800.0])
Hs = gaussian_filter(Hn, 2); tpi = Hs - gaussian_filter(Hs, 14)
ok = (tpi > 35) & (Hs > 2200) & (Hs < 3000) & (gaussian_filter(slope, 2) < 0.4) & (np.abs(X) < 5000) & (np.abs(Y) < 5000)
iy, ix = np.unravel_index(np.argmax(np.where(ok, tpi, -1e9)), tpi.shape); P0 = np.array([xs[ix], ys[iy]])
best = None
for ang in np.arange(0, np.pi, np.pi/24):
    d = np.array([math.cos(ang), math.sin(ang)]); hh = [ground(*(P0 + d*s_)) for s_ in np.linspace(-300, 300, 13)]
    v = float(np.mean(np.abs(np.diff(hh))))
    if best is None or v < best[0]: best = (v, d)
W0 = best[1]; U = np.array([-W0[1], W0[0]]); V = W0
print("P0", P0, ground(*P0))
# ------------------------------------------------ forêt dense de montagne + buissons + herbe, sentier dégagé
LEAVES = [leaf_mat(f"lf{i}", t, 0.3) for i, t in enumerate([(0.05, 0.11, 0.04), (0.07, 0.14, 0.05), (0.09, 0.15, 0.05)])]
BARK = mat("bark", (0.12, 0.09, 0.07), 0.9)
TV = [tree_variant(f"t{i}", "small", LEAVES[i % 3], BARK, 50 + i) for i in range(4)] + [tree_variant(f"B{i}", "broad", LEAVES[i % 3], BARK, 70 + i) for i in range(2)] + [tree_variant(f"b{i}", "bush", LEAVES[i % 3], BARK, 80 + i) for i in range(2)]
tc = variant_collection("trees", TV)
N = 160000; px = rng.uniform(xs[0], xs[-1], N); py = rng.uniform(ys[0], ys[-1], N)
pz = map_coordinates(Hn, [py/STEP + ny/2, px/STEP + nx/2], order=1); ps = map_coordinates(slope, [py/STEP + ny/2, px/STEP + nx/2], order=1)
dens = np.clip((3700 - pz)/500, 0, 1)*np.clip(1.2 - ps*1.0, 0, 1)*0.9
dl = np.abs((px - P0[0])*U[0] + (py - P0[1])*U[1]); du = (px - P0[0])*U[0] + (py - P0[1])*U[1]; dw = (px - P0[0])*W0[0] + (py - P0[1])*W0[1]
keep = (rng.uniform(0, 1, N) < dens) & (dl > 9) & ~((du > 8) & (du < 45) & (dw > -70) & (dw < 30))   # champ libre devant la caméra
scatter("trees", np.stack([px, py, pz - 0.3], 1)[keep], rng.uniform(0.6, 1.3, keep.sum()), rng.uniform(0, 6.3, keep.sum()), rng.integers(0, 8, keep.sum()), tc)
GR = [tree_variant(f"g{i}", "grass", leaf_mat(f"gr{i}", t, 0.35), BARK, 300 + i) for i, t in enumerate([(0.16, 0.22, 0.07), (0.2, 0.26, 0.09), (0.13, 0.19, 0.06)])]
gc = variant_collection("grass", GR); NG = 45000
rr = 2 + 140*rng.uniform(0, 1, NG)**2; aa = rng.uniform(0, 6.3, NG); gx_ = P0[0] + rr*np.cos(aa); gy_ = P0[1] + rr*np.sin(aa)
gz_ = map_coordinates(Hn, [gy_/STEP + ny/2, gx_/STEP + nx/2], order=1)
onpath = np.abs((gx_ - P0[0])*U[0] + (gy_ - P0[1])*U[1]) < 2.5
sl = (~onpath | (rng.uniform(0, 1, NG) < 0.1)) & (rng.uniform(0, 1, NG) < 0.5)
scatter("grass", np.stack([gx_, gy_, gz_ - 0.05], 1)[sl], rng.uniform(0.3, 0.6, NG)[sl], rng.uniform(0, 6.3, NG)[sl], rng.integers(0, 3, NG)[sl], gc)
# ------------------------------------------------ la colonne : 6 éléphants à la file, caméra en travelling latéral
WALK = [elephant(f"w{k}", RED, k/8, link=False).data for k in range(8)]
NE, GAP = 6, 7.0
EL = [elephant(f"e{i}", RED, 0.0) for i in range(NE)]
for o in EL: o.data = WALK[0]
W = V; yaw = math.atan2(W[1], W[0])
def pos(i, t):
    p = P0 - W*(i*GAP) + W*0.9*t; return Vector((p[0], p[1], ground(*p) - 0.1))
sky(9, math.degrees(math.atan2(U[1], U[0])) + 140, dust=2.0, air=1.4, strength=0.45); sun(9, math.degrees(math.atan2(U[1], U[0])) + 140, 2.2, (1.0, 0.82, 0.62), 4.0)
cam = camera((0, 0, 0), (1, 1, 1), 30, dof=20, fstop=4.0)
def place(t):
    for i, o in enumerate(EL): o.data = WALK[int((t*0.7 + i*0.37) % 1*8) % 8]; o.location = pos(i, t); o.rotation_euler = (0, 0, yaw)
    k = t/DUR; lead = pos(0, t); mid = pos(2, t)
    off = Vector((*(-W*(10 - 4*k) + U*(30 - 3*k)), 0)); c = mid + off; c.z = max(ground(c.x, c.y) + 3.0, mid.z + 6.5)
    tg = mid + Vector((*(W*5 - U*30), 0)); tg.z = mid.z - 4.0; cam.location = c; cam.rotation_euler = (c - tg).to_track_quat("Z", "Y").to_euler()
    cam.data.dof.focus_distance = (mid - c).length
render_setup(SAMPLES, SCALE, float(os.environ.get("EXPO", -1.0)), mist=(60, 2600), mist_col=(0.8, 0.82, 0.82), mist_fac=0.8)
FR = os.environ.get("FRAMES")
if FR:
    a, b = map(int, FR.split(",")); os.makedirs(out, exist_ok=True)
    for f in range(a, b):
        p = os.path.join(out, f"{f:04d}.jpg")
        if os.path.exists(p): continue
        place(f/FPS); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
else:
    place(float(os.environ.get("T", 1.0))); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
