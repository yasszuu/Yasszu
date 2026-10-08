"""Procedural sound design for the watermelon cuts animation.

Reads the motion JSON dumped by watermelon.py (--dump) and writes a stereo WAV whose
events (throw, blade swishes, slices, juice, burst, every piece impact) are synced to it.
Usage: python sound.py motion.json out.wav
"""
import json, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(7)
m = json.load(open(sys.argv[1]))
FPS, END = m["fps"], m["end"]
dur = END / FPS + 0.6
mix = np.zeros((int(dur * SR), 2))

def t_of(frame):
    return (frame - 1) / FPS

def n_samp(sec):
    return int(sec * SR)

def noise(sec):
    return rng.standard_normal(n_samp(sec))

def band(x, lo=None, hi=None, order=4):
    if lo and hi:
        sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    elif lo:
        sos = signal.butter(order, lo, "highpass", fs=SR, output="sos")
    else:
        sos = signal.butter(order, hi, "lowpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def env(sec, attack, tau):
    t = np.arange(n_samp(sec)) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / tau)

def place(x, at, gain=1.0, pan=0.0):
    """Mix mono x at time `at` (s) with constant-power pan in [-1, 1]."""
    i = n_samp(at)
    if i < 0:
        x, i = x[-i:], 0
    x = x[: max(0, len(mix) - i)]
    th = (np.clip(pan, -1, 1) + 1) * np.pi / 4
    mix[i:i + len(x), 0] += x * gain * np.cos(th)
    mix[i:i + len(x), 1] += x * gain * np.sin(th)

def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)

def sweep_tone(sec, f0, f1, tau):
    t = np.arange(n_samp(sec)) / SR
    f = f1 + (f0 - f1) * np.exp(-t / (sec / 3))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau)

def crackle(sec, density, lo, hi):
    x = np.zeros(n_samp(sec))
    k = rng.random(len(x)) < density / SR
    x[k] = rng.standard_normal(k.sum())
    return band(x, lo, hi, 2)

def ringing(sec, freqs, decays, amps):
    t = np.arange(n_samp(sec)) / SR
    return sum(a * np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t / d)
               for f, d, a in zip(freqs, decays, amps))

# ------------------------------------------------------------- throw: melon flies past the lens
mel = np.array(m["melon"])
cam = np.array(m["cam"])
dist = np.linalg.norm(mel - cam, axis=1)
closest = int(np.argmin(dist[: m["arrive"]])) + 1
tp = t_of(closest)
L = 1.6
t = np.arange(n_samp(L)) / SR
# whoosh: loud and bright as it passes the camera, then darker and quieter as it recedes
pass_env = np.where(t < tp, (t / max(tp, 1e-3)) ** 2, np.exp(-(t - tp) / 0.28))
hi_layer = band(noise(L), 1800, 7000) * np.where(t < tp, pass_env, np.exp(-(t - tp) / 0.09))
lo_layer = band(noise(L), 120, 1200) * pass_env
tumble = 1 + 0.5 * np.sin(2 * np.pi * np.cumsum(np.interp(t, [0, L], [11, 3])) / SR)
whoosh = norm(0.6 * norm(hi_layer) + norm(lo_layer)) * tumble
pan = np.interp(t, [0, tp, L], [0.6, 0.15, 0.0])
th = (pan + 1) * np.pi / 4
mix[: len(t), 0] += 0.75 * whoosh * np.cos(th)
mix[: len(t), 1] += 0.75 * whoosh * np.sin(th)
place(sweep_tone(0.35, 140, 55, 0.12), tp - 0.02, 0.5)          # body "whomp" past the lens

# anticipation swell into the first cut
t_cut0 = t_of(m["cuts"][0])
sw_len = 0.55
sw = band(noise(sw_len), 3000, 12000) * np.linspace(0, 1, n_samp(sw_len)) ** 3
place(norm(sw), t_cut0 - sw_len + 0.02, 0.18)

