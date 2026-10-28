"""Épisode « Le moustique tigre » v2 (nouvelle DA) : timeline, bruitages, musique — voix ElevenLabs existante (vo/*.wav)."""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve
SR = 44100
rng = np.random.default_rng(5)
SCRIPT = [
[
"m01",
"",
"En *2004*, un minuscule moustique est repéré à *Menton*, sur la Côte d'Azur.",
0
],
[
"m02",
"",
"Vingt ans plus tard, il a envahi plus de *80 départements*.",
0
],
[
"m03",
"",
"Voici comment le *moustique tigre* a conquis la France.",
0
],
[
"m04",
"",
"Tout commence ici, dans les forêts d'*Asie du Sud-Est*.",
0
],
[
"m05",
"",
"Pendant des siècles, il ne quitte pas sa région.",
0
],
[
"m06",
"",
"Mais au *XXe siècle*, il trouve un moyen de transport parfait : les *vieux pneus*.",
0
],
[
"m07",
"",
"Il pond ses œufs dans l'*eau de pluie* qui stagne à l'intérieur… et les pneus voyagent par *bateau*, dans le monde entier.",
0
],
[
"m08",
"",
"En *1979*, il débarque en Europe, en *Albanie*.",
0
],
[
"m09",
"",
"En *1985*, il atteint les *États-Unis*, au Texas.",
0
],
[
"m10",
"",
"Puis, en *1990*, il arrive en *Italie*, à Gênes.",
0
],
[
"m11",
"",
"De là, il n'a plus qu'à longer la côte… jusqu'à *Menton*, en *2004*.",
0
],
[
"m12",
"",
"Et ses œufs ont un super-pouvoir : ils *résistent au froid* de l'hiver.",
0
],
[
"m13",
"",
"Alors il remonte la *vallée du Rhône*, caché dans les *voitures* et les *camions*.",
0
],
[
"m14",
"",
"Il conquiert le *Sud-Ouest*, puis le *centre* de la France.",
0
],
[
"m15",
"",
"Il atteint même la *région parisienne*.",
0
],
[
"m16",
"",
"Au 1er janvier *2025*, il est installé dans *81 départements* : plus de *4 sur 5* !",
0
],
[
"m17",
"",
"Et le problème, ce ne sont pas seulement ses piqûres.",
0
],
[
"m18",
"",
"Il peut transmettre la *dengue* et le *chikungunya*.",
0
],
[
"m19",
"",
"En *2025*, la France bat un *record* : plus de *800 cas* de chikungunya contractés sur place, en métropole.",
0
],
[
"m20",
"",
"Le moustique tigre est désormais là pour *rester*.",
0
],
[
"m21",
"",
"Et toi, il est déjà arrivé dans ton département ? Dis-le en commentaire ! Et abonne-toi pour le prochain épisode.",
0
]
]
GAP = {"m01": 1.6, "m02": 0.4, "m03": 0.4, "m04": 0.8, "m05": 0.4, "m06": 0.5, "m07": 0.5, "m08": 0.6, "m09": 0.6, "m10": 0.6, "m11": 0.5, "m12": 0.6, "m13": 0.5, "m14": 0.4, "m15": 0.4, "m16": 0.6, "m17": 0.7, "m18": 0.4, "m19": 0.5, "m20": 0.6, "m21": 0.8}
clips = {k: sf.read(f"vo/{k}.wav", dtype="float32")[0] for k, *_ in SCRIPT}
dur = {k: len(v)/SR for k, v in clips.items()}

# ------------------------------------------------------------------ timeline
TL = {"vo": [], "cue": {}, "ticker": [], "sfx": []}
t = 0.0
for k, _, cap, gap in SCRIPT:
    t += GAP[k]
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + dur[k], 3), "cap": cap})
    t += dur[k]
V = {v["id"]: v for v in TL["vo"]}
S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]
TL["duration"] = round(Ed("m21") + 1.6, 3)
M = lambda k, f: S(k) + (Ed(k) - S(k))*f
cue = TL["cue"]
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})

