"""Épisode « La sterne arctique » : découpe la voix ElevenLabs, construit la timeline (carte + 3 plans 3D Blender),
place les bruitages (cri de sterne fourni, seulement dans l'intro + pack SFX) et synthétise la musique.

Usage : VO_FILE=assets/voix-sterne.mp3 python3 audio.py
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(9)

SCRIPT = [
 ("s01", "", "Cet oiseau de *100 grammes* fait, chaque année, le *plus long voyage* du monde."),
 ("s02", "", "Plus de *70 000 kilomètres*… et parfois bien plus."),
 ("s03", "", "Voici l'incroyable migration de la *sterne arctique*."),
 ("s04", "", "Tout commence en *juin*, au *Groenland*, tout près du pôle Nord."),
 ("s05", "", "Là-bas, c'est l'été : le soleil ne se *couche jamais*."),
 ("s06", "", "La sterne y pond ses *œufs*, et élève ses *petits*."),
 ("s07", "", "Mais dès la fin de l'été, elle s'envole vers le *sud*."),
 ("s08", "", "Direction : l'autre bout du monde. L'*Antarctique*."),
 ("s09", "", "Elle commence par faire une *pause* en plein milieu de l'Atlantique Nord… pour faire le plein de *poissons*."),
 ("s10", "", "Puis, au large de l'Afrique, la route se *sépare* : certaines longent les côtes *africaines*… d'autres traversent jusqu'au *Brésil*."),
 ("s11", "", "Après des semaines de vol, elle atteint enfin l'*Antarctique*."),
 ("s12", "", "Et là-bas… c'est l'été. *Encore l'été* !"),
 ("s13", "", "La sterne vit donc *deux étés* par an : c'est sans doute l'animal qui voit le plus la *lumière du jour* sur Terre."),
 ("s14", "", "Au printemps, elle repart vers le *nord*, en dessinant un immense *S* à travers l'Atlantique."),
 ("s15", "", "En *2016*, une sterne partie d'*Angleterre* a parcouru *96 000 kilomètres*… en *dix mois*."),
 ("s16", "", "Et comme elle peut vivre plus de *30 ans*…"),
 ("s17", "", "elle parcourt, dans sa vie, plus de *deux millions* de kilomètres."),
 ("s18", "", "C'est *trois allers-retours* entre la Terre et la *Lune* !"),
 ("s19", "", "Pas mal, pour un oiseau de *100 grammes*."),
 ("s20", "", "Et toi, tu connaissais la sterne arctique ? Dis-le en commentaire ! Et abonne-toi pour le prochain épisode."),
]
GAPS = {k: g for k, g in zip([s[0] for s in SCRIPT],
        [0.9, 0.4, 0.4, 0.8, 0.4, 0.4, 0.5, 0.4, 0.6, 0.5, 0.6, 0.4, 0.5, 0.6, 0.6, 0.6, 0.3, 0.4, 0.5, 0.8])}
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
TL = {"vo": [], "cue": {}, "ticker": [], "sfx": [], "photos": [], "clips": []}
t = 0.0
for k, _, cap in SCRIPT:
    t += GAPS[k]
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + dur[k], 3), "cap": cap})
    t += dur[k]
V = {v["id"]: v for v in TL["vo"]}
S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]; M = lambda k, f: S(k) + (Ed(k) - S(k))*f
TL["duration"] = round(Ed("s20") + 2.0, 3)
cue = TL["cue"]
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})
# 3 plans 3D (Blender) plein écran, ~4,5 s chacun, amenés par une plongée sur la carte
def clip(name, a, b): TL["clips"].append({"name": name, "a": round(a, 3), "b": round(b, 3)})
clip("groenland", M("s04", 0.55), M("s04", 0.55) + 4.6)
clip("ocean", M("s09", 0.35), M("s09", 0.35) + 4.4)
clip("antarctique", M("s11", 0.45), M("s11", 0.45) + 4.6)

cue["title"] = 0.3
cue["preview"] = [S("s02") - 0.2, Ed("s02")]          # la route complète se dessine
cue["k70"] = M("s02", 0.15)
cue["globe"] = [S("s03") - 0.3, Ed("s03")]
cue["green"] = [S("s04") - 0.4, M("s04", 0.55)]
cue["colony"] = [Ed("s04") + 0.2, Ed("s06") + 0.2]     # après le plan 3D
cue["south"] = [S("s07") - 0.2, Ed("s07") + 0.2]
cue["anta"] = [S("s08") - 0.2, Ed("s08")]
cue["stop"] = [S("s09") - 0.3, M("s09", 0.35)]
cue["split"] = [S("s10") - 0.4, Ed("s10")]
cue["arrive"] = [S("s11") - 0.3, M("s11", 0.45)]
cue["summers"] = [S("s13") - 0.4, Ed("s13")]
cue["north"] = [S("s14") - 0.3, Ed("s14") + 0.2]
cue["farne"] = [S("s15") - 0.3, Ed("s15") + 0.2]
cue["life"] = [S("s16") - 0.3, Ed("s17")]
cue["moon"] = [S("s18") - 0.5, Ed("s18") + 0.6]
cue["g100"] = [S("s19") - 0.2, Ed("s19")]
cue["outro"] = S("s20") - 0.3

# frise des mois (6 = juin … 17 = mai suivant)
TL["ticker"] = [
    [S("s04"), S("s04") + 0.01, 6, 6, 1],
    [S("s07"), Ed("s07"), 6, 8, 1],
    [S("s09"), M("s09", 0.3), 8, 9, 1],
    [S("s10"), Ed("s10"), 9, 10, 1],
    [S("s11"), M("s11", 0.4), 10, 12, 1],
    [S("s14"), Ed("s14"), 12, 17, 1],
]

# ------------------------------------------------------------------ bruitages
sfx("cri", 0.25, 0.8)                                     # cri de sterne : seulement dans l'intro
sfx("pop", cue["title"], 0.6); sfx("woosh", cue["preview"][0], 0.6); sfx("impact", cue["k70"], 0.55)
sfx("woosh", cue["globe"][0], 0.6); sfx("woosh", cue["green"][0], 0.7)
for c in TL["clips"]: sfx("woosh", c["a"] - 0.2, 0.8); sfx("woosh", c["b"] - 0.25, 0.5)
sfx("pop", cue["colony"][0] + 0.3, 0.5); sfx("woosh", cue["south"][0], 0.6); sfx("woosh", cue["anta"][0], 0.7); sfx("impact", M("s08", 0.75), 0.6)
sfx("pop", cue["stop"][0] + 1.0, 0.6); sfx("woosh", cue["split"][0], 0.6); sfx("pop", M("s10", 0.5), 0.5)
sfx("woosh", cue["arrive"][0], 0.6); sfx("woosh", cue["summers"][0], 0.6); sfx("impact", M("s13", 0.25), 0.6)
sfx("woosh", cue["north"][0], 0.6); sfx("woosh", cue["farne"][0], 0.7); sfx("impact", M("s15", 0.7), 0.6)
sfx("woosh", cue["life"][0], 0.7); sfx("impact", M("s17", 0.55), 0.7); sfx("woosh", cue["moon"][0], 0.6)
for i in range(3): sfx("pop", S("s18") + 0.3 + i*0.45, 0.5)
sfx("pop", cue["g100"][0] + 0.4, 0.6); sfx("woosh", cue["outro"], 0.5)
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
BANK = {k: load_wav(f"assets/s_{k}.wav") for k in ("pop", "woosh", "tick", "impact", "cri")}
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
    if x < S("s04"): return dict(pad=.8, pluck=.4, perc=.3)
    if x < S("s13"): return dict(pad=.9, pluck=1., perc=.7)
    if x < S("s16"): return dict(pad=.9, pluck=.8, perc=.9)
    if x < S("s19"): return dict(pad=1., pluck=.9, perc=1.)
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
