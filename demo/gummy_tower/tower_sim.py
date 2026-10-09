"""Planar physics for the gummy animal tower (pybullet).

Animals drop one by one onto a pedestal; then a random event (nothing / projectile / quake)
decides whether the tower stands. Writes per-frame planar transforms + contact events as JSON.

Usage: python tower_sim.py --n 5 --out sim.json [--seed S] [--event none|ball|quake]
"""
import argparse, json, math, os, random, tempfile
import numpy as np
import pybullet as p
from scipy.spatial import ConvexHull
from shapes import ANIMALS, GUMMY_COLORS, THICK, animal_geometry

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--seed", type=int, default=None)
ap.add_argument("--event", default=None)
ap.add_argument("--interval", type=float, default=None)
args = ap.parse_args()

seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1 << 30)
rng = random.Random(seed)
FPS, SUB = 30, 8
DT = 1 / (FPS * SUB)
G = 15.0                       # a bit more than earth gravity: reads as small candy
PED_TOP, PED_R = 1.2, 1.45     # pedestal top height and half width
DROP = 1.6                     # spawn height above the settled tower top
INTERVALS = {1: 0.9, 3: 0.9, 5: 0.85, 10: 0.6, 20: 0.42, 30: 0.34, 50: 0.27}
interval = args.interval or INTERVALS.get(args.n, 0.4)
event = args.event or rng.choice(["none", "ball", "quake"])

p.connect(p.DIRECT)
p.setGravity(0, 0, -G)
p.setPhysicsEngineParameter(fixedTimeStep=DT, numSolverIterations=60)

tmp = tempfile.mkdtemp()

def hull_obj(poly, name):
    pts = [(x, y, z) for (x, z) in poly.exterior.coords[:-1] for y in (-THICK / 2, THICK / 2)]
    pts = np.array(pts)
    hull = ConvexHull(pts)
    path = os.path.join(tmp, name + ".obj")
    with open(path, "w") as f:
        for v in pts:
            f.write("v %f %f %f\n" % tuple(v))
        for s in hull.simplices:
            f.write("f %d %d %d\n" % tuple(s + 1))
    return path

shape_cache = {}
def animal_shape(name):
    if name not in shape_cache:
        outline, parts, _, _ = animal_geometry(name)
        files = [hull_obj(pp, f"{name}_{i}") for i, pp in enumerate(parts)]
        col = p.createCollisionShapeArray([p.GEOM_MESH] * len(files), fileNames=files)
        shape_cache[name] = (col, outline.area)
    return shape_cache[name]

def set_material(b, restitution=0.1, friction=1.2):
    p.changeDynamics(b, -1, restitution=restitution, lateralFriction=friction,
                     rollingFriction=0.002, spinningFriction=0.002,
                     linearDamping=0.04, angularDamping=0.25)

# world: floor + pedestal (dynamic, pinned by a constraint so a quake can drag it around)
floor = p.createMultiBody(0, p.createCollisionShape(p.GEOM_PLANE))
set_material(floor, 0.2, 0.9)
ped_col = p.createCollisionShape(p.GEOM_CYLINDER, radius=PED_R, height=PED_TOP)
ped = p.createMultiBody(500, ped_col, basePosition=[0, 0, PED_TOP / 2])
set_material(ped, 0.2, 0.9)
pin = p.createConstraint(ped, -1, -1, -1, p.JOINT_FIXED, [0, 0, 0], [0, 0, 0], [0, 0, PED_TOP / 2])
p.changeConstraint(pin, maxForce=1e7)

bodies = []   # dicts: id, kind, name, color, spawn_frame
species = list(ANIMALS)
colors = list(GUMMY_COLORS)

def planar(b):
    """Keep a body in the XZ plane, rotating only about Y (like the 2D stacking games)."""
    pos, orn = p.getBasePositionAndOrientation(b)
    v, w = p.getBaseVelocity(b)          # read before the reset, which zeroes velocity
    m = np.array(p.getMatrixFromQuaternion(orn)).reshape(3, 3)
    th = math.atan2(m[0, 2], m[0, 0])
    p.resetBasePositionAndOrientation(b, [pos[0], 0, pos[2]], p.getQuaternionFromEuler([0, th, 0]))
    p.resetBaseVelocity(b, [v[0], 0, v[2]], [0, w[1], 0])
    return pos[0], pos[2], th

def settled_top():
    top = PED_TOP
    for b in bodies:
        v, _ = p.getBaseVelocity(b["id"])
        if abs(v[2]) < 1.2:
            top = max(top, p.getAABB(b["id"])[1][2])
    return top

def highest_x():
    best, x = -1, 0.0
    for b in bodies:
        if b["kind"] != "animal":
            continue
        (x0, _, _), (x1, _, z1) = p.getAABB(b["id"])
        if z1 > best:
            best, x = z1, (x0 + x1) / 2
    return x

# ----------------------------------------------------------------------------- schedule
t_first = 0.5
spawn_t = [t_first + i * interval for i in range(args.n)]
t_event = spawn_t[-1] + DROP / 4 + 1.0
EVENT_LEN = {"none": 2.5, "ball": 2.5, "quake": 3.0}[event]
t_end = t_event + EVENT_LEN + 1.9
frames = int(math.ceil(t_end * FPS))