TL["ticker"] = [
    [S("m08"), S("m08") + 0.01, 1979, 1979, 1],
    [S("m09"), S("m09") + 0.6, 1979, 1985, 1],
    [S("m10"), S("m10") + 0.6, 1985, 1990, 1],
    [S("m11"), M("m11", 0.85), 1990, 2004, 1],
    [S("m13"), Ed("m13"), 2004, 2012, 1],
    [S("m14"), Ed("m14"), 2012, 2017, 1],
    [S("m15"), Ed("m15"), 2017, 2019, 1],
    [S("m16"), M("m16", 0.45), 2019, 2025, 1],
]
sfx("pop", 0.3, 0.7); sfx("whoosh", 1.2, 0.8)
sfx("impact", M("m01", 0.12), 0.8); sfx("whoosh", M("m01", 0.5), 0.8); sfx("pop", M("m01", 0.7), 0.9)
sfx("whoosh", S("m02") - 0.25, 0.9); sfx("riser", M("m02", 0.75), 0.6); sfx("impact", M("m02", 0.75), 1.0)
sfx("whoosh", S("m03") - 0.1, 0.8); sfx("impact", M("m03", 0.6), 0.9)
sfx("whoosh", S("m04") - 0.3, 0.9); sfx("pop", M("m04", 0.75), 0.8)
sfx("shimmer", S("m05") + 0.3, 0.4)
sfx("whoosh", S("m06") - 0.2, 0.7); sfx("hit", M("m06", 0.3), 0.7); sfx("pop", M("m06", 0.72), 0.9)
sfx("whoosh", M("m07", 0.45), 0.8)
for i in range(8): sfx("pop", M("m07", 0.5) + i*0.12, 0.4)
sfx("whoosh", S("m08") - 0.3, 0.8); sfx("impact", M("m08", 0.82), 0.9)
sfx("whoosh", S("m09") - 0.3, 0.8); sfx("impact", M("m09", 0.82), 0.9)
sfx("whoosh", S("m10") - 0.3, 0.8); sfx("impact", M("m10", 0.82), 0.9)
sfx("whoosh", S("m11") - 0.2, 0.8); sfx("pop", M("m11", 0.82), 0.9)
sfx("whoosh", S("m12") - 0.2, 0.7); sfx("pop", M("m12", 0.45), 0.8); sfx("impact", M("m12", 0.7), 0.7)
sfx("whoosh", S("m13") - 0.3, 0.8)
sfx("whoosh", S("m14") - 0.2, 0.8); sfx("hit", M("m14", 0.6), 0.6)
sfx("whoosh", S("m15") - 0.2, 0.8); sfx("hit", M("m15", 0.6), 0.7)
sfx("whoosh", S("m16") - 0.3, 0.8); sfx("riser", M("m16", 0.6), 0.6); sfx("impact", M("m16", 0.6), 1.0); sfx("hit", M("m16", 0.88), 0.7)
sfx("whoosh", S("m17") - 0.2, 0.7); sfx("pop", S("m17") + 0.05, 0.8)
sfx("hit", M("m18", 0.4), 0.8); sfx("hit", M("m18", 0.72), 0.8)
sfx("whoosh", S("m19") - 0.3, 0.8)
for i in range(14): sfx("pop", M("m19", 0.35) + i*0.15, 0.35)
sfx("riser", M("m19", 0.62), 0.6); sfx("impact", M("m19", 0.62), 1.0)
sfx("whoosh", S("m20") - 0.2, 0.8); sfx("impact", M("m20", 0.7), 0.8)
sfx("pop", S("m21") + 0.2, 0.7)
last = -9
for t0, t1, y0, y1, step in TL["ticker"]:
    if y1 == y0: continue
    for y in range(int(y0) + step, int(y1) + 1, step):
        tt = t0 + (t1 - t0) * (y - y0) / (y1 - y0)
        if tt - last > 0.14: sfx("tick", tt, 0.5); last = tt
TL["sfx"].sort(key=lambda s: s["t"])
json.dump(TL, open("timeline.json", "w"), ensure_ascii=False, indent=1)
N = int(TL["duration"] * SR) + SR
tt = np.arange(N) / SR

