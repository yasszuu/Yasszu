"""Épisode « Le moustique tigre envahit la France » : découpe la voix ElevenLabs, construit la timeline,
place les VRAIS bruitages fournis (bzz du moustique + pack SFX) et synthétise la musique.

Usage : VO_FILE=assets/voix-moustique.mp3 python3 audio.py
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(9)

SCRIPT = [
 ("m01", "", "En *2004*, un minuscule moustique est repéré à *Menton*, sur la Côte d'Azur."),
 ("m02", "", "Vingt ans plus tard, il a envahi plus de *80 départements*."),
 ("m03", "", "Voici comment le *moustique tigre* a conquis la France."),
 ("m04", "", "Tout commence ici, dans les forêts d'*Asie du Sud-Est*."),
 ("m05", "", "Pendant des siècles, il ne quitte pas sa région."),
 ("m06", "", "Mais au *XXe siècle*, il trouve un moyen de transport parfait : les *vieux pneus*."),
 ("m07", "", "Il pond ses œufs dans l'*eau de pluie* qui stagne à l'intérieur… et les pneus voyagent par *bateau*, dans le monde entier."),
 ("m08", "", "En *1979*, il débarque en Europe, en *Albanie*."),
 ("m09", "", "En *1985*, il atteint les *États-Unis*, au Texas."),
 ("m10", "", "Puis, en *1990*, il arrive en *Italie*, à Gênes."),
 ("m11", "", "De là, il n'a plus qu'à longer la côte… jusqu'à *Menton*, en *2004*."),
 ("m12", "", "Et ses œufs ont un super-pouvoir : ils *résistent au froid* de l'hiver."),
 ("m13", "", "Alors il remonte la *vallée du Rhône*, caché dans les *voitures* et les *camions*."),
 ("m14", "", "Il conquiert le *Sud-Ouest*, puis le *centre* de la France."),
 ("m15", "", "Il atteint même la *région parisienne*."),
 ("m16", "", "Au 1er janvier *2025*, il est installé dans *81 départements* : plus de *4 sur 5* !"),
 ("m17", "", "Et le problème, ce ne sont pas seulement ses piqûres."),
 ("m18", "", "Il peut transmettre la *dengue* et le *chikungunya*."),
 ("m19", "", "En *2025*, la France bat un *record* : plus de *800 cas* de chikungunya contractés sur place, en métropole."),
 ("m20", "", "Le moustique tigre est désormais là pour *rester*."),
 ("m21", "", "Et toi, il est déjà arrivé dans ton département ? Dis-le en commentaire ! Et abonne-toi pour le prochain épisode."),
]
GAPS = {k: g for k, g in zip([s[0] for s in SCRIPT],
        [0.9, 0.4, 0.4, 0.8, 0.4, 0.5, 0.5, 0.6, 0.6, 0.6, 0.5, 0.6, 0.5, 0.4, 0.4, 0.6, 0.7, 0.4, 0.5, 0.6, 0.8])}
def load_external():
    """Voix ElevenLabs : soit VO_DIR (un mp3 par réplique, triés par nom),
    soit VO_FILE (un seul mp3, découpé sur les pauses longues entre répliques)."""
    import subprocess, glob
    def read(p):
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.float32).copy()
    def trim(x):
        nz = np.where(np.abs(x) > 0.01)[0]; return x[max(nz[0]-300, 0): nz[-1]+2000]
    ids = [k for k, *_ in SCRIPT]
    if os.environ.get("VO_DIR"):
        files = sorted(glob.glob(os.path.join(os.environ["VO_DIR"], "*.mp3")) + glob.glob(os.path.join(os.environ["VO_DIR"], "*.wav")))
        assert len(files) == len(ids), f"{len(files)} fichiers pour {len(ids)} répliques"
        return {k: trim(read(f)) for k, f in zip(ids, files)}
    x = read(os.environ["VO_FILE"])
    hop = int(0.02*SR); rms = np.sqrt(np.convolve(x**2, np.ones(hop)/hop, "same"))[::hop]
    silent = rms < max(0.004, np.percentile(rms, 95)*0.03)
    # pauses candidates, puis on garde les len(ids)-1 plus longues
    runs, i = [], 0
    while i < len(silent):
        if silent[i]:
            j = i
            while j < len(silent) and silent[j]: j += 1
            if i > 0 and j < len(silent): runs.append((j - i, i, j))
            i = j
        else: i += 1
    cuts = sorted(sorted(runs, reverse=True)[:len(ids) - 1], key=lambda r: r[1])
    assert len(cuts) == len(ids) - 1, f"seulement {len(cuts)+1} segments trouvés"
    print("pause la plus courte retenue :", round(min(c[0] for c in cuts)*0.02, 2), "s")
    bounds = [0] + [((a + b)//2)*hop for _, a, b in cuts] + [len(x)]
    out = {k: trim(x[bounds[n]:bounds[n+1]]) for n, k in enumerate(ids)}
    os.makedirs("vo", exist_ok=True)
    for k, v in out.items(): sf.write(f"vo/{k}.wav", v, SR)
    return out
clips = load_external()
dur = {k: len(v)/SR for k, v in clips.items()}

# ------------------------------------------------------------------ timeline
TL = {"vo": [], "cue": {}, "ticker": [], "sfx": [], "photos": []}
t = 0.0
for k, _, cap in SCRIPT:
    t += GAPS[k]
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + dur[k], 3), "cap": cap})
    t += dur[k]
V = {v["id"]: v for v in TL["vo"]}
S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]; M = lambda k, f: S(k) + (Ed(k) - S(k))*f
TL["duration"] = round(Ed("m21") + 2.0, 3)
cue = TL["cue"]
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})
def photo(img, a, b, z0=1.04, z1=1.14, px=0.0, py=0.0, gray=0.0): TL["photos"].append(dict(img=img, a=round(a,3), b=round(b,3), z0=z0, z1=z1, px=px, py=py, gray=gray))

# 3 photos seulement (rares, ~2 s), toujours amenées par un mouvement de carte
photo("p_pneus", M("m07", 0.22), M("m07", 0.22) + 2.0, 1.04, 1.14, 0.0, -0.02)
photo("p_menton", M("m11", 0.62), M("m11", 0.62) + 2.0, 1.04, 1.13, 0.0, 0.02)
photo("p_pique", S("m17") - 0.1, S("m17") + 2.0, 1.03, 1.16, 0.0, 0.0)

cue["title"] = 0.3
cue["intro"] = [M("m01", 0.55), Ed("m01") + 0.2]          # Menton (zoom) → recul sur la France
cue["flag"] = M("m01", 0.85)
cue["preview"] = [S("m02") + 0.2, M("m02", 0.85)]          # aperçu : les 81 départements s'allument
cue["k80"] = M("m02", 0.55)
cue["asia"] = [S("m04") - 0.6, S("m04") + 1.4]             # demi-tour du globe vers l'Asie du Sud-Est
cue["tire"] = M("m06", 0.6)
cue["lanes"] = [M("m07", 0.22) + 2.0, Ed("m07") + 0.3]     # routes maritimes depuis l'Asie
cue["alb"] = [S("m08") - 0.5, Ed("m08")]
cue["usa"] = [S("m09") - 0.5, Ed("m09")]
cue["ita"] = [S("m10") - 0.5, Ed("m10")]
cue["coast"] = [S("m11") - 0.3, M("m11", 0.62)]
cue["cold"] = [S("m12") - 0.4, Ed("m12")]
cue["rhone"] = [S("m13") - 0.4, Ed("m13") + 0.3]
cue["sw"] = [S("m14") - 0.3, Ed("m14") + 0.2]
cue["paris"] = [S("m15") - 0.3, Ed("m15") + 0.2]
cue["k81"] = M("m16", 0.62)
cue["virus"] = [S("m18") - 0.3, Ed("m18")]
cue["record"] = [S("m19") - 0.3, Ed("m19")]
cue["k800"] = M("m19", 0.45)
cue["stay"] = [S("m20") - 0.3, Ed("m20")]
cue["outro"] = S("m21") - 0.3

TL["ticker"] = [
    [S("m08"), S("m08") + 0.01, 1979, 1979, 1],
    [S("m09"), M("m09", 0.3), 1979, 1985, 1],
    [S("m10"), M("m10", 0.3), 1985, 1990, 1],
    [M("m11", 0.1), M("m11", 0.55), 1990, 2004, 1],
    [S("m13"), Ed("m13"), 2004, 2012, 1],
    [S("m14"), Ed("m14"), 2012, 2017, 1],
    [S("m15"), Ed("m15"), 2017, 2018, 1],
    [S("m16"), M("m16", 0.6), 2018, 2025, 1],
]

# ------------------------------------------------------------------ bruitages (vrais fichiers fournis)
sfx("bzz", 0.2, 0.7)
sfx("pop", cue["title"], 0.6)
sfx("woosh", cue["intro"][0], 0.6); sfx("impact", cue["flag"], 0.5)
sfx("pop", cue["k80"], 0.6)
sfx("woosh", cue["asia"][0], 0.8); sfx("bzz", S("m04") + 1.2, 0.6)
sfx("pop", cue["tire"], 0.6)
for p in TL["photos"]: sfx("woosh", p["a"] - 0.15, 0.7)
sfx("woosh", cue["lanes"][0], 0.5)
for k in ("alb", "usa", "ita"): sfx("woosh", cue[k][0], 0.6); sfx("impact", cue[k][0] + 2.0, 0.45)
sfx("woosh", cue["coast"][0], 0.5); sfx("impact", M("m11", 0.55), 0.55)
sfx("woosh", cue["cold"][0], 0.5); sfx("pop", M("m12", 0.45), 0.6)
sfx("woosh", cue["rhone"][0], 0.6); sfx("pop", M("m13", 0.6), 0.5)
sfx("woosh", cue["sw"][0], 0.5); sfx("woosh", cue["paris"][0], 0.55)
sfx("woosh", S("m16") - 0.3, 0.6); sfx("impact", cue["k81"], 0.65)
sfx("bzz", S("m17") + 0.1, 0.8)
sfx("woosh", cue["virus"][0], 0.5); sfx("impact", M("m18", 0.35), 0.5); sfx("impact", M("m18", 0.75), 0.5)
sfx("woosh", cue["record"][0], 0.5); sfx("impact", cue["k800"], 0.65)
sfx("bzz", S("m20") + 0.2, 0.6)
sfx("woosh", cue["outro"], 0.5); sfx("pop", cue["outro"] + 2.4, 0.6)
last = -9
for t0, t1, y0, y1, step in TL["ticker"]:
    if y1 == y0: continue
    for y in range(int(y0) + step, int(y1) + 1, step):
        tt = t0 + (t1 - t0)*(y - y0)/(y1 - y0)
        if tt - last > 0.15: sfx("tick", tt, 0.45); last = tt

json.dump(TL, open("timeline.json", "w"), ensure_ascii=False, indent=1)
N = int(TL["duration"]*SR) + SR
tt = np.arange(N)/SR
vo = np.zeros(N, np.float32)
for v in TL["vo"]:
    x = clips[v["id"]]; i = int(v["start"]*SR); vo[i:i+len(x)] += x
sf.write("vo.wav", vo, SR)

def load_wav(p):
    x, sr = sf.read(p, dtype="float32")
    if x.ndim > 1: x = x.mean(1)
    if sr != SR: x = resample_poly(x, SR, sr).astype(np.float32)
    return x/ (np.abs(x).max() + 1e-9)*0.8
BANK = {k: load_wav(f"assets/s_{k}.wav") for k in ("pop", "woosh", "tick", "impact", "bzz")}
fx = np.zeros(N, np.float32)
for s in TL["sfx"]:
    x = BANK[s["name"]]*s["gain"]; i = max(int(s["t"]*SR), 0); fx[i:i+len(x)] += x[:N-i]
sf.write("sfx.wav", fx, SR)
# ------------------------------------------------------------------ musique (tension, 96 BPM, la mineur)
lp = lambda x, f: sosfilt(butter(2, f, "lowpass", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, "highpass", fs=SR, output="sos"), x)
def reverb(x, decay=1.6, mix=0.25):
    n = int(decay*SR); ir = rng.standard_normal(n)*np.exp(-np.arange(n)/SR*6.9/decay); ir = lp(ir, 5000); ir /= np.sqrt((ir**2).sum())
    wet = fftconvolve(x, ir); out = np.zeros(len(wet)); out[:len(x)] += x*(1 - mix); out += wet*mix; return out
bpm = 96; beat = 60/bpm; bar = 4*beat; A = 55.0
PROG = [(0, [0, 3, 7]), (8, [0, 4, 7]), (3, [0, 4, 7]), (10, [0, 4, 7])]          # Am F C G
def section(x):
    if x < S("m04"): return dict(pad=.8, pluck=.4, perc=.4)
    if x < S("m13"): return dict(pad=.8, pluck=1., perc=.8)
    if x < S("m17"): return dict(pad=.9, pluck=.8, perc=1.)
    if x < S("m20"): return dict(pad=.9, pluck=.6, perc=1.)
    return dict(pad=1., pluck=.7, perc=.6)
mus = np.zeros(N)
for b in range(int(TL["duration"]/bar) + 1):
    t0 = b*bar; sec = section(t0 + 0.01); i0 = int(t0*SR); root, iv = PROG[b % 4]
    n = int(bar*SR) + int(0.6*SR); tl = np.arange(n)/SR
    env = np.clip(tl/0.4, 0, 1)*np.clip((bar + 0.6 - tl)/0.6, 0, 1); f0 = A*2**(root/12)
    seg = sum(np.sin(2*np.pi*f0*2*2**(s/12)*tl) for s in iv)/3*env*0.10*sec["pad"] + np.sin(2*np.pi*f0*tl)*env*0.16*sec["pad"]
    for k, ix in enumerate([0, 1, 2, 1, 0, 2, 1, 2]):
        st = int(k*beat/2*SR); f = f0*4*2**(iv[ix]/12); tn = np.arange(int(0.5*SR))/SR
        pl = sum(np.sin(2*np.pi*f*h*tn)/h*np.exp(-tn*(8 + 5*h)) for h in range(1, 5))
        e = min(len(pl), n - st); seg[st:st+e] += pl[:e]*0.06*sec["pluck"]
    for k in range(4):
        st = int(k*beat*SR); tn = np.arange(int(0.3*SR))/SR
        h = np.sin(2*np.pi*np.cumsum(60 + 80*np.exp(-tn*28))/SR)*np.exp(-tn*12)*0.26 if k % 2 == 0 else hp(rng.standard_normal(len(tn)), 3000)*np.exp(-tn*40)*0.07
        seg[st:st+len(h)] += h*sec["perc"]
    e = min(n, N - i0)
    if e > 0: mus[i0:i0+e] += seg[:e]
mus = reverb(mus)[:N]; mus *= np.clip(tt/1.5, 0, 1)*np.clip((TL["duration"] - tt)/2.0, 0, 1)
sf.write("music.wav", (mus/np.abs(mus).max()*0.6).astype(np.float32), SR)
print(json.dumps({"duration": TL["duration"]}))
