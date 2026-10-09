"""Épisode « Les hippopotames d'Escobar » : découpe la voix ElevenLabs, construit la timeline
(cartes + séquences photo plein écran), place les VRAIS bruitages fournis et synthétise la musique.

Usage : VO_FILE=assets/voix-hippo.mp3 python3 audio.py
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(9)

SCRIPT = [
 ("h01", "", "En Colombie, près de *200 hippopotames* vivent en liberté… à des milliers de kilomètres de l'*Afrique*."),
 ("h02", "", "Et tout ça… à cause de *Pablo Escobar*."),
 ("h03", "", "Dans les *années 80*, le baron de la drogue se fait construire un *zoo privé*, dans sa propriété : l'*Hacienda Nápoles*."),
 ("h04", "", "Girafes, zèbres, éléphants… et *quatre hippopotames* venus d'Afrique : un mâle et trois femelles."),
 ("h05", "", "En *1993*, Escobar est abattu par la police, à *Medellín*."),
 ("h06", "", "Les autorités déplacent la plupart des animaux… sauf les hippopotames, *trop dangereux* à transporter."),
 ("h07", "", "Abandonnés, ils rejoignent le fleuve *Magdalena*… et y trouvent le paradis : de l'eau toute l'année, et *aucun prédateur*."),
 ("h08", "", "Résultat : la population *explose*."),
 ("h09", "", "Au départ, ils étaient *quatre*. En *2023*, on en recense environ *170*."),
 ("h10", "", "Et ils sont *dangereux* : l'hippopotame est l'un des animaux les plus *meurtriers* d'Afrique."),
 ("h11", "", "Leurs excréments *polluent les rivières*, et ils menacent les espèces locales, comme le *lamantin*."),
 ("h12", "", "En *2022*, la Colombie les déclare officiellement *espèce invasive*."),
 ("h13", "", "Le gouvernement essaie tout : la *stérilisation*… puis l'envoi de *70 hippopotames* en *Inde* et au *Mexique*."),
 ("h14", "", "Mais *aucun pays* ne les accepte."),
 ("h15", "", "Alors, en *avril 2026*, la Colombie autorise l'*euthanasie* d'environ *80 hippopotames*."),
 ("h16", "", "Une décision qui *divise* : pour les habitants de la région, ils sont devenus une *attraction*… et un *symbole*."),
 ("h17", "", "Et selon certaines projections, sans intervention, ils pourraient être *plus de 1 000* d'ici *2035*."),
 ("h18", "", "Et toi, tu ferais quoi des hippopotames d'Escobar ? Dis-le en commentaire !"),
]
GAPS = {k: g for k, g in zip([s[0] for s in SCRIPT],
        [0.9, 0.4, 0.6, 0.5, 0.6, 0.6, 0.6, 0.4, 0.4, 0.7, 0.5, 0.6, 0.6, 0.4, 0.6, 0.6, 0.6, 0.8])}
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
TL["duration"] = round(Ed("h18") + 2.2, 3)
cue = TL["cue"]
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})
def photo(img, a, b, z0=1.04, z1=1.14, px=0.0, py=0.0, gray=0.0): TL["photos"].append(dict(img=img, a=round(a,3), b=round(b,3), z0=z0, z1=z1, px=px, py=py, gray=gray))

# séquences photo plein écran : courtes et ponctuelles (~2 s), toujours après une plongée sur la carte
photo("p2", M("h03", 0.62), M("h03", 0.62) + 2.0, 1.04, 1.14, 0.0, -0.02)
photo("p3", S("h04") - 0.1, S("h04") + 1.9, 1.05, 1.14, 0.03, 0.0)
photo("p4", M("h06", 0.42), M("h06", 0.42) + 1.9, 1.04, 1.12, -0.02, 0.0, 0.35)
photo("p5", M("h07", 0.62), M("h07", 0.62) + 2.0, 1.04, 1.13, 0.0, 0.02)
photo("p6", S("h10") + 0.2, S("h10") + 2.3, 1.02, 1.18, 0.0, -0.02)
photo("p7", M("h11", 0.45), M("h11", 0.45) + 1.9, 1.04, 1.12, 0.02, 0.0)
photo("p8", M("h16", 0.32), M("h16", 0.32) + 2.0, 1.04, 1.13, -0.02, 0.0)

# repères carte
cue["intro"] = [0.6, M("h01", 0.42), M("h01", 0.72)]       # Afrique zoomée → recul + demi-tour → Colombie
cue["flag"] = M("h01", 0.7)
cue["title"] = 0.3
cue["k200"] = M("h01", 0.15)
cue["kEscobar"] = M("h02", 0.3)
cue["napoles"] = [S("h03") - 0.2, S("h03") + 0.9]
cue["ultraNap"] = [M("h03", 0.36), M("h03", 0.62)]          # plongée jusque dans le zoo → photo p2
cue["arc"] = [S("h04") + 1.6, Ed("h04") + 0.2]
cue["medellin"] = [S("h05") - 0.4, S("h05") + 0.6]
cue["ultraAband"] = [S("h06"), M("h06", 0.42)]
cue["river"] = [S("h07") - 0.4, S("h07") + 0.8]               # embouchure du Magdalena
cue["sweep"] = [S("h07") + 0.8, M("h07", 0.5)]                 # balayage le long du fleuve
cue["ultraRiv"] = [M("h07", 0.5), M("h07", 0.62)]
cue["boom"] = [S("h08") - 0.4, Ed("h09")]
cue["k170"] = M("h09", 0.62)
cue["ultraRiv2"] = [S("h11"), M("h11", 0.45)]
cue["invasive"] = [S("h12") - 0.4, S("h12") + 0.6]
cue["stampInv"] = M("h12", 0.6)
cue["mexico"] = [S("h13") - 0.3, M("h13", 0.55)]
cue["india"] = [M("h13", 0.55), Ed("h13") + 0.4]
cue["refuse"] = M("h14", 0.4)
cue["back"] = [S("h15") - 0.4, S("h15") + 0.9]
cue["k80"] = M("h15", 0.7)
cue["ultraVill"] = [S("h16"), M("h16", 0.32)]
cue["future"] = [M("h16", 0.32) + 2.0, S("h17") + 0.8]
cue["k1000"] = M("h17", 0.6)
cue["outro"] = S("h18") - 0.3

TL["ticker"] = [
    [S("h03"), S("h03") + 0.01, 1981, 1981, 1],
    [S("h05"), M("h05", 0.3), 1981, 1993, 1],
    [S("h09"), M("h09", 0.62), 1993, 2023, 5],
    [S("h12"), S("h12") + 0.01, 2022, 2022, 1],
    [S("h15"), M("h15", 0.3), 2022, 2026, 1],
    [S("h17"), M("h17", 0.6), 2026, 2035, 1],
]

# ------------------------------------------------------------------ bruitages (vrais fichiers fournis)
sfx("woosh", 0.55, 0.6)
sfx("cri", Ed("h01") - 0.1, 0.9)
for k in ("ultraNap", "ultraAband", "ultraRiv", "ultraRiv2", "ultraVill"): sfx("woosh", cue[k][0] + 0.05, 0.35)
sfx("woosh", cue["sweep"][0], 0.4)
for p in TL["photos"]:
    sfx("woosh", p["a"] - 0.15, 0.7)                     # entrée de chaque séquence photo
sfx("woosh", cue["intro"][0] - 0.1, 0.8); sfx("woosh", cue["intro"][1], 0.6)
sfx("impact", cue["flag"], 0.55)
sfx("pop", cue["title"], 0.6); sfx("pop", cue["kEscobar"], 0.6)
sfx("pop", cue["napoles"][1] - 0.2, 0.6)
sfx("woosh", cue["arc"][0] + 0.2, 0.6)
sfx("woosh", cue["medellin"][0], 0.6); sfx("impact", M("h05", 0.55), 0.5)
sfx("woosh", cue["river"][0], 0.6)
sfx("pop", cue["boom"][0] + 0.6, 0.6); sfx("impact", cue["k170"], 0.6)
sfx("cri", S("h10") + 0.2, 0.75); sfx("impact", M("h10", 0.7), 0.5)
sfx("woosh", cue["invasive"][0], 0.6); sfx("impact", cue["stampInv"], 0.8)
sfx("woosh", cue["mexico"][0], 0.6); sfx("woosh", cue["india"][0], 0.6)
sfx("impact", cue["refuse"], 0.8)
sfx("woosh", cue["back"][0], 0.7); sfx("impact", cue["k80"], 0.6)
sfx("woosh", cue["future"][0], 0.6); sfx("impact", cue["k1000"], 0.6)
sfx("cri", S("h18") + 0.4, 0.7)
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

# ------------------------------------------------------------------ musique (tension tropicale, 96 BPM, la mineur)
lp = lambda x, f: sosfilt(butter(2, f, "lowpass", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, "highpass", fs=SR, output="sos"), x)
def reverb(x, decay=1.6, mix=0.25):
    n = int(decay*SR); ir = rng.standard_normal(n)*np.exp(-np.arange(n)/SR*6.9/decay); ir = lp(ir, 5000); ir /= np.sqrt((ir**2).sum())
    wet = fftconvolve(x, ir); out = np.zeros(len(wet)); out[:len(x)] += x*(1 - mix); out += wet*mix; return out
bpm = 96; beat = 60/bpm; bar = 4*beat; A = 55.0
PROG = [(0, [0, 3, 7]), (8, [0, 4, 7]), (3, [0, 4, 7]), (10, [0, 4, 7])]          # Am F C G
def section(x):
    if x < S("h03"): return dict(pad=.8, pluck=.4, perc=.4)
    if x < S("h10"): return dict(pad=.8, pluck=1., perc=.8)
    if x < S("h13"): return dict(pad=.9, pluck=.6, perc=1.)
    if x < S("h16"): return dict(pad=.9, pluck=.8, perc=1.)
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
