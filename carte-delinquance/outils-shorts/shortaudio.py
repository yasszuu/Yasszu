"""Bibliothèque audio commune pour les vidéos courtes : timeline, bruitages, musique."""
import json, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
SR = 44100
rng = np.random.default_rng(5)
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


def load_wav(p):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
def bank():
    B = {"whoosh": whoosh(), "impact": impact(), "hit": hit(), "stamp": stamp(), "pop": pop(), "tick": tick(),
         "bell": bell(), "shimmer": shimmer(), "riser": riser(), "down": down()}
    R = {k: load_wav(f"../moust2/assets/s_{k}.wav") for k in ("pop", "woosh", "tick", "impact")}
    B.update({"whoosh": R["woosh"], "pop": R["pop"]*0.9, "tick": R["tick"]*0.8, "impact": R["impact"]})
    return B
def build(gaps, tail, cues, cry, cry_len, cry_gain=0.9, extra_cry=(), music_sec=None, bpm=96, minor=True):
    """gaps: {id: silence avant}, cues(S, Ed, M, sfx) ajoute les bruitages, cry: fichier du cri (joué à t=0)."""
    script = json.load(open("script.json"))
    clips = {k: sf.read(f"vo/{k}.wav", dtype="float32")[0] for k, *_ in script}
    TL = {"vo": [], "sfx": [], "ticker": []}; t = 0.0
    for k, _, cap in script:
        t += gaps.get(k, 0.35); d = len(clips[k])/SR
        TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + d, 3), "cap": cap}); t += d
    V = {v["id"]: v for v in TL["vo"]}; S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]; M = lambda k, f: S(k) + (Ed(k) - S(k))*f
    TL["duration"] = round(t + tail, 3)
    def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})
    cues(S, Ed, M, sfx, TL)
    TL["sfx"].sort(key=lambda s: s["t"])
    json.dump(TL, open("timeline.json", "w"), ensure_ascii=False, indent=1)
    N = int(TL["duration"]*SR) + SR; tt = np.arange(N)/SR
    vo = np.zeros(N, np.float32)
    for v in TL["vo"]: x = clips[v["id"]]; i = int(v["start"]*SR); vo[i:i+len(x)] += x
    sf.write("vo.wav", vo, SR)
    B = bank(); fx = np.zeros(N, np.float32)
    for when, path, ln, g in [(0.0, cry, cry_len, cry_gain), *extra_cry]:
        c = load_wav(path)[:int(ln*SR)]; c = c*np.clip((ln - np.arange(len(c))/SR)/0.35, 0, 1); i = int(when*SR); fx[i:i+len(c)] += (c/np.abs(c).max()*g)[:N-i]
    for s in TL["sfx"]:
        if s["name"] not in B: B[s["name"]] = load_wav(s["name"])
        x = B[s["name"]]*s["gain"]; i = int(s["t"]*SR)
        if s["name"] == "riser": i -= len(x)
        i = max(i, 0); fx[i:i+len(x)] += x[:N-i]
    sf.write("sfx.wav", fx, SR)
    # musique : pad + arpège + percussions, progression mineure, intensité par section
    beat = 60/bpm; bar = 4*beat
    A, C, D, E_, F, G = 55.0, 65.41, 73.42, 82.41, 87.31, 98.0
    PROG = [(A, [0, 3, 7]), (F, [0, 4, 7]), (C, [0, 4, 7]), (G, [0, 4, 7])] if minor else [(C, [0, 4, 7]), (G, [0, 4, 7]), (A, [0, 3, 7]), (F, [0, 4, 7])]
    sec = music_sec or (lambda x: dict(pad=0, pluck=0, drum=0) if x < 1.2 else dict(pad=.9, pluck=.9, drum=1.))
    mus = np.zeros(N); saw = lambda f, t: 2*((f*t) % 1) - 1
    for b in range(int(TL["duration"]/bar) + 1):
        t0 = b*bar; s_ = sec(t0 + 0.01); root, iv = PROG[b % 4]
        i0 = int(t0*SR); n = int(bar*SR) + int(0.5*SR); tl = np.arange(n)/SR
        env = np.clip(tl/0.4, 0, 1)*np.clip((bar + 0.5 - tl)/0.5, 0, 1)
        pad = lp(sum(saw(root*4*2**(s/12)*(1 + dt), tl) for s in iv for dt in (-.004, .004))/6, 900)*env*0.22*s_["pad"]
        seg = pad + np.sin(2*np.pi*root*tl)*env*0.22*s_["pad"]
        if s_["pluck"]:
            notes = [iv[0], iv[1], iv[2], 12 + iv[0], iv[2], iv[1], 12 + iv[1], iv[2]]
            for k, s in enumerate(notes):
                st = int(k*beat/2*SR); f = root*8*2**(s/12); tn = np.arange(int(1.0*SR))/SR
                pl = sum(np.sin(2*np.pi*f*h*tn)/h*np.exp(-tn*(3 + 2.5*h)) for h in range(1, 6))
                e = min(len(pl), n - st); seg[st:st+e] += pl[:e]*0.07*s_["pluck"]
        if s_["drum"]:
            for k in range(4):
                st = int(k*beat*SR); tn = np.arange(int(0.5*SR))/SR
                kick = np.sin(2*np.pi*np.cumsum(50 + 90*np.exp(-tn*25))/SR)*np.exp(-tn*7)
                seg[st:st+len(kick)] += kick*(0.4 if k % 2 == 0 else 0.22)*s_["drum"]
            for k in range(8):
                st = int((k*beat/2 + beat/4)*SR); sh = hp(rng.standard_normal(int(0.04*SR)), 6000)*np.exp(-np.arange(int(0.04*SR))/SR*90)
                seg[st:st+len(sh)] += sh*0.06*s_["drum"]
            for k in (1, 3):
                st = int(k*beat*SR); tn = np.arange(int(0.25*SR))/SR
                cl = bp(rng.standard_normal(len(tn)), 900, 5000)*np.exp(-tn*22)
                seg[st:st+len(cl)] += cl*0.12*s_["drum"]
        e = min(n, N - i0)
        if e > 0: mus[i0:i0+e] += seg[:e]
    mus = reverb(mus, 2.2, 0.25)[:N]; mus *= np.clip(tt/1.0, 0, 1)*np.clip((TL["duration"] - tt)/1.2, 0, 1)
    sf.write("music.wav", norm(mus, 0.6), SR)
    return TL
