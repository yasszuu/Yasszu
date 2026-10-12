"""Plan 3D : le lion de l'Atlas (forme rouge) marche sur une crête du Haut Atlas au soleil couchant.
bl/bin/python atlas.py <out(.jpg|dir)> [samples] [scale%]   (FRAMES=a,b pour une séquence, T=t pour une image)"""
import sys, os; sys.path.insert(0, '../gombe3d'); from lib import *
from scipy.ndimage import gaussian_filter, map_coordinates
out = sys.argv[1]; SAMPLES = int(sys.argv[2]) if len(sys.argv) > 2 else 24; SCALE = int(sys.argv[3]) if len(sys.argv) > 3 else 50
FPS, DUR = 30, 4.6
sc = reset()
RED = mat("lion", (0.85, 0.0, 0.0), 0.55, emit=(1, 0, 0), emit_s=0.2)
def lion(name, m, phase=0.0, link=True):
    """Lion maquette (metaballs → maillage), x = avant, taille réelle (~1,1 m au garrot)."""
    mb = bpy.data.metaballs.new(name + "_mb"); mb.resolution = 0.04; mb.render_resolution = 0.03; mb.threshold = 0.6
    mo = bpy.data.objects.new(name + "_mbo", mb); col().objects.link(mo)
    def ball(p, r): e = mb.elements.new(); e.type = "BALL"; e.co = p; e.radius = r; return e
    def ell(p, r, s): e = mb.elements.new(); e.type = "ELLIPSOID"; e.co = p; e.radius = r; e.size_x, e.size_y, e.size_z = s; return e
    def caps(p0, p1, r):
        p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; e = mb.elements.new(); e.type = "CAPSULE"
        e.co = (p0 + p1)/2; e.radius = r; e.size_x = d.length/2; e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized()); return e
    ell((0, 0, 0.86), 0.47, (1.75, 0.95, 0.9))                                      # corps
    ball((0.5, 0, 0.92), 0.47); ball((-0.55, 0, 0.86), 0.42)                      # épaules / hanches
    ell((0.72, 0, 1.12), 0.56, (1.0, 1.25, 1.3)); ell((0.62, 0, 0.78), 0.4, (0.9, 1.0, 1.0))                                 # crinière
    ball((1.05, 0, 1.1), 0.28); ball((1.27, 0, 1.0), 0.15)                         # tête + museau
    ball((1.0, 0.2, 1.38), 0.08); ball((1.0, -0.2, 1.38), 0.08)                 # oreilles
    for side, ph in ((1, 0.0), (-1, 0.5)):
        for fx, off in ((0.55, 0.0), (-0.6, 0.5)):                                 # pattes avant / arrière, diagonales opposées
            s = math.sin((phase + ph + off)*2*math.pi); lift = max(0, math.cos((phase + ph + off)*2*math.pi))*0.12
            top = (fx, side*0.2, 0.85); knee = (fx + 0.1*s - (0.08 if fx < 0 else 0), side*0.21, 0.45 + lift*0.5); paw = (fx + 0.25*s, side*0.21, 0.07 + lift)
            caps(top, knee, 0.16 if fx > 0 else 0.17); caps(knee, paw, 0.12); ball((paw[0] + 0.06, paw[1], paw[2]), 0.13)
    sw = math.sin(phase*2*math.pi)*0.12
    pts = [(-0.95, 0, 0.98), (-1.3, sw*0.5, 0.82), (-1.55, sw, 0.55), (-1.65, sw*1.3, 0.38)]
    for a, b in zip(pts[:-1], pts[1:]): caps(a, b, 0.05)
    ball(pts[-1], 0.09)                                                            # touffe de la queue
    bpy.context.view_layer.objects.active = mo
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg)); bpy.data.objects.remove(mo, do_unlink=True)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    if link: col().objects.link(o)
    o.data.materials.append(m); return o