ev = {"type": event}
if event == "ball":
    ev.update(side=rng.choice([-1, 1]), height_frac=rng.uniform(0.25, 0.85),
              speed=rng.uniform(5.0, 11.0), radius=0.42)
elif event == "quake":
    ev.update(amp=rng.uniform(0.04, 0.16), freq=rng.uniform(3.0, 6.0))

records = []     # per frame: {body_index: [x, z, th]}
contacts = []    # impact events
tops = []
ped_x = []
prev_vel = {}
prev_pairs = {}
next_spawn = 0
step = 0
ball = None
for f in range(frames):
    for s in range(SUB):
        t = step * DT
        # spawn
        while next_spawn < args.n and t >= spawn_t[next_spawn]:
            name = rng.choice(species)
            col, area = animal_shape(name)
            top = settled_top()
            x = 0.85 * highest_x() + rng.gauss(0, 0.13)
            th = rng.uniform(-0.3, 0.3)
            b = p.createMultiBody(area * THICK * 1.2, col,
                                  basePosition=[x, 0, top + DROP],
                                  baseOrientation=p.getQuaternionFromEuler([0, th, 0]))
            set_material(b)
            p.resetBaseVelocity(b, [0, 0, -0.5], [0, 0, 0])
            bodies.append({"id": b, "kind": "animal", "name": name,
                           "color": rng.choice(colors), "spawn_frame": f})
            next_spawn += 1
        # events
        if event == "ball" and ball is None and t >= t_event:
            h = PED_TOP + ev["height_frac"] * max(settled_top() - PED_TOP, 0.6)
            x0 = -ev["side"] * 6.5
            sc = p.createCollisionShape(p.GEOM_SPHERE, radius=ev["radius"])
            ball = p.createMultiBody(4.0, sc, basePosition=[x0, 0, h + 0.25])
            set_material(ball, 0.45, 0.6)
            p.resetBaseVelocity(ball, [ev["side"] * ev["speed"], 0, 1.2], [0, 0, 0])
            bodies.append({"id": ball, "kind": "ball", "name": "ball",
                           "color": rng.choice(colors), "spawn_frame": f})
            ev["frame"] = f
        if event == "quake":
            k = (t - t_event) / EVENT_LEN
            a = ev["amp"] * math.sin(math.pi * min(max(k, 0), 1)) if 0 <= k <= 1 else 0.0
            dx = a * math.sin(2 * math.pi * ev["freq"] * (t - t_event))
            p.changeConstraint(pin, [dx, 0, PED_TOP / 2], maxForce=1e7)
            ev["frame"] = int(t_event * FPS)
        p.stepSimulation()
        step += 1
        # contacts: a pair that was not touching on the previous step is an impact
        pairs = {}
        for c in p.getContactPoints():
            a_, b_ = c[1], c[2]
            key = (min(a_, b_), max(a_, b_))
            pairs[key] = c
        for key, c in pairs.items():
            if key in prev_pairs or key[0] == key[1]:
                continue
            n = np.array(c[7])
            va = np.array(prev_vel.get(c[1], (0, 0, 0)))
            vb = np.array(prev_vel.get(c[2], (0, 0, 0)))
            speed = abs(float(np.dot(va - vb, n)))
            if speed > 0.35:
                contacts.append({"t": step * DT, "a": c[1], "b": c[2], "speed": round(speed, 3),
                                 "x": round(c[5][0], 3), "z": round(c[5][2], 3)})
        prev_pairs = pairs
        for b in bodies:
            prev_vel[b["id"]] = p.getBaseVelocity(b["id"])[0]
    rec = {}
    for i, b in enumerate(bodies):
        x, z, th = planar(b["id"])
        rec[i] = [round(x, 4), round(z, 4), round(th, 4)]
    records.append(rec)
    tops.append(settled_top())
    ped_x.append(p.getBasePositionAndOrientation(ped)[0][0])

# outcome: how many animals are still on the pedestal at the end
on_ped = sum(1 for b in bodies if b["kind"] == "animal"
             and p.getBasePositionAndOrientation(b["id"])[0][2] > PED_TOP - 0.05)
max_top = max(tops)
collapse_frame = None
for f, tp in enumerate(tops):
    if f > int(spawn_t[min(2, args.n - 1)] * FPS) and tp < PED_TOP + 0.6 * (max_top - PED_TOP) \
            and max_top - tp > 0.8:
        collapse_frame = f
        break

id_index = {b["id"]: i for i, b in enumerate(bodies)}
for c in contacts:
    for k in ("a", "b"):
        c[k] = id_index.get(c[k], "floor" if c[k] == floor else "pedestal" if c[k] == ped else "?")

json.dump({"n": args.n, "seed": seed, "fps": FPS, "frames": frames, "event": ev,
           "ped_top": PED_TOP, "ped_r": PED_R,
           "bodies": [{k: v for k, v in b.items() if k != "id"} for b in bodies],
           "records": records, "tops": tops, "ped_x": ped_x, "contacts": contacts,
           "spawn_t": spawn_t, "on_pedestal": on_ped, "collapse_frame": collapse_frame},
          open(args.out, "w"))
print(f"n={args.n} seed={seed} event={event} frames={frames} on_pedestal={on_ped}/{args.n} "
      f"collapse_frame={collapse_frame} contacts={len(contacts)} max_top={max_top:.2f}")
