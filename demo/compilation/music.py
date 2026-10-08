"""Procedural lo-fi background track. Usage: python music.py SECONDS out.wav"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(3)
LEN = float(sys.argv[1])
BPM = 92
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int((LEN + 2) * SR)
L = np.zeros((N, 2))

def midi(m):
    return 440 * 2 ** ((m - 69) / 12)

def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "lowpass", fs=SR, output="sos"), x, axis=0)

def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "highpass", fs=SR, output="sos"), x, axis=0)

def add(x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    x = x[: N - i]
    th = (pan + 1) * np.pi / 4
    L[i:i + len(x), 0] += gain * np.cos(th) * x
    L[i:i + len(x), 1] += gain * np.sin(th) * x

def adsr(n, a, d, s, r):
    t = np.arange(n) / SR
    e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / d))
    rel = int(r * SR)
    if rel and rel < n:
        e[-rel:] *= np.linspace(1, 0, rel)
    return e

# Am7 - Fmaj7 - Cmaj7 - G6 (A minor, warm and loopable)
chords = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 55, 59, 64], [55, 59, 62, 64]]
roots = [45, 41, 48, 43]

def pad(notes, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0.08):
            f = midi(m) * 2 ** (det / 12)
            ph = rng.random()
            x += signal.sawtooth(2 * np.pi * (f * t + ph)) * 0.5
    x = lp(x, 1400)
    return x * adsr(n, 0.4, 1.0, 0.8, 0.5) / len(notes)

def pluck(m, dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(m)
    x = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t))
    return x * np.exp(-t / 0.16) * np.clip(t / 0.003, 0, 1)

def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(m)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return x * adsr(n, 0.01, 0.35, 0.5, 0.08)

def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 45 + 90 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)

def snare():
    n = int(0.25 * SR); t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 1200) * np.exp(-t / 0.07)
    return 0.7 * x + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)

def hat():
    n = int(0.06 * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000, 4) * np.exp(-t / 0.015)

bars = int(np.ceil(LEN / BAR)) + 1
arp_pattern = [0, 2, 1, 3, 2, 1, 3, 2]
for b in range(bars):
    t0 = b * BAR
    k = b % 4
    add(pad(chords[k], BAR + 0.6), t0, 0.32)
    full = b >= 2                          # drums and bass come in on bar 3
    for beat in range(4):
        tb = t0 + beat * BEAT
        if full:
            if beat in (0, 2):
                add(kick(), tb, 0.85)
            if beat in (1, 3):
                add(snare(), tb, 0.32, 0.05)
            add(bass(roots[k] - 12 + (7 if beat == 3 and b % 2 else 0), BEAT * 0.9), tb, 0.45)
        for h in range(2):
            swing = 0.035 if h else 0
            if full:
                add(hat(), tb + h * BEAT / 2 + swing, 0.13 if h else 0.18, 0.3)
    for j, idx in enumerate(arp_pattern):
        tn = t0 + j * BEAT / 2 + (0.03 if j % 2 else 0)
        m = chords[k][idx] + 12
        add(pluck(m), tn, 0.13 * (1.0 if b >= 1 else 0.6), -0.35 + 0.7 * (j % 2))

# simple stereo echo on everything, vinyl crackle, warm top end
echo = np.zeros_like(L)
dly = int(BEAT * 0.75 * SR)
echo[dly:, 0] = L[:-dly, 1] * 0.25
echo[dly:, 1] = L[:-dly, 0] * 0.25
L += lp(echo, 3000)
crackle = np.zeros(N)
pops = rng.random(N) < 6 / SR
crackle[pops] = rng.standard_normal(pops.sum())
crackle = hp(crackle, 2000) + 0.004 * lp(rng.standard_normal(N), 3000)
L += np.stack([crackle, crackle], 1) * 0.12
L = lp(L, 9000)

L = L[: int(LEN * SR)]
fade = int(2.0 * SR)
L[-fade:] *= np.linspace(1, 0, fade)[:, None]
L[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
L /= np.max(np.abs(L)) + 1e-9
L *= 0.89
wavfile.write(sys.argv[2], SR, (L * 32767).astype(np.int16))
print("wrote", sys.argv[2], len(L) / SR)