# ------------------------------------------------ relief réel (Haut Atlas, 25 m), couleurs : terre rouge, roche, neige
H = np.load('h.npy').astype(np.float64); ny, nx = H.shape; STEP = 25.0
xs = (np.arange(nx) - nx/2)*STEP; ys = (np.arange(ny) - ny/2)*STEP; X, Y = np.meshgrid(xs, ys)
Hn = H + gaussian_filter(rng.normal(0, 1, H.shape), 1.0)*3
gy, gx = np.gradient(gaussian_filter(Hn, 1), STEP); slope = np.hypot(gx, gy)
soil = np.array([0.36, 0.17, 0.09]); dry = np.array([0.38, 0.30, 0.17]); rock = np.array([0.30, 0.26, 0.23]); snow = np.array([0.85, 0.86, 0.9]); green = np.array([0.13, 0.15, 0.06])
g = gaussian_filter(rng.uniform(0, 1, H.shape), 2)[..., None]
C = soil*(0.7 + 0.6*g) + (dry - soil)*np.clip(gaussian_filter(rng.normal(0, 1, H.shape), 5), 0, 1)[..., None]
C = C + (rock - C)*np.clip((slope - 0.45)*2.5, 0, 0.85)[..., None]
C = C + (green - C)*(np.clip((2400 - Hn)/600, 0, 0.6)*np.clip(gaussian_filter(rng.normal(0, 1, H.shape), 3) + 0.2, 0, 1))[..., None]
snowk = np.clip((Hn - 2850 - 120*gaussian_filter(rng.normal(0, 1, H.shape), 4))/140, 0, 1)*np.clip(1.2 - slope, 0, 1)
C = C + (snow - C)*snowk[..., None]
grid_mesh("terrain", X, Y, Hn, C, vcol_mat("terrain", 0.9, 0.35, 0.6))
ground = lambda x, y: float(map_coordinates(Hn, [[y/STEP + ny/2], [x/STEP + nx/2]], order=1)[0])
# ------------------------------------------------ végétation : genévriers / chênes verts épars, touffes d'herbe sèche, rochers
LEAVES2 = [mat(f"jun{i}", t, 0.8) for i, t in enumerate([(0.05, 0.09, 0.04), (0.07, 0.1, 0.05), (0.09, 0.11, 0.05)])]
BARK = mat("bark", (0.12, 0.09, 0.07), 0.9)
TV = [tree_variant(f"t{i}", "small", LEAVES2[i % 3], BARK, 50 + i) for i in range(3)] + [tree_variant(f"b{i}", "bush", LEAVES2[i % 3], BARK, 80 + i) for i in range(2)]
tc = variant_collection("trees", TV)
P0 = np.array([-750.0, -3500.0]); SUMMIT = np.array([-3850.0, 5225.0]); U = (SUMMIT - P0)/np.linalg.norm(SUMMIT - P0); V = np.array([U[1], -U[0]])
N = 60000; px = rng.uniform(xs[0], xs[-1], N); py = rng.uniform(ys[0], ys[-1], N)
pz = map_coordinates(Hn, [py/STEP + ny/2, px/STEP + nx/2], order=1); ps = map_coordinates(slope, [py/STEP + ny/2, px/STEP + nx/2], order=1)
dens = np.clip((2700 - pz)/700, 0, 1)*np.clip(1 - ps*1.5, 0, 1)*0.5
dc = np.hypot(px - P0[0], py - P0[1]); keep = (rng.uniform(0, 1, N) < dens) & (dc > 60)
scatter("trees", np.stack([px, py, pz - 0.3], 1)[keep], rng.uniform(0.6, 1.2, keep.sum()), rng.uniform(0, 6.3, keep.sum()), rng.integers(0, 5, keep.sum()), tc)
GR = [tree_variant(f"g{i}", "grass", leaf_mat(f"gr{i}", t, 0.35), BARK, 300 + i) for i, t in enumerate([(0.36, 0.26, 0.12), (0.42, 0.32, 0.16), (0.3, 0.22, 0.1)])]
gc = variant_collection("grass", GR); NG = 40000
rr = 1.5 + 120*rng.uniform(0, 1, NG)**2; aa = rng.uniform(0, 6.3, NG); gx_ = P0[0] + rr*np.cos(aa); gy_ = P0[1] + rr*np.sin(aa)
gz_ = map_coordinates(Hn, [gy_/STEP + ny/2, gx_/STEP + nx/2], order=1)
onpath = np.abs((gx_ - P0[0])*V[0] + (gy_ - P0[1])*V[1]) < 1.6                     # sentier dégagé pour le lion
sl = ~onpath | (rng.uniform(0, 1, NG) < 0.15)
sl &= rng.uniform(0, 1, NG) < 0.45
scatter("grass", np.stack([gx_, gy_, gz_ - 0.05], 1)[sl], rng.uniform(0.2, 0.42, NG)[sl], rng.uniform(0, 6.3, NG)[sl], rng.integers(0, 3, NG)[sl], gc)
ROCK = mat("rock", (0.32, 0.25, 0.2), 0.85)
spec = []
for k in range(420):
    r_ = 3 + 90*rng.uniform()**1.5; a_ = rng.uniform(0, 6.3); x_, y_ = P0[0] + r_*math.cos(a_), P0[1] + r_*math.sin(a_)
    if abs((x_ - P0[0])*V[0] + (y_ - P0[1])*V[1]) < 2.5: continue
    s_ = rng.uniform(0.12, 0.55)*(1 + r_/60); spec.append((x_, y_, ground(x_, y_) + s_*0.15, s_*rng.uniform(1, 1.5), s_*rng.uniform(0.8, 1.2), s_*0.55, k))
