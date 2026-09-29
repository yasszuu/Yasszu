import math, random, wave, struct, array
SR = 44100; DUR = 20.0; N = int(SR * DUR)
L = array.array('f', [0.0]) * N; R = array.array('f', [0.0]) * N
rnd = random.Random(7)
def add(i, v, pan=0.0):
    if 0 <= i < N:
        L[i] += v * (1 - max(0, pan)); R[i] += v * (1 + min(0, pan))
def tone(t0, dur, f0, f1, amp, decay, pan=0.0, attack=0.005):
    ph = 0.0; n = int(dur * SR); s0 = int(t0 * SR)
    for k in range(n):
        x = k / n; f = f0 * (f1 / f0) ** x; ph += 2 * math.pi * f / SR
        env = min(1, k / (attack * SR + 1)) * math.exp(-decay * k / SR)
        add(s0 + k, math.sin(ph) * amp * env, pan)
def noise(t0, dur, amp, decay, lp0=0.9, lp1=0.9, rise=False, pan=0.0, hp=False):
    n = int(dur * SR); s0 = int(t0 * SR); y = 0.0; prev = 0.0
    for k in range(n):
        x = k / n; a = lp0 + (lp1 - lp0) * x
        w = rnd.uniform(-1, 1); y += a * (w - y)
        v = (y - prev) if hp else y; prev = y
        env = (x ** 2.2) if rise else math.exp(-decay * k / SR) * min(1, k / 80)
        add(s0 + k, v * amp * env, pan)
def boom(t0, amp=0.9, big=False):
    tone(t0, 1.6 if big else 1.0, 130, 38, amp, 3.0 if big else 4.5)
    noise(t0, 0.25, amp * 0.5, 18, 0.5, 0.2)
    if big: noise(t0, 2.5, amp * 0.7, 1.6, 0.08, 0.02)
# nappe grave
for k in range(N):
    t = k / SR
    env = min(1, t / 1.5) * (1 - max(0, (t - 18.8) / 1.2)) if t < 20 else 0
    v = (math.sin(2 * math.pi * 41.2 * t) * 0.22 + math.sin(2 * math.pi * 61.7 * t + math.sin(t * 0.7)) * 0.10
         + math.sin(2 * math.pi * 82.4 * t) * 0.05 * (0.5 + 0.5 * math.sin(t * 1.3)))
    if 17.2 < t: v *= 0.5
    L[k] += v * env; R[k] += v * env
# battement de cœur (plan 1)
for t0 in [0.4, 1.15, 1.9, 2.65]:
    tone(t0, 0.35, 90, 45, 0.55, 12); tone(t0 + 0.18, 0.3, 80, 42, 0.35, 14)
# laser
tone(1.3, 0.6, 2400, 300, 0.12, 5, pan=0.3); noise(1.3, 2.2, 0.10, 1.2, 0.95, 0.9, hp=True, pan=0.3)
# pulsations 100 bpm du plan 3 au plan 5
t = 7.6
while t < 17.1:
    if not (9.3 < t < 9.8): tone(t, 0.3, 110, 45, 0.5, 11)
    noise(t + 0.3, 0.06, 0.08, 60, 0.9, 0.9, hp=True, pan=0.2 * math.sin(t))
    t += 0.6
# whooshes avant les coupes
for c in [3.6, 7.6, 11.6, 15.0, 17.2]:
    noise(c - 0.7, 0.7, 0.35, 0, 0.02, 0.6, rise=True, pan=-0.3)
    boom(c, 0.55)
# explosion planète
tone(4.4, 1.15, 50, 70, 0.25, 0.2)
boom(5.55, 1.0, big=True)
# choc VS : boom + résonance métallique + verre
boom(9.55, 1.0, big=True)
for f, p in [(812, -0.4), (1270, 0.3), (1833, -0.1), (2610, 0.5)]:
    tone(9.55, 2.2, f, f * 0.995, 0.06, 2.2, pan=p)
for i in range(40):
    tt = 9.55 + rnd.random() * 0.9; tone(tt, 0.08, 3000 + rnd.random() * 5000, 2500, 0.05, 40, pan=rnd.uniform(-.8, .8))
# gélules qui tombent : petits clics
tt = 11.7
while tt < 14.9:
    tone(tt, 0.05, 1800 + rnd.random() * 2600, 1500, 0.07, 70, pan=rnd.uniform(-.9, .9)); tt += 0.05 + rnd.random() * 0.1
# compteur
for i in range(25):
    tt = 12.0 + 1.6 * (1 - (1 - i / 24) ** 3)
    tone(tt, 0.04, 2200, 2200, 0.05, 90)
# barres de stats
for i, d in enumerate([0.1, 0.18, 0.28, 0.36, 0.46, 0.54]):
    tone(15.0 + 0.1 + d + 0.1, 0.35, 300 + i * 60, 900 + i * 120, 0.08, 6, pan=-0.6 + i * 0.24)
boom(16.3, 0.6)
# logo : impact + accord scintillant
boom(17.75, 0.9, big=True)
for f in [130.8, 196.0, 261.6, 329.6, 392.0, 587.3]:
    for det in (-0.6, 0.6):
        tone(17.75, 2.25, f + det, f + det, 0.045, 0.9, pan=det, attack=0.4)
for i in range(30):
    tt = 17.9 + rnd.random() * 1.8; tone(tt, 0.4, 3500 + rnd.random() * 3000, 3200, 0.02, 8, pan=rnd.uniform(-1, 1))
# finalisation
peak = max(max(abs(x) for x in L), max(abs(x) for x in R))
g = 1.4 / peak
out = array.array('h')
for k in range(N):
    fade = min(1, (DUR - k / SR) / 0.5)
    for s in (L[k], R[k]):
        out.append(int(math.tanh(s * g) * 0.89 * fade * 32767))
w = wave.open('audio.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes()); w.close()
print('ok')
