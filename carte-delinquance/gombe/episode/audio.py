"""Épisode « La guerre des chimpanzés de Gombe » : découpe la voix, timeline, bruitages, musique.
Usage : VO_FILE=assets/voix.mp3 python3 audio.py"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(11)

SCRIPT = [
 ("s01", "", "Ils avaient grandi ensemble, mangé ensemble, dormi ensemble… *4 ans plus tard*, ils s'étaient *entretués*."),
 ("s02", "", "Ce ne sont pas des humains. Ce sont des *chimpanzés*. Et c'est la *première guerre* jamais observée chez les animaux."),
 ("s03", "", "Voici la guerre des chimpanzés de *Gombe*."),
 ("s04", "", "Tout se passe ici, au bord du *lac Tanganyika*, dans le petit parc national de *Gombe*."),
 ("s05", "", "Depuis *1960*, la primatologue *Jane Goodall* y observe une communauté de chimpanzés : *Kasakela*."),
 ("s06", "", "À l'époque, elle pense que les chimpanzés sont *plus pacifiques* que nous."),
 ("s07", "", "Mais au début des années *70*, la communauté se *divise*."),
 ("s08", "", "*6 mâles*, *3 femelles* et leurs petits partent s'installer au *sud*. Ils forment un nouveau clan : *Kahama*."),
 ("s09", "", "Au *nord*, Kasakela garde *8 mâles* adultes et *12 femelles*."),
 ("s10", "", "Pendant un temps, les deux clans s'évitent. Puis la frontière devient un *champ de bataille*."),
 ("s11", "", "Le *7 janvier 1974*, *6 mâles* de Kasakela s'enfoncent en silence dans le territoire de *Kahama*."),
 ("s12", "", "Ils surprennent *Godi*, un jeune mâle, seul dans un arbre. Ils le frappent, le mordent… Godi ne sera *jamais revu*."),
 ("s13", "", "C'est la *première fois* qu'on voit des chimpanzés *tuer volontairement* l'un des leurs."),
 ("s14", "", "Et ce n'est que le début. Les *raids* se multiplient."),
 ("s15", "", "Même le vieux *Goliath*, qui avait été l'un de leurs chefs, est attaqué par ses *anciens amis*."),
 ("s16", "", "Un à un, les *6 mâles* de Kahama disparaissent. Le dernier, *Sniff*, est tué en *1978*."),
 ("s17", "", "*Kasakela a gagné*. Et s'empare de *tout le territoire*."),
 ("s18", "", "Mais la victoire ne dure pas : au sud, un clan encore plus puissant, *Kalande*, repousse bientôt les vainqueurs."),
 ("s19", "", "Pour Jane Goodall, c'est un *choc* : la guerre n'est pas une *invention humaine*."),
 ("s20", "", "Et toi, tu savais que les chimpanzés pouvaient se faire la guerre ? Dis-le en commentaire ! Et abonne-toi pour le prochain épisode."),
]
GAPS = {k: g for k, g in zip([s[0] for s in SCRIPT],
        [1.2, 0.5, 0.4, 0.7, 0.5, 0.4, 0.5, 0.4, 0.4, 0.5, 0.6, 0.4, 0.5, 0.5, 0.5, 0.6, 0.5, 0.5, 0.6, 0.8])}
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
    if os.path.exists("vo_bounds.json"):                                  # découpage aligné (align.py)
        out = {k: trim(x[a:b]) for k, (a, b) in zip(ids, json.load(open("vo_bounds.json")))}
        os.makedirs("vo", exist_ok=True)
        for k, v in out.items(): sf.write(f"vo/{k}.wav", v, SR)
        return out
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
TL = {"vo": [], "cue": {}, "ticker": [], "sfx": [], "clips": []}
t = 0.0
for k, _, cap in SCRIPT:
    t += GAPS[k]
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + dur[k], 3), "cap": cap})
    t += dur[k]
    if k == "s04": t += 3.4                                   # place pour le plan 3D de la vallée
    if k == "s11": t += 2.6                                   # plan 3D du raid
    if k == "s18": t += 2.4                                   # plan 3D de Kalande
V = {v["id"]: v for v in TL["vo"]}
S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]; M = lambda k, f: S(k) + (Ed(k) - S(k))*f
TL["duration"] = round(Ed("s20") + 2.0, 3)
cue = TL["cue"]
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})
def clip(name, a, b): TL["clips"].append({"name": name, "a": round(a, 3), "b": round(b, 3)})
clip("vallee", Ed("s04") - 0.6, Ed("s04") - 0.6 + 4.5)
clip("raid", Ed("s11") - 1.6, Ed("s11") - 1.6 + 4.5)
clip("kalande", Ed("s18") - 1.8, Ed("s18") - 1.8 + 4.5)
# frise des années : [t0, t1, an0, an1]
TL["ticker"] = [[S("s05"), M("s05", 0.3), 1960, 1960], [S("s07"), M("s07", 0.5), 1960, 1972],
                [S("s11"), M("s11", 0.3), 1972, 1974], [S("s14"), Ed("s14"), 1974, 1976], [S("s16"), Ed("s16"), 1976, 1978]]
# ------------------------------------------------------------------ bruitages (cri de chimpanzé : seulement dans l'intro)
sfx("cri", 0.15, 0.9)
sfx("impact", M("s01", 0.62), 0.7); sfx("woosh", S("s02") - 0.2, 0.6); sfx("pop", M("s02", 0.35), 0.5); sfx("impact", M("s02", 0.7), 0.6)
sfx("woosh", S("s03") - 0.3, 0.7); sfx("woosh", S("s04") - 0.2, 0.6); sfx("pop", M("s04", 0.55), 0.5)
for c in TL["clips"]: sfx("woosh", c["a"] - 0.2, 0.8); sfx("woosh", c["b"] - 0.25, 0.5)
sfx("pop", S("s05") + 0.3, 0.6); sfx("pop", M("s05", 0.85), 0.5); sfx("pop", M("s06", 0.4), 0.5)
sfx("woosh", S("s07") - 0.2, 0.5); sfx("impact", M("s07", 0.75), 0.6)
for i in range(9): sfx("pop", M("s08", 0.05) + i*0.18, 0.35)
for i in range(20): sfx("pop", M("s09", 0.3) + i*0.09, 0.22)
sfx("impact", M("s10", 0.65), 0.7); sfx("woosh", S("s11") - 0.2, 0.6); sfx("impact", M("s11", 0.1), 0.5)
sfx("impact", M("s12", 0.45), 0.8); sfx("woosh", M("s12", 0.8), 0.4); sfx("impact", M("s13", 0.3), 0.6)
for i in range(5): sfx("impact", M("s14", 0.45) + i*0.28, 0.4)
sfx("impact", M("s15", 0.7), 0.7)
for i in range(6): sfx("impact", M("s16", 0.08) + i*0.42, 0.45)
sfx("woosh", S("s17") - 0.1, 0.6); sfx("impact", M("s17", 0.5), 0.6); sfx("woosh", S("s18") - 0.2, 0.6); sfx("impact", M("s18", 0.45), 0.7)
sfx("impact", M("s19", 0.3), 0.6); sfx("woosh", S("s20") - 0.3, 0.5)
last = -9
for t0, t1, y0, y1 in TL["ticker"]:
    for y in range(int(y0) + 1, int(y1) + 1):
        tt = t0 + (t1 - t0)*(y - y0)/max(1, y1 - y0)
        if tt - last > 0.12: sfx("tick", tt, 0.4); last = tt
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
BANK = {k: load_wav(f"assets/s_{k}.wav") for k in ("pop", "woosh", "tick", "impact", "cri")}
fx = np.zeros(N, np.float32)
for s in TL["sfx"]:
    x = BANK[s["name"]]*s["gain"]; i = max(int(s["t"]*SR), 0); fx[i:i+len(x)] += x[:N-i]
sf.write("sfx.wav", fx, SR)
# ------------------------------------------------------------------ musique (tension, 84 BPM, ré mineur, cordes graves + tambours)
lp = lambda x, f: sosfilt(butter(2, f, "lowpass", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, "highpass", fs=SR, output="sos"), x)
def reverb(x, decay=2.2, mix=0.3):
    n = int(decay*SR); ir = rng.standard_normal(n)*np.exp(-np.arange(n)/SR*6.9/decay); ir = lp(ir, 4500); ir /= np.sqrt((ir**2).sum())
    wet = fftconvolve(x, ir); out = np.zeros(len(wet)); out[:len(x)] += x*(1 - mix); out += wet*mix; return out
bpm = 84; beat = 60/bpm; bar = 4*beat; D = 73.42/2
PROG = [(0, [0, 3, 7]), (8, [0, 4, 7]), (5, [0, 3, 7]), (7, [0, 4, 7])]          # Dm Bb Gm A
def section(x):
    if x < S("s04"): return dict(pad=.9, pulse=.3, drum=.5)
    if x < S("s10"): return dict(pad=.8, pulse=.6, drum=.3)
    if x < S("s17"): return dict(pad=1., pulse=1., drum=1.)
    if x < S("s19"): return dict(pad=1., pulse=.8, drum=.8)
    return dict(pad=.9, pulse=.5, drum=.4)
mus = np.zeros(N)
for b in range(int(TL["duration"]/bar) + 1):
    t0 = b*bar; sec = section(t0 + 0.01); i0 = int(t0*SR); root, iv = PROG[b % 4]
    n = int(bar*SR) + int(0.8*SR); tl = np.arange(n)/SR
    env = np.clip(tl/0.8, 0, 1)*np.clip((bar + 0.8 - tl)/0.8, 0, 1); f0 = D*2**(root/12)
    saw = lambda f: sum(np.sin(2*np.pi*f*h*tl + h)/h for h in range(1, 7))
    seg = lp(sum(saw(f0*2*2**(s/12)) for s in iv)/3, 1400)*env*0.07*sec["pad"] + np.sin(2*np.pi*f0*tl)*env*0.18*sec["pad"]
    for k in range(8):                                                       # pulsation de cordes en croches
        st = int(k*beat/2*SR); tn = np.arange(int(beat/2*SR))/SR; f = f0*2
        pl = lp(saw_ := sum(np.sin(2*np.pi*f*h*tn)/h for h in range(1, 6)), 1800)*np.exp(-tn*7)
        e = min(len(pl), n - st); seg[st:st+e] += pl[:e]*0.05*sec["pulse"]
    for k in (0, 1.5, 2, 3.5):                                               # tambours graves (taiko)
        st = int(k*beat*SR); tn = np.arange(int(0.6*SR))/SR
        h = np.sin(2*np.pi*np.cumsum(48 + 70*np.exp(-tn*18))/SR)*np.exp(-tn*6)*0.32 + lp(rng.standard_normal(len(tn)), 900)*np.exp(-tn*30)*0.05
        seg[st:st+len(h)] += h*sec["drum"]*(1 if k in (0, 2) else 0.6)
    e = min(n, N - i0)
    if e > 0: mus[i0:i0+e] += seg[:e]
mus = reverb(mus)[:N]; mus *= np.clip(tt/1.5, 0, 1)*np.clip((TL["duration"] - tt)/2.0, 0, 1)
sf.write("music.wav", (mus/np.abs(mus).max()*0.6).astype(np.float32), SR)
print(json.dumps({"duration": TL["duration"]}))