# ------------------------------------------------------------------ voix
vo = np.zeros(N, np.float32)
for v in TL["vo"]:
    x = clips[v["id"]]; i = int(v["start"]*SR); vo[i:i+len(x)] += x
sf.write("vo.wav", vo, SR)

# ------------------------------------------------------------------ synthèse des bruitages
T = lambda d: np.arange(int(d*SR)) / SR
lp = lambda x, f: sosfilt(butter(2, f, "lowpass", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, "highpass", fs=SR, output="sos"), x)
bp = lambda x, a, b: sosfilt(butter(2, [a, b], "bandpass", fs=SR, output="sos"), x)
def reverb(x, decay=2.2, mix=0.35):
    n = int(decay*SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n)/SR * 6.9/decay)
    ir = lp(ir, 5000); ir /= np.sqrt((ir**2).sum())
    wet = fftconvolve(x, ir)
    out = np.zeros(len(wet)); out[:len(x)] += x*(1-mix); out += wet*mix
    return out
def bandsweep(noise, f0, f1, q=1.2):
    out = np.zeros_like(noise); n = len(noise); blk = 512
    for i in range(0, n, blk):
        f = f0 * (f1/f0) ** (i/n)
        out[i:i+blk] = bp(noise[i:i+blk], max(f/q, 30), min(f*q, SR/2-100))
    return out
def norm(x, peak=0.8): return (x / (np.abs(x).max() + 1e-9) * peak).astype(np.float32)

def howl(d=3.6, base=1.0):
    t = T(d); n = len(t)
    f = np.interp(t, [0, .35, .9, 2.6, d], [360, 600, 640, 615, 430]) * base
    vib = (np.sin(2*np.pi*4.6*t) * np.clip((t-0.6)/0.8, 0, 1) * 9) + np.sin(2*np.pi*0.7*t)*4
    ph = 2*np.pi*np.cumsum(f + vib)/SR
    x = np.sin(ph) + .32*np.sin(2*ph+.4) + .1*np.sin(3*ph+1.1) + .04*np.sin(4*ph)
    breath = bp(rng.standard_normal(n), 500*base, 2600*base) * 0.10
    env = np.clip(t/0.3, 0, 1)**1.5 * np.clip((d - t)/0.9, 0, 1) * (1 + 0.15*np.sin(2*np.pi*0.5*t))
    y = lp((x + breath) * env, 3500)
    return norm(reverb(y, 2.8, 0.42), 0.7)
def howl_pack():   # deux loups qui se répondent
    a = howl(3.6, 1.0); b = howl(3.2, 1.13)
    out = np.zeros(len(a) + int(0.9*SR)); out[:len(a)] += a; out[int(0.9*SR):int(0.9*SR)+len(b)] += 0.7*b
    return norm(out, 0.75)
def whoosh(d=0.9, f0=300, f1=3500):
    n = int(d*SR); x = bandsweep(rng.standard_normal(n), f0, f1)
    e = np.sin(np.pi*np.linspace(0, 1, n)**0.7)**2
    return norm(x*e, 0.6)
def impact():
    t = T(1.8); f = 36 + 90*np.exp(-t*14)
    sub = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*2.4)
    click = lp(rng.standard_normal(len(t)) * np.exp(-t*60), 2500) * 0.5
    return norm(reverb(0.9*sub + click, 1.5, 0.2), 0.95)
def hit():
    t = T(0.6); f = 60 + 160*np.exp(-t*30)
    body = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*7)
    sn = bp(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t*25)
    return norm(0.8*body + 0.35*sn, 0.7)
def stamp():
    t = T(0.9); thud = np.sin(2*np.pi*np.cumsum(70 + 120*np.exp(-t*40))/SR) * np.exp(-t*9)
    slap = bp(rng.standard_normal(len(t)), 300, 4000) * np.exp(-t*35)
    return norm(reverb(thud + 0.6*slap, 1.0, 0.25), 0.95)
def pop():
    t = T(0.18); f = 700 + 900*(1-np.exp(-t*40))
    return (np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*28) * 0.5).astype(np.float32)
