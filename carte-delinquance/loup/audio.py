"""Épisode « Le retour du loup en France » : voix off, timeline, bruitages, musique.

Sorties : vo.wav, sfx.wav, music.wav, timeline.json
La timeline (timeline.json) est partagée avec la page de rendu : tous les
mouvements de caméra et apparitions sont calés sur les répliques de la voix.
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(5)

# ------------------------------------------------------------------ script
# (id, texte prononcé, sous-titre (*mot* = jaune), silence avant la réplique)
SCRIPT = [
 ("h1", "En novembre 1992, un couple de loups est aperçu dans les Alpes françaises.",
        "En *novembre 1992*, un couple de loups est aperçu dans les *Alpes françaises*.", 1.5),
 ("h2", "Trente ans plus tard, ils sont plus de mille.", "Trente ans plus tard, ils sont *plus de 1 000*.", 0.25),
 ("h3", "Voici leur incroyable retour.", "Voici leur *incroyable retour*.", 0.3),

 ("a1", "Au dix-huitième siècle, le loup vivait sur presque tout le territoire.",
        "Au *XVIIIe siècle*, le loup vivait sur presque *tout le territoire*.", 0.7),
 ("a2", "Mais traqué, piégé, empoisonné, il recule partout...", "Mais *traqué*, *piégé*, *empoisonné*… il recule partout.", 0.2),
 ("a3", "et disparaît de France dans les années mille neuf cent trente.", "Et il *disparaît* de France dans les *années 1930*.", 0.1),

 ("b1", "Il ne survit plus qu'en Italie : à peine une centaine de loups, cachés dans les Apennins.",
        "Il ne survit plus qu'en *Italie* : à peine *une centaine*, cachés dans les *Apennins*.", 0.9),
 ("b2", "Protégés à partir de mille neuf cent soixante et onze, ils se multiplient...",
        "*Protégés* à partir de *1971*, ils se multiplient...", 0.3),
 ("b3", "et remontent vers le nord, de montagne en montagne.", "et remontent vers le *nord*, de montagne en montagne.", 0.1),

 ("c1", "Jusqu'au cinq novembre mille neuf cent quatre-vingt-douze.", "Jusqu'au *5 novembre 1992*.", 0.8),
 ("c2", "Ils sont repérés dans le parc national du Mercantour.", "Ils sont repérés dans le parc du *Mercantour*.", 0.9),
 ("c3", "Personne ne les a réintroduits : ils sont revenus seuls.", "Personne ne les a réintroduits : ils sont *revenus seuls*.", 0.35),

 ("d1", "Ensuite, tout s'accélère.", "Ensuite, *tout s'accélère*.", 0.7),
 ("d2", "Le Massif central en quatre-vingt-dix-sept.", "Le *Massif central* en *1997*.", 0.25),
 ("d3", "Les Pyrénées en quatre-vingt-dix-neuf.", "Les *Pyrénées* en *1999*.", 0.25),
 ("d4", "Puis le Jura, en deux mille trois.", "Puis le *Jura* en *2003*.", 0.25),
 ("d5", "Et enfin, les Vosges.", "Et enfin, les *Vosges*.", 0.25),
 ("d6", "Aujourd'hui, il est signalé jusqu'en Bretagne et en Normandie.",
        "Aujourd'hui, il est signalé jusqu'en *Bretagne*… et en *Normandie* !", 0.5),

 ("e1", "En deux mille vingt-cinq, l'Office français de la biodiversité estime leur nombre à environ mille quatre-vingts loups.",
        "En 2025, l'OFB estime leur nombre à environ *1 080 loups*.", 0.6),

 ("f1", "Mais ce retour a un prix : environ douze mille animaux d'élevage tués en une seule année.",
        "Mais ce retour a un prix : environ *12 000 animaux d'élevage* tués en un an.", 0.8),
 ("f2", "Et en deux mille vingt-cinq, l'Europe a abaissé son niveau de protection.",
        "Et en 2025, l'Europe a *abaissé sa protection*.", 0.4),

 ("g1", "Alors, est-ce que le loup a sa place en France ?", "Alors, le loup a-t-il *sa place en France* ?", 1.6),
 ("g2", "Dis-le en commentaire. Et abonne-toi pour le prochain épisode : le lion de l'Atlas.",
        "Dis-le en commentaire ! Prochain épisode : *le lion de l'Atlas*.", 0.4),
]

def tts_all():
    import sherpa_onnx
    d = "vits-piper-fr_FR-tom-medium"
    tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=f"{d}/fr_FR-tom-medium.onnx", tokens=f"{d}/tokens.txt",
                                                   data_dir=f"{d}/espeak-ng-data", length_scale=0.9, noise_scale=0.6, noise_scale_w=0.7),
        num_threads=4)))
    os.makedirs("vo", exist_ok=True); out = {}
    for k, say, _, _ in SCRIPT:
        a = tts.generate(say, sid=0, speed=1.0)
        x = np.asarray(a.samples, dtype=np.float32)
        if a.sample_rate != SR: x = resample_poly(x, SR, a.sample_rate).astype(np.float32)
        nz = np.where(np.abs(x) > 0.01)[0]; x = x[max(nz[0]-200, 0): nz[-1]+1000]
        sf.write(f"vo/{k}.wav", x, SR); out[k] = x
    return out

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

clips = load_external() if (os.environ.get("VO_FILE") or os.environ.get("VO_DIR")) else tts_all()
dur = {k: len(v)/SR for k, v in clips.items()}

# ------------------------------------------------------------------ timeline
TL = {"vo": [], "cue": {}, "ticker": [], "sfx": []}
t = 0.0
for k, _, cap, gap in SCRIPT:
    t += gap
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + dur[k], 3), "cap": cap})
    t += dur[k]
V = {v["id"]: v for v in TL["vo"]}
S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]
TL["duration"] = round(Ed("g2") + 2.2, 3)
cue = TL["cue"]
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})

# repères visuels (partagés avec la page)
cue["zoomFR"] = [S("h3") - 0.1, S("a1") + 0.2]
cue["fillAll"] = [S("a1") + 0.3, S("a1") + 1.6]
cue["fade"] = [S("a2"), Ed("a3") - 0.4]
cue["stamp"] = Ed("a3") - 0.35
cue["toItaly"] = [S("b1") - 0.7, S("b1") + 0.6]
cue["apennins"] = [S("b1") + 0.4, S("b1") + 2.0]
cue["protect"] = S("b2") + 0.2
cue["path"] = [S("b3") - 0.3, S("c1") + 0.2]          # tracé linéaire Abruzzes → Mercantour
cue["arrive"] = Ed("c1") + 0.05                         # impact « 1992 »
cue["merc"] = S("c2") + 0.3
cue["toFR"] = [S("d1") - 0.2, S("d1") + 1.0]
cue["expand"] = [S("d1") + 0.4, Ed("d6")]
cue["labels"] = {"48": S("d2") + 0.1, "66": S("d3") + 0.1, "39": S("d4") + 0.1, "88": S("d5") + 0.1,
                 "29": S("d6") + 1.2, "76": S("d6") + 2.0}
cue["count"] = S("e1") + 0.4
cue["prey"] = S("f1") + 1.2
cue["downgrade"] = S("f2") + 0.3
cue["outro"] = S("g1") - 1.2
cue["next"] = S("g2") + 1.6

# années du ticker (segments linéaires) : [t0, t1, an0, an1, pas]
TL["ticker"] = [
    [S("a1"), S("a1") + 0.01, 1750, 1750, 10],
    [S("a2"), Ed("a3") - 0.4, 1750, 1930, 10],
    [S("b1") - 0.2, S("b1") + 0.01, 1970, 1970, 1],
    [S("b2"), S("b2") + 0.6, 1970, 1971, 1],
    [cue["path"][0], cue["path"][1], 1971, 1992, 1],
]
# expansion : années calées sur les répliques
EXP = [(S("d1"), 1992), (S("d2"), 1997), (S("d3"), 1999), (S("d4"), 2003), (S("d5"), 2011), (S("d6"), 2016), (Ed("d6"), 2025)]
for (t0, y0), (t1, y1) in zip(EXP, EXP[1:]): TL["ticker"].append([t0, t1, y0, y1, 1])
TL["ticker"].append([S("e1"), S("e1") + 0.01, 2025, 2025, 1])
cue["tickerShow"] = [S("a1") - 0.3, Ed("f2") + 0.3]

# ------------------------------------------------------------------ bruitages (positions)
sfx("howl2", 0.05, 0.9)
sfx("pop", 0.25, 0.7)
sfx("pop", S("h2") + 1.3, 0.8)                       # badge +1 000
sfx("whoosh_long", cue["zoomFR"][0], 1.0)
sfx("impact", cue["zoomFR"][1] - 0.1, 0.7)
sfx("wind", S("a2") - 0.3, 0.6)
sfx("stamp", cue["stamp"], 1.0)
sfx("whoosh_long", cue["toItaly"][0], 0.9)
sfx("shimmer", cue["apennins"][0] + 0.3, 0.5)
sfx("pop", cue["protect"], 0.8)
sfx("riser", cue["arrive"], 0.9)
sfx("impact", cue["arrive"], 1.0)
sfx("pop", cue["merc"], 0.8)
sfx("howl", cue["merc"] + 0.2, 0.55)
sfx("whoosh_long", cue["toFR"][0], 0.9)
for c, tt in cue["labels"].items(): sfx("hit", tt, 0.6)
sfx("impact", cue["count"], 0.8); sfx("bell", cue["count"] + 0.05, 0.5)
sfx("hit", cue["prey"], 0.9)
sfx("down", cue["downgrade"] + 0.6, 0.8)
sfx("howl2", cue["outro"], 0.9)
sfx("pop", cue["next"], 0.7)
# pas : empreintes le long du tracé (régulières)
NPAW = 22
for i in range(NPAW):
    sfx("step", cue["path"][0] + (cue["path"][1] - cue["path"][0]) * (i + 0.5) / NPAW, 0.35 + 0.1*(i % 2))
cue["paws"] = NPAW
# ticks du ticker à chaque année franchie (limités à ~7 par seconde)
last = -9
for t0, t1, y0, y1, step in TL["ticker"]:
    if y1 == y0: continue
    for y in range(int(y0) + step, int(y1) + 1, step):
        tt = t0 + (t1 - t0) * (y - y0) / (y1 - y0)
        if tt - last > 0.14: sfx("tick", tt, 0.5); last = tt

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

BANK = {"howl": howl(), "howl2": howl_pack(), "whoosh": whoosh(), "whoosh_long": whoosh(1.6, 150, 2500),
        "impact": impact(), "hit": hit(), "stamp": stamp(), "pop": pop(), "tick": tick(), "step": step(),
        "bell": bell(), "shimmer": shimmer(), "riser": riser(), "down": down(), "wind": wind()}
fx = np.zeros(N, np.float32)
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
def section(x):   # intensité par section, 0..1 par couche
    if x < S("a1"):  return dict(pad=.8, pluck=0, drum=0, tens=0)
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
print(json.dumps({"duration": TL["duration"], "vo_end": Ed("g2")}))
