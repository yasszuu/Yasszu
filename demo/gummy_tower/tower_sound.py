"""Sound design for one gummy-tower clip, driven by the simulation JSON.

Usage: python tower_sound.py sim.json out.wav
"""
import json, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
S = json.load(open(sys.argv[1]))
FPS = S["fps"]
DUR = S["frames"] / FPS
rng = np.random.default_rng(S["seed"] % (2 ** 31))
mix = np.zeros((int((DUR + 1.5) * SR), 2))
SIZE = {"panda": 1.12, "penguin": 1.0, "cat": 0.95, "dog": 0.97, "bunny": 0.9, "ball": 1.7}

def ns(sec):
    return int(sec * SR)

def tt(sec):
    return np.arange(ns(sec)) / SR

def filt(x, lo=None, hi=None, order=2):
    if lo and hi:
        sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    elif lo:
        sos = signal.butter(order, lo, "highpass", fs=SR, output="sos")
    else:
        sos = signal.butter(order, hi, "lowpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)

def place(x, at, gain=1.0, pan=0.0):
    i = ns(max(at, 0))
    x = x[: max(0, len(mix) - i)]
    th = (np.clip(pan, -1, 1) + 1) * np.pi / 4
    mix[i:i + len(x), 0] += gain * np.cos(th) * x
    mix[i:i + len(x), 1] += gain * np.sin(th) * x

def tone(freq_curve, amp_curve):
    return np.sin(2 * np.pi * np.cumsum(freq_curve) / SR) * amp_curve

# ------------------------------------------------------------------ building blocks
def boing(f0, dur=0.22, wobble=0.07, decay=0.08):
    """Gummy impact: a pitch drop into a jelly wobble."""
    t = tt(dur)
    f = f0 * (1 + 0.6 * np.exp(-t / 0.012)) * (1 + wobble * np.exp(-t / 0.08) * np.sin(2 * np.pi * 17 * t))
    body = tone(f, np.exp(-t / decay) * np.clip(t / 0.002, 0, 1))
    body += 0.25 * tone(2.01 * f, np.exp(-t / (decay * 0.6)))
    squish = filt(rng.standard_normal(len(t)), 250, 2600) * np.exp(-t / 0.022)
    return norm(body) + 0.45 * norm(squish)

def tok(freqs=(1150, 2650), dur=0.08):
    t = tt(dur)
    return norm(sum(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.02) for f in freqs))

def thud(dur=0.18):
    t = tt(dur)
    return norm(filt(rng.standard_normal(len(t)), None, 350) * np.exp(-t / 0.04)
                + 0.8 * tone(90 * (1 + np.exp(-t / 0.02)), np.exp(-t / 0.06)))

def pop(f0):
    t = tt(0.07)
    return tone(f0 * (1 + 1.4 * t / 0.07), np.exp(-t / 0.018) * np.clip(t / 0.001, 0, 1))

def whoosh(dur, lo, hi, rise=True):
    t = tt(dur)
    e = (t / dur) ** 2 if rise else np.exp(-t / (dur / 4))
    return norm(filt(rng.standard_normal(len(t)), lo, hi)) * e

def marimba(f, dur=0.6):
    t = tt(dur)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / 0.03)) \
        * np.exp(-t / 0.22) * np.clip(t / 0.002, 0, 1)

def slide_whistle(dur=0.9):
    t = tt(dur)
    f = np.geomspace(1900, 320, len(t)) * (1 + 0.025 * np.sin(2 * np.pi * 6 * t))
    env = np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.12, 0, 1)
    x = tone(f, env) + 0.12 * tone(2 * f, env)
    return norm(x + 0.08 * filt(rng.standard_normal(len(t)), 1500, 6000) * env)

# ------------------------------------------------------------------ clip start + spawns
place(marimba(1046.5) + marimba(1568.0) * 0, 0.02, 0.18)
place(marimba(1568.0), 0.12, 0.16)
for k, ts in enumerate(S["spawn_t"]):
    place(pop(rng.uniform(520, 760)), ts, 0.16, rng.uniform(-0.3, 0.3))
    place(whoosh(0.35, 1200, 5000, rise=False), ts + 0.02, 0.05)