def tick():
    t = T(0.05); return (np.sin(2*np.pi*2600*t) * np.exp(-t*110) * 0.35).astype(np.float32)
def step():
    t = T(0.25); x = lp(rng.standard_normal(len(t)), 900) * np.exp(-t*30) + np.sin(2*np.pi*80*t)*np.exp(-t*25)*0.6
    return norm(x, 0.5)
def bell():
    t = T(2.5); x = sum(a*np.sin(2*np.pi*880*m*t)*np.exp(-t*dd) for m, a, dd in
                        [(1, .5, 1.6), (2.76, .25, 2.5), (5.4, .12, 4), (8.9, .06, 6)])
    return norm(x*np.clip(t/0.002, 0, 1), 0.5)
def shimmer():
    t = T(2.2); x = sum(np.sin(2*np.pi*f*t)*np.exp(-t*1.8)*np.clip((t-o)/0.02, 0, 1)
                        for f, o in [(1320, 0), (1760, .08), (2217, .16), (2637, .24)])
    return norm(reverb(x, 2.0, .5), 0.4)
def riser(d=1.8):
    n = int(d*SR); t = np.linspace(0, 1, n)
    x = norm(bandsweep(rng.standard_normal(n), 400, 6000, 1.5) * t**2, 0.5)
    tone = np.sin(2*np.pi*np.cumsum(200 + 600*t**2)/SR) * t**2 * 0.15
    y = x + tone; y[-int(0.02*SR):] *= np.linspace(1, 0, int(0.02*SR)); return y.astype(np.float32)
def down():
    t = T(1.2); f = 900*np.exp(-t*2.2) + 120
    return norm(reverb(np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*2.5), 1.2, .3), 0.45)
def wind(d=7.0):
    n = int(d*SR); t = np.arange(n)/SR
    x = rng.standard_normal(n); out = np.zeros(n); blk = 1024
    for i in range(0, n, blk):
        f = 500 + 350*np.sin(2*np.pi*0.23*t[i]) + 150*np.sin(2*np.pi*0.61*t[i])
        out[i:i+blk] = bp(x[i:i+blk], f*0.7, f*1.4)
    e = np.clip(t/1.5, 0, 1) * np.clip((d-t)/2, 0, 1)
    return norm(out*e, 0.35)

BANK = {"whoosh": whoosh(), "whoosh_long": whoosh(1.6, 150, 2500),
        "impact": impact(), "hit": hit(), "stamp": stamp(), "pop": pop(), "tick": tick(), "step": step(),
        "bell": bell(), "shimmer": shimmer(), "riser": riser(), "down": down(), "wind": wind()}
import subprocess
def load_wav(p):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
REAL = {k: load_wav(f"assets/s_{k}.wav") for k in ("pop", "woosh", "tick", "impact", "bzz")}
BANK.update({"whoosh": REAL["woosh"], "whoosh_long": REAL["woosh"], "pop": REAL["pop"]*0.9, "tick": REAL["tick"]*0.8, "impact": REAL["impact"]})
fx = np.zeros(N, np.float32)
cri = REAL["bzz"][:int(2.2*SR)]; cri = cri*np.clip((2.2 - np.arange(len(cri))/SR)/0.4, 0, 1); fx[:len(cri)] += cri/np.abs(cri).max()*0.9
for s in TL["sfx"]:
    x = BANK[s["name"]] * s["gain"]; i = int(s["t"]*SR)
    if s["name"] == "riser": i -= len(x)
    i = max(i, 0); fx[i:i+len(x)] += x[:N-i]
sf.write("sfx.wav", fx, SR)