obj_from("rocks", *blobs(spec, 2, 0.28), ROCK)
# ------------------------------------------------ le lion (marche vers le sommet) + caméra en travelling latéral
WALK = [lion(f"w{k}", RED, k/8, link=False).data for k in range(8)]
L = lion("lion", RED, 0.0); L.data = WALK[0]
yaw = math.atan2(-U[1], -U[0])                 # le lion vient vers nous, le sommet enneigé derrière lui
def lion_at(t):
    p = P0 + U*6 - U*1.3*t; return Vector((p[0], p[1], ground(*p) - 0.05))
sky(6, 90 - 200, dust=1.4, air=1.1, strength=0.55); sun(6, 200, 3.0, (1.0, 0.6, 0.35), 1.0)
cam = camera((0, 0, 0), (1, 1, 1), 32, dof=8, fstop=3.2)
def place(t):
    L.data = WALK[int((t*1.3) % 1*8) % 8]; L.location = lion_at(t); L.rotation_euler = (0, 0, yaw)
    lp = lion_at(t); k = t/DUR
    off = Vector((*(-U*(5.0 - 0.8*k) + V*(4.2 - 1.2*k)), 0)); c = lp + off; c.z = max(ground(c.x, c.y) + 1.2, lp.z + 1.25)
    tg = lp + Vector((*(-U*0.4), 0)) + Vector((0, 0, 1.25)); cam.location = c; cam.rotation_euler = (c - tg).to_track_quat("Z", "Y").to_euler()
    cam.data.dof.focus_distance = (lp - c).length
render_setup(SAMPLES, SCALE, float(os.environ.get("EXPO", -1.3)), mist=(200, 30000), mist_col=(0.9, 0.62, 0.45), mist_fac=0.7)
FR = os.environ.get("FRAMES")
if FR:
    a, b = map(int, FR.split(",")); os.makedirs(out, exist_ok=True)
    for f in range(a, b):
        p = os.path.join(out, f"{f:04d}.jpg")
        if os.path.exists(p): continue
        place(f/FPS); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
else:
    place(float(os.environ.get("T", 1.0))); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