# ------------------------------------------------------------------ impacts
bodies = S["bodies"]
last_hit = {}
for c in S["contacts"]:
    a, b, v = c["a"], c["b"], c["speed"]
    animal = a if isinstance(a, int) else b if isinstance(b, int) else None
    other = b if animal == a else a
    if animal is None:
        continue
    if c["t"] - last_hit.get(animal, -1) < 0.07:
        continue
    last_hit[animal] = c["t"]
    g = min(1.0, v / 4.5) ** 0.9
    size = SIZE.get(bodies[animal]["name"], 1.0)
    pan = float(np.clip(c["x"] / 4.0, -1, 1))
    f0 = 330 / size * rng.uniform(0.9, 1.12)
    place(boing(f0), c["t"], 0.5 * g, pan)
    if other == "pedestal":
        place(tok(), c["t"], 0.22 * g, pan)
    elif other == "floor":
        place(thud(), c["t"], 0.65 * g, pan)

# ------------------------------------------------------------------ event
ev = S["event"]
if ev["type"] == "ball" and "frame" in ev:
    t0 = ev["frame"] / FPS
    travel = 6.5 / ev["speed"]
    place(whoosh(travel + 0.1, 400, 3500), t0, 0.5, -ev["side"] * 0.6)
    ball_i = next(i for i, b in enumerate(bodies) if b["kind"] == "ball")
    hits = [c for c in S["contacts"] if ball_i in (c["a"], c["b"])]
    if hits:
        th = hits[0]["t"]
        place(boing(120, dur=0.6, wobble=0.12, decay=0.22), th, 0.9)
        place(norm(filt(rng.standard_normal(ns(0.35)), 200, 3000) * np.exp(-tt(0.35) / 0.06)), th, 0.5)
elif ev["type"] == "quake":
    t0 = ev["frame"] / FPS
    L = 3.0
    t = tt(L)
    env = np.sin(np.pi * t / L) ** 1.5
    am = 0.6 + 0.4 * np.sin(2 * np.pi * ev["freq"] * t)
    rumble = norm(filt(rng.standard_normal(len(t)), None, 140, 4)) * env * am
    rumble += 0.5 * np.sin(2 * np.pi * 42 * t) * env
    place(rumble, t0, 0.8 * min(1, ev["amp"] / 0.1 + 0.3))
    rattle = filt(rng.standard_normal(len(t)), 1800, 6000) * (rng.random(len(t)) < 0.002) * env
    place(norm(rattle + 1e-9), t0, 0.15)

# ------------------------------------------------------------------ verdict cues
ped_top = S["ped_top"]
falls = []
seen = set()
for f, rec in enumerate(S["records"]):
    for k, (x, z, th) in rec.items():
        i = int(k)
        if bodies[i]["kind"] == "animal" and i not in seen and z < ped_top - 0.35:
            seen.add(i)
            falls.append(f / FPS)
falls.sort()
collapse_t = None
for k in range(len(falls)):
    window = [x for x in falls if falls[k] <= x <= falls[k] + 1.2]
    if len(window) >= max(2, min(3, S["n"] // 2)):
        collapse_t = falls[k]
        break
if collapse_t is not None:
    place(slide_whistle(), collapse_t - 0.1, 0.32)
else:
    t_end = DUR - 1.4
    for k, f in enumerate((1046.5, 1318.5, 1568.0, 2093.0)):
        place(marimba(f, 0.9), t_end + 0.09 * k, 0.22)

# ------------------------------------------------------------------ room + master
ir_t = tt(0.5)
ir = np.stack([filt(rng.standard_normal(len(ir_t)), None, 6000) * np.exp(-ir_t / 0.09) for _ in range(2)], 1)
ir /= np.sqrt((ir ** 2).sum(0))
wet = np.stack([signal.fftconvolve(mix[:, c], ir[:, c])[: len(mix)] for c in range(2)], 1)
out = mix + 0.18 * wet
out = filt(out.T, 30, None).T
out /= np.max(np.abs(out)) + 1e-9
out = np.tanh(out * 1.5) / np.tanh(1.5) * 0.89
out = out[: ns(DUR)]
wavfile.write(sys.argv[2], SR, (out * 32767).astype(np.int16))
print(f"wrote {sys.argv[2]} {len(out) / SR:.2f}s, collapse={collapse_t}, falls={len(falls)}")
