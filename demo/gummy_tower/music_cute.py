"""Bouncy, cute background loop (marimba, pizzicato bass, soft drums).
Usage: python music_cute.py SECONDS out.wav"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(11)
LEN = float(sys.argv[1])
BPM = 112
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int((LEN + 3) * SR)
out = np.zeros((N, 2))

def midi(m):
    return 440 * 2 ** ((m - 69) / 12)

def tt(sec):
    return np.arange(int(sec * SR)) / SR

def add(x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    x = x[: N - i]
    th = (pan + 1) * np.pi / 4
    out[i:i + len(x), 0] += g * np.cos(th) * x
    out[i:i + len(x), 1] += g * np.sin(th) * x

def marimba(m, dur=0.5):
    t = tt(dur); f = midi(m)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / 0.02)) \
        * np.exp(-t / 0.18) * np.clip(t / 0.002, 0, 1)

def glock(m, dur=0.8):
    t = tt(dur); f = midi(m)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.1)) \
        * np.exp(-t / 0.35) * np.clip(t / 0.001, 0, 1)

def pizz(m, dur=0.35):
    t = tt(dur); f = midi(m)
    x = signal.sawtooth(2 * np.pi * f * t) * np.exp(-t / 0.09)
    sos = signal.butter(2, 900, "lowpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def kick():
    t = tt(0.25)
    return np.sin(2 * np.pi * np.cumsum(50 + 80 * np.exp(-t / 0.025)) / SR) * np.exp(-t / 0.08)

def shaker():
    t = tt(0.07)
    sos = signal.butter(4, 6000, "highpass", fs=SR, output="sos")
    return signal.sosfilt(sos, rng.standard_normal(len(t))) * np.exp(-t / 0.02)

def snap():
    t = tt(0.12)
    sos = signal.butter(2, [1500, 5000], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, rng.standard_normal(len(t))) * np.exp(-t / 0.03)

# C - Am - F - G in C major, a playful melody over it
chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
bass = [36, 33, 41, 43]
melody = [  # (beat offset, midi) per 2-bar phrase, repeated with variation
    [(0, 72), (0.5, 76), (1, 79), (2, 76), (2.5, 74), (3, 72), (4, 69), (5, 72), (5.5, 74), (6, 76), (7, 74)],
    [(0, 77), (0.5, 76), (1, 74), (2, 72), (3, 74), (4, 79), (4.5, 77), (5, 76), (6, 74), (6.5, 72), (7, 71)],
]
bars = int(np.ceil(LEN / BAR)) + 1
for b in range(bars):
    t0 = b * BAR
    k = b % 4
    full = b >= 1
    for beat in range(4):
        tb = t0 + beat * BEAT
        add(pizz(bass[k] + (7 if beat == 2 else 0)), tb, 0.5)
        if full:
            if beat in (0, 2):
                add(kick(), tb, 0.6)
            if beat in (1, 3):
                add(snap(), tb, 0.22, 0.1)
            for h in range(2):
                add(shaker(), tb + h * BEAT / 2 + (0.02 if h else 0), 0.08 if h else 0.11, 0.35)
        # offbeat chord stabs
        for m in chords[k]:
            add(marimba(m + 12, 0.25), tb + BEAT / 2, 0.07, -0.2)
    if b % 2 == 0 and b >= 2:
        phrase = melody[(b // 2) % 2]
        for off, m in phrase:
            add(glock(m), t0 + off * BEAT, 0.16, 0.15)

dly = int(BEAT * 0.75 * SR)
echo = np.zeros_like(out)
echo[dly:, 0] = out[:-dly, 1] * 0.2
echo[dly:, 1] = out[:-dly, 0] * 0.2
out += echo
out = out[: int(LEN * SR)]
fade = int(min(2.0, LEN / 4) * SR)
out[-fade:] *= np.linspace(1, 0, fade)[:, None]
out /= np.max(np.abs(out)) + 1e-9
out *= 0.89
wavfile.write(sys.argv[2], SR, (out * 32767).astype(np.int16))
print("wrote", sys.argv[2], len(out) / SR)