# ------------------------------------------------------------------ musique (84 BPM, la mineur)
bpm = 84; beat = 60/bpm; bar = 4*beat
A, C, D, E, F, G = 55.0, 65.41, 73.42, 82.41, 87.31, 98.0
PROG = [(A, [0, 3, 7]), (F, [0, 4, 7]), (C, [0, 4, 7]), (G, [0, 4, 7])]          # Am F C G
PROG_T = [(A, [0, 3, 7]), (F, [0, 4, 7]), (D, [0, 3, 7]), (E, [0, 4, 7])]        # Am F Dm E (tension)
def section(x):
    if x < 1.3: return dict(pad=0, pluck=0, drum=0, tens=0)
    if x < S("m04"): return dict(pad=.8, pluck=.8, drum=1., tens=0)
    if x < S("m08"): return dict(pad=.8, pluck=.7, drum=.4, tens=0)
    if x < S("m12"): return dict(pad=1., pluck=1., drum=1., tens=0)
    if x < S("m17"): return dict(pad=.7, pluck=0, drum=.35, tens=1)
    return dict(pad=1., pluck=.9, drum=.8, tens=0)
def _old(x):   # intensité par section, 0..1 par couche
    if x < 1.4:      return dict(pad=0, pluck=0, drum=0, tens=0)
    if x < S("a1"):  return dict(pad=.8, pluck=.6, drum=1., tens=0)
    if x < S("b1"):  return dict(pad=.6, pluck=0, drum=0, tens=1)
    if x < S("c1"):  return dict(pad=.8, pluck=.7, drum=0, tens=0)
    if x < S("d1"):  return dict(pad=.9, pluck=.5, drum=.4, tens=0)
    if x < S("f1"):  return dict(pad=1., pluck=1., drum=1., tens=0)
    if x < S("g1"):  return dict(pad=.7, pluck=0, drum=.35, tens=1)
    return dict(pad=1., pluck=.8, drum=.5, tens=0)
mus = np.zeros(N)
nbars = int(TL["duration"]/bar) + 1
def saw(f, t): return 2*((f*t) % 1) - 1
for b in range(nbars):
    t0 = b*bar; sec = section(t0 + 0.01)
    root, iv = (PROG_T if sec["tens"] else PROG)[b % 4]
    i0 = int(t0*SR); n = int(bar*SR) + int(0.5*SR); tl = np.arange(n)/SR
    env = np.clip(tl/0.6, 0, 1) * np.clip((bar + 0.5 - tl)/0.5, 0, 1)
    pad = sum(saw(root*4*2**(s/12)*(1+dt), tl) for s in iv for dt in (-.004, .004)) / 6
    pad = lp(pad, 900) * env * 0.22 * sec["pad"]
    sub = np.sin(2*np.pi*root*tl) * env * 0.22 * sec["pad"]
    seg = pad + sub
    # arpège pincé (synthèse additive)
    if sec["pluck"]:
        notes = [iv[0], iv[1], iv[2], 12 + iv[0], iv[2], iv[1], 12 + iv[1], iv[2]]
        for k, s in enumerate(notes):
            st = int(k*beat/2*SR); f = root*8*2**(s/12); tn = np.arange(int(1.2*SR))/SR
            pl = sum(np.sin(2*np.pi*f*h*tn)/h * np.exp(-tn*(3 + 2.5*h)) for h in range(1, 6))
            e = min(len(pl), n - st); seg[st:st+e] += pl[:e] * 0.07 * sec["pluck"]
    if sec["drum"]:
        for k in (0, 2):
            st = int(k*beat*SR); tn = np.arange(int(0.6*SR))/SR
            tom = np.sin(2*np.pi*np.cumsum(55 + 70*np.exp(-tn*20))/SR) * np.exp(-tn*6)
            seg[st:st+len(tom)] += tom * 0.35 * sec["drum"]
        for k in range(8):
            st = int((k*beat/2 + beat/4)*SR); sh = hp(rng.standard_normal(int(0.04*SR)), 6000) * np.exp(-np.arange(int(0.04*SR))/SR*90)
            seg[st:st+len(sh)] += sh * 0.05 * sec["drum"]
    e = min(n, N - i0)
    if e > 0: mus[i0:i0+e] += seg[:e]
mus = reverb(mus, 2.5, 0.3)[:N]
mus *= np.clip(tt/2.0, 0, 1) * np.clip((TL["duration"] - tt)/2.0, 0, 1)
sf.write("music.wav", norm(mus, 0.6), SR)
print(json.dumps({"duration": TL["duration"], "vo_end": Ed("m21")}))
