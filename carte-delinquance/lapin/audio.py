"""Épisode « Les lapins d'Australie » : découpe la voix ElevenLabs, construit la timeline,
synthétise les bruitages et la musique (pizzicati enjoués).

Usage : VO_FILE=voix-lapin.mp3 python3 audio.py
Sorties : vo.wav, sfx.wav, music.wav, timeline.json
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(7)

# (id, texte, sous-titre (*mot* = jaune))

# (id, texte, sous-titre (*mot* = jaune))
SCRIPT = [
 ("r01", "", "En *1859*, un homme relâche *24 lapins* en Australie."),
 ("r02", "", "Aujourd'hui, ils sont environ *200 millions*."),
 ("r03", "", "Voici comment *24 lapins* ont envahi tout un *continent*."),
 ("r04", "", "*Thomas Austin* est un colon anglais, installé près de *Geelong*, dans le sud de l'Australie."),
 ("r05", "", "Il veut chasser comme en *Angleterre*… alors il fait venir des lapins d'*Europe*."),
 ("r06", "", "Le jour de *Noël 1859*, *24 lapins* arrivent sur sa propriété."),
 ("r07", "", "Six ans plus tard, il en a déjà tué *20 000* sur ses terres."),
 ("r08", "", "Car en Australie, le lapin n'a presque *aucun prédateur*… et une lapine peut avoir *plusieurs dizaines* de petits par an."),
 ("r09", "", "Ils avancent jusqu'à *100 kilomètres* par an : l'invasion de mammifère la *plus rapide* jamais enregistrée."),
 ("r10", "", "En *50 ans*, ils colonisent presque *tout le continent*."),
 ("r11", "", "Alors, l'Australie tente un plan fou : une *clôture géante*."),
 ("r12", "", "Entre *1901* et *1907*, trois clôtures sont construites, sur plus de *3 000 kilomètres*."),
 ("r13", "", "Mais c'est *trop tard* : les lapins sont déjà passés de l'autre côté."),
 ("r14", "", "En *1950*, on essaie une autre arme : un virus, la *myxomatose*."),
 ("r15", "", "En deux ans, la population passe de *600 millions*… à *100 millions*."),
 ("r16", "", "Mais les survivants deviennent *résistants*… et les lapins *reviennent*."),
 ("r17", "", "Aujourd'hui, ils occupent *70 %* du pays."),
 ("r18", "", "Tout ça… à cause de *24 lapins*."),
 ("r19", "", "Et toi, tu connais d'autres animaux qui ont envahi un pays ? Dis-le en commentaire !"),
]
GAPS = {"r01": 0.4, "r02": 0.35, "r03": 0.5, "r04": 0.7, "r05": 0.5, "r06": 0.8, "r07": 0.45, "r08": 0.5, "r09": 0.6,
        "r10": 0.35, "r11": 0.7, "r12": 0.4, "r13": 0.4, "r14": 0.8, "r15": 0.45, "r16": 0.45, "r17": 0.5, "r18": 0.7,
        "r19": 0.9}
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
TL = {"vo": [], "cue": {}, "ticker": [], "sfx": []}
t = 0.0
for k, _, cap in SCRIPT:
    t += GAPS[k]
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + dur[k], 3), "cap": cap})
    t += dur[k]
V = {v["id"]: v for v in TL["vo"]}
S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]; M = lambda k, f: S(k) + (Ed(k) - S(k))*f
TL["duration"] = round(Ed("r19") + 2.2, 3)
cue = TL["cue"]
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})

# repères visuels (partagés avec la page)
cue["intro"] = [0.0, M("r01", 0.45), M("r01", 0.95)]      # Angleterre zoomée → recul + demi-tour → plongée Australie
cue["flag"] = M("r01", 0.9)                               # l'Australie se remplit de son drapeau
cue["k24"] = M("r01", 0.6)
cue["k200"] = M("r02", 0.45)
cue["swarm"] = [S("r02"), Ed("r02") + 0.3]
cue["title"] = S("r03") + 0.2
cue["flagOut"] = [S("r03") + 0.4, S("r03") + 1.4]
cue["geelong"] = [S("r04") - 0.5, S("r04") + 0.9]
cue["austin"] = M("r04", 0.15)
cue["route"] = [S("r05") - 0.3, Ed("r05") + 0.4]         # bateau Angleterre → Australie (via le Cap)
cue["noel"] = [S("r06") - 0.4, S("r06") + 0.7]
cue["k24b"] = M("r06", 0.55)
cue["k20000"] = M("r07", 0.6)
cue["babies"] = M("r08", 0.55)
cue["spread"] = [S("r09") - 0.4, Ed("r10")]
cue["k100"] = M("r09", 0.3)
cue["wa"] = [S("r11") - 0.4, S("r11") + 0.8]
cue["fence"] = [S("r12") + 0.2, Ed("r12")]
cue["k3000"] = M("r12", 0.75)
cue["late"] = M("r13", 0.25)
cue["virus"] = [S("r14") - 0.5, S("r14") + 0.7]
cue["kmyxo"] = M("r14", 0.7)
cue["crash"] = [M("r15", 0.2), Ed("r15")]
cue["back"] = [S("r16") + 0.3, Ed("r16")]
cue["k70"] = M("r17", 0.55)
cue["home"] = [S("r18") - 0.5, S("r18") + 0.6]
cue["k24c"] = M("r18", 0.6)
cue["outro"] = S("r19") - 0.4

TL["ticker"] = [
    [S("r06"), S("r06") + 0.01, 1859, 1859, 1],
    [S("r07"), M("r07", 0.6), 1859, 1865, 1],
    [S("r09"), Ed("r10"), 1865, 1910, 5],
    [S("r12"), Ed("r12"), 1901, 1907, 1],
    [S("r14"), S("r14") + 0.01, 1950, 1950, 1],
    [S("r15"), Ed("r15"), 1950, 1952, 1],
    [S("r17"), S("r17") + 0.6, 1952, 2025, 10],
]
cue["tickerShow"] = [S("r06") - 0.3, Ed("r17") + 0.3]

# ------------------------------------------------------------------ bruitages (positions)
sfx("whoosh_long", 0.15, 0.9); sfx("whoosh_long", cue["intro"][1] - 0.2, 0.8)
sfx("impact", cue["flag"] - 0.05, 0.8)
for k in ("k24", "k200", "k24b", "k20000", "k100", "k3000", "kmyxo", "k70", "k24c"): sfx("type", cue[k], 0.8)
for i in range(16): sfx("pop", cue["swarm"][0] + 0.5 + i*0.11, 0.35)
sfx("whoosh", cue["flagOut"][0], 0.6)
sfx("whoosh_long", cue["geelong"][0], 0.9); sfx("pop", cue["austin"], 0.7)
sfx("whoosh_long", cue["route"][0], 0.8); sfx("horn", S("r05") + 0.6, 0.5)
sfx("whoosh_long", cue["noel"][0], 0.8); sfx("bell", S("r06") + 0.3, 0.45)
for i in range(12): sfx("pop", cue["k24b"] + 0.2 + i*0.07, 0.3)
for i in range(10): sfx("pop", cue["babies"] + i*0.09, 0.3)
sfx("whoosh_long", cue["spread"][0], 0.8); sfx("riser", Ed("r10"), 0.5)
sfx("whoosh_long", cue["wa"][0], 0.8)
for i in range(14): sfx("thud", cue["fence"][0] + i*(cue["fence"][1] - cue["fence"][0])/14, 0.45)
sfx("stamp", cue["late"], 0.9)
sfx("whoosh_long", cue["virus"][0], 0.8); sfx("down", cue["crash"][0] + 0.6, 0.7)
sfx("shimmer", cue["back"][0], 0.5)
for i in range(10): sfx("pop", cue["back"][0] + 0.3 + i*0.12, 0.3)
sfx("hit", cue["k70"], 0.7)
sfx("whoosh_long", cue["home"][0], 0.9); sfx("impact", cue["k24c"], 0.7)
sfx("pop", cue["outro"] + 0.5, 0.7)
last = -9
for t0, t1, y0, y1, step in TL["ticker"]:
    if y1 == y0: continue
    for y in range(int(y0) + step, int(y1) + 1, step):
        tt = t0 + (t1 - t0)*(y - y0)/(y1 - y0)
        if tt - last > 0.14: sfx("tick", tt, 0.45); last = tt

json.dump(TL, open("timeline.json", "w"), ensure_ascii=False, indent=1)
N = int(TL["duration"]*SR) + SR
tt = np.arange(N)/SR
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



def typew():                       # petit « tac » pour le texte qui s'écrit
    t = T(0.12); x = hp(rng.standard_normal(len(t)), 1800)*np.exp(-t*70) + np.sin(2*np.pi*900*t)*np.exp(-t*50)*0.4
    return norm(x, 0.45)
def thud():                        # piquet de clôture enfoncé
    t = T(0.4); x = np.sin(2*np.pi*np.cumsum(90 + 140*np.exp(-t*35))/SR)*np.exp(-t*12) + lp(rng.standard_normal(len(t)), 1200)*np.exp(-t*40)*0.4
    return norm(x, 0.6)
def horn(d=1.6):                   # corne de bateau douce
    t = T(d); x = sum(np.sin(2*np.pi*f*t)/k for k, f in enumerate([110, 220, 330, 440], 1))
    env = np.clip(t/0.15, 0, 1)*np.clip((d - t)/0.5, 0, 1)
    return norm(reverb(lp(x, 900)*env, 2.0, 0.35), 0.4)

BANK = {"whoosh": whoosh(), "whoosh_long": whoosh(1.4, 150, 3000), "impact": impact(), "hit": hit(), "stamp": stamp(),
        "pop": pop(), "tick": tick(), "bell": bell(), "shimmer": shimmer(), "riser": riser(), "down": down(),
        "type": typew(), "thud": thud(), "horn": horn()}
fx = np.zeros(N, np.float32)
for s in TL["sfx"]:
    x = BANK[s["name"]]*s["gain"]; i = int(s["t"]*SR)
    if s["name"] == "riser": i -= len(x)
    i = max(i, 0); fx[i:i+len(x)] += x[:N-i]
sf.write("sfx.wav", fx, SR)

# ------------------------------------------------------------------ musique : pizzicati enjoués, 112 BPM (ré majeur)
bpm = 112; beat = 60/bpm; bar = 4*beat
Dm = 73.42
PROG = [(0, [0, 4, 7]), (7, [0, 4, 7]), (9, [0, 3, 7]), (5, [0, 4, 7])]          # I V vi IV
PROG_T = [(9, [0, 3, 7]), (5, [0, 4, 7]), (9, [0, 3, 7]), (4, [0, 4, 8])]        # tension (myxomatose)
def section(x):
    if x < S("r04"):  return dict(pad=.7, pluck=.6, perc=.5, tens=0)
    if x < S("r09"):  return dict(pad=.7, pluck=1., perc=.8, tens=0)
    if x < S("r14"):  return dict(pad=.9, pluck=1., perc=1., tens=0)
    if x < S("r16"):  return dict(pad=.8, pluck=.3, perc=0, tens=1)
    return dict(pad=.9, pluck=1., perc=1., tens=0)
mus = np.zeros(N)
for b in range(int(TL["duration"]/bar) + 1):
    t0 = b*bar; sec = section(t0 + 0.01); i0 = int(t0*SR)
    root, iv = (PROG_T if sec["tens"] else PROG)[b % 4]
    n = int(bar*SR) + int(0.6*SR); tl = np.arange(n)/SR
    env = np.clip(tl/0.4, 0, 1)*np.clip((bar + 0.6 - tl)/0.6, 0, 1)
    f0 = Dm*2**(root/12)
    pad = sum(np.sin(2*np.pi*f0*2*2**(s/12)*tl) for s in iv)/3*env*0.10*sec["pad"]
    bass = np.sin(2*np.pi*f0*tl)*env*0.16*sec["pad"]
    seg = pad + bass
    if sec["pluck"]:
        pat = [0, 2, 1, 2, 0, 2, 1, 2]
        for k, ix in enumerate(pat):
            st = int(k*beat/2*SR); f = f0*4*2**(iv[ix]/12); tn = np.arange(int(0.5*SR))/SR
            pl = sum(np.sin(2*np.pi*f*h*tn)/h*np.exp(-tn*(9 + 5*h)) for h in range(1, 5))
            e = min(len(pl), n - st); seg[st:st+e] += pl[:e]*0.07*sec["pluck"]
    if sec["perc"]:
        for k in range(4):
            st = int(k*beat*SR); tn = np.arange(int(0.25*SR))/SR
            kick = np.sin(2*np.pi*np.cumsum(55 + 90*np.exp(-tn*30))/SR)*np.exp(-tn*14)*0.28 if k % 2 == 0 else \
                   hp(rng.standard_normal(len(tn)), 1500)*np.exp(-tn*30)*0.10                   # clap léger
            seg[st:st+len(kick)] += kick*sec["perc"]
    e = min(n, N - i0)
    if e > 0: mus[i0:i0+e] += seg[:e]
mus = reverb(mus, 1.6, 0.25)[:N]
mus *= np.clip(tt/1.2, 0, 1)*np.clip((TL["duration"] - tt)/2.0, 0, 1)
sf.write("music.wav", norm(mus, 0.6), SR)
print(json.dumps({"duration": TL["duration"]}))