# ------------------------------------------------------------- the cuts
for i, s in enumerate(m["cuts"]):
    p = 0.4 if i % 2 == 0 else -0.4
    pitch = 1 + rng.uniform(-0.08, 0.08)
    ts = t_of(s)
    # blade swish through the air
    sw = band(noise(0.16), 2500 * pitch, 11000) * env(0.16, 0.03, 0.035)
    place(norm(sw), ts - 0.015, 0.5, -p)
    # metallic "shing"
    ring = ringing(0.5, np.array([2870, 4610, 6930, 9180]) * pitch,
                   [0.16, 0.11, 0.08, 0.05], [0.5, 0.35, 0.25, 0.15])
    place(norm(ring) * env(0.5, 0.002, 0.2), ts, 0.16, -p * 0.5)
    tc = ts + 1 / FPS                                            # blade inside the fruit
    # rind crack
    crack = crackle(0.07, 1800, 900, 6000) * env(0.07, 0.001, 0.02)
    place(norm(crack), tc - 0.01, 0.55, p * 0.3)
    # wet flesh slice / squelch
    sq = band(noise(0.16), 150, 1400) * env(0.16, 0.004, 0.045)
    place(norm(sq), tc, 0.7, p * 0.2)
    place(sweep_tone(0.12, 260 * pitch, 120 * pitch, 0.04), tc, 0.35, p * 0.2)
    # juice squirt: sprayed droplets
    sp = (band(noise(0.35), 2000, 9000) * env(0.35, 0.01, 0.09)
          + crackle(0.35, 600, 1500, 7000) * env(0.35, 0.005, 0.12) * 2)
    place(norm(sp), tc + 0.01, 0.38, p * 0.6)

# ------------------------------------------------------------- burst
tb = t_of(m["release"]) + 0.5 / FPS
splat = band(noise(0.6), 80, 2500) * env(0.6, 0.003, 0.11)
place(norm(splat), tb, 0.85)
place(sweep_tone(0.7, 90, 38, 0.22), tb, 0.8)                     # sub thump
place(norm(crackle(0.4, 2500, 700, 6000) * env(0.4, 0.001, 0.07)), tb, 0.5)
spr = band(noise(1.0), 1800, 9000) * env(1.0, 0.01, 0.25)
place(norm(spr), tb + 0.02, 0.35)
# droplets pattering down over the next second
for _ in range(140):
    td = tb + 0.25 + rng.gamma(2.0, 0.22)
    drop = band(rng.standard_normal(n_samp(0.03)), 2500, 7500, 2) * env(0.03, 0.0005, 0.006)
    place(norm(drop), td, rng.uniform(0.04, 0.16), rng.uniform(-0.9, 0.9))

# ------------------------------------------------------------- impacts from the simulation
def wood_knock(v):
    k = ringing(0.35, np.array([185, 405, 730, 1160]) * rng.uniform(0.92, 1.08),
                [0.11, 0.07, 0.045, 0.03], [1.0, 0.7, 0.5, 0.3])
    click = band(noise(0.02), 1500, 6000) * env(0.02, 0.0005, 0.004)
    out = norm(k) * 0.8
    out[: len(click)] += norm(click) * 0.4
    return out

def floor_thud(v):
    th_ = band(noise(0.25), None, 500) * env(0.25, 0.001, 0.05)
    return norm(th_) + 0.6 * sweep_tone(0.25, 110, 60, 0.06)

def wet_slap(v):
    return norm(band(noise(0.12), 300, 3500) * env(0.12, 0.001, 0.025))

events = []
for name, tr in m["pieces"].items():
    p = np.array(tr)
    vz = np.diff(p[:, 2])                                         # m / frame
    last = -99
    for f in range(m["release"] + 1, len(vz)):
        dv = vz[f] - vz[f - 1]
        if vz[f - 1] < -0.02 and dv > 0.03 and f - last > 3:
            x, y, z = p[f]
            on_board = abs(x) < 1.65 and abs(y) < 0.68 and z < 0.8
            events.append((f + 1, min(1.0, (dv / 0.15)) ** 0.8, x, on_board))
            last = f
print(f"{len(events)} impacts")
for f, g, x, on_board in events:
    at = t_of(f) - 0.5 / FPS
    pan = float(np.clip(x / 2.5, -1, 1))
    body = wood_knock(g) if on_board else floor_thud(g)
    place(body, at, 0.55 * g, pan)
    place(wet_slap(g), at, 0.35 * g, pan)

# ------------------------------------------------------------- room + master
ir_len = 0.7
ir_t = np.arange(n_samp(ir_len)) / SR
ir = np.stack([band(rng.standard_normal(len(ir_t)), None, 5000) * np.exp(-ir_t / 0.13) for _ in range(2)], 1)
ir /= np.sqrt((ir ** 2).sum(0))
wet = np.stack([signal.fftconvolve(mix[:, c], ir[:, c])[: len(mix)] for c in range(2)], 1)
out = mix + 0.22 * wet
out = band(out.T, 30, None, 2).T                                   # remove DC / rumble
out /= np.max(np.abs(out)) + 1e-9
out = np.tanh(out * 1.6) / np.tanh(1.6)                             # gentle limiter
out *= 10 ** (-1 / 20)
out = out[: n_samp(END / FPS)]
wavfile.write(sys.argv[2], SR, (out * 32767).astype(np.int16))
print("wrote", sys.argv[2], out.shape[0] / SR, "s")
