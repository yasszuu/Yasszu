"""Génère la voix off, la timeline, les bruitages et la musique.

Sorties : vo.wav, sfx.wav, music.wav, timeline.json
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt

SR = 44100
VOICE = os.environ.get("VOICE", "tom")
rng = np.random.default_rng(3)

# ------------------------------------------------------------------ voix off
# say = texte prononcé, cap = sous-titre affiché (*mot* = surligné en jaune)
SCRIPT = {
    "hook":  dict(say="Quels sont les départements où l'on enregistre le plus de crimes et délits en France ?",
                  cap="Quels sont les *départements* où l'on enregistre le plus de *crimes et délits* en France ?"),
    "intro": dict(say="Voici le classement officiel de deux mille vingt-quatre, rapporté au nombre d'habitants.",
                  cap="Voici le classement *officiel 2024*, rapporté au nombre d'habitants."),
    "n5": dict(say="Numéro cinq.", cap="Numéro *5*"),
    "d5": dict(say="L'Hérault. Soixante-deux faits pour mille habitants.", cap="L'*Hérault* : *62* faits pour 1 000 habitants"),
    "n4": dict(say="Numéro quatre.", cap="Numéro *4*"),
    "d4": dict(say="Le Rhône. Soixante-dix pour mille.", cap="Le *Rhône* : *70* pour 1 000"),
    "n3": dict(say="Numéro trois.", cap="Numéro *3*"),
    "d3": dict(say="La Seine-Saint-Denis. Près de soixante-dix-sept pour mille.", cap="La *Seine-Saint-Denis* : près de *77* pour 1 000"),
    "n2": dict(say="Numéro deux.", cap="Numéro *2*"),
    "d2": dict(say="Les Bouches-du-Rhône. Quatre-vingts pour mille.", cap="Les *Bouches-du-Rhône* : *80* pour 1 000"),
    "n1": dict(say="Et numéro un...", cap="Et numéro *1*..."),
    "d1": dict(say="Paris ! Cent seize faits pour mille habitants.", cap="*Paris* ! *116* faits pour 1 000 habitants"),
    "why": dict(say="Un record gonflé par les millions de touristes et de travailleurs qui passent chaque jour dans la capitale.",
                cap="Un record gonflé par les *millions de touristes* et de travailleurs qui passent chaque jour dans la capitale."),
    "cta": dict(say="Et toi, ton département est dans le classement ? Dis-le en commentaire !",
                cap="Et toi, ton département est dans le classement ? *Dis-le en commentaire !*"),
}

def tts_all():
    import sherpa_onnx
    d = f"vits-piper-fr_FR-{VOICE}-medium"
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=f"{d}/fr_FR-{VOICE}-medium.onnx", tokens=f"{d}/tokens.txt",
                                                   data_dir=f"{d}/espeak-ng-data", length_scale=0.92, noise_scale=0.6),
        num_threads=4))
    tts = sherpa_onnx.OfflineTts(cfg)
    out = {}
    os.makedirs("vo", exist_ok=True)
    for k, v in SCRIPT.items():
        a = tts.generate(v["say"], sid=0, speed=1.0)
        x = np.asarray(a.samples, dtype=np.float32)
        if a.sample_rate != SR: x = resample_poly(x, SR, a.sample_rate).astype(np.float32)
        # retire les silences de début/fin
        nz = np.where(np.abs(x) > 0.01)[0]
        x = x[max(nz[0]-200, 0): nz[-1]+800]
        sf.write(f"vo/{k}.wav", x, SR)
        out[k] = x
    return out

clips = tts_all()
dur = {k: len(v)/SR for k, v in clips.items()}

# ------------------------------------------------------------------ timeline
TL = {"vo": [], "items": [], "sfx": []}
def place(k, t):
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t+dur[k], 3), "cap": SCRIPT[k]["cap"]})
    return t + dur[k]
def sfx(name, t, gain=1.0): TL["sfx"].append({"name": name, "t": round(t, 3), "gain": gain})

t = 0.35
sfx("pop", 0.25, 0.8)
t = place("hook", t)
TL["spinEnd"] = max(t - 0.2, 3.6)
sfx("whoosh", TL["spinEnd"] - 0.9, 0.7)
TL["zoom"] = [TL["spinEnd"], TL["spinEnd"] + 2.4]
sfx("whoosh_long", TL["zoom"][0] - 0.1, 1.0)
sfx("impact", TL["zoom"][1] - 0.05, 0.9)
t = place("intro", TL["zoom"][0] + 0.3)
TL["title"] = TL["zoom"][0] + 0.6
sfx("pop", TL["title"], 0.6)
t = max(t, TL["zoom"][1]) + 0.35

CODES = {"5": ("34", "Hérault", 62.3), "4": ("69", "Rhône", 70.5), "3": ("93", "Seine-Saint-Denis", 76.7),
         "2": ("13", "Bouches-du-Rhône", 80), "1": ("75", "Paris", 116)}
for r in "54321":
    t0 = t
    sfx("whoosh", t0, 0.8)
    sfx("tick", t0 + 0.05, 0.9)
    if r == "1":
        tn = place("n1", t0 + 0.15)
        thi = tn + 0.75                      # pause dramatique
    else:
        tn = place("n" + r, t0 + 0.1)
        thi = max(t0 + 1.0, tn + 0.15)
    sfx("impact" if r == "1" else "hit", thi, 1.0 if r == "1" else 0.85)
    if r == "1": sfx("bell", thi + 0.05, 0.7); sfx("riser", thi, 0.9)   # le riser se termine sur l'impact
    te = place("d" + r, thi + 0.05)
    code, name, rate = CODES[r]
    TL["items"].append({"rank": int(r), "code": code, "name": name, "rate": rate,
                        "t0": round(t0, 3), "tHi": round(thi, 3), "tEnd": round(te + 0.35, 3)})
    t = te + 0.4

TL["final"] = t
sfx("whoosh_long", t, 0.8)
for j in range(5): sfx("tick", t + 1.0 + j*0.14, 0.7)
t = place("why", t + 0.6)
t = place("cta", t + 0.35)
sfx("pop", TL["vo"][-1]["start"], 0.6)
TL["duration"] = round(t + 1.6, 3)
json.dump(TL, open("timeline.json", "w"), ensure_ascii=False, indent=1)
N = int(TL["duration"] * SR) + SR

# ------------------------------------------------------------------ piste voix
vo = np.zeros(N, np.float32)
for v in TL["vo"]:
    x = clips[v["id"]]; i = int(v["start"]*SR); vo[i:i+len(x)] += x
sf.write("vo.wav", vo, SR)

# ------------------------------------------------------------------ bruitages
T = lambda d: np.arange(int(d*SR)) / SR
def env(n, a, d):  # attaque / décroissance exponentielle
    t = np.arange(n)/SR; return np.minimum(t/a, 1) * np.exp(-t/d)
def bandsweep(noise, f0, f1, q=1.2):
    out = np.zeros_like(noise); n = len(noise); blk = 512
    for i in range(0, n, blk):
        f = f0 * (f1/f0) ** (i/n)
        sos = butter(2, [max(f/q, 30), min(f*q, SR/2-100)], "bandpass", fs=SR, output="sos")
        out[i:i+blk] = sosfilt(sos, noise[i:i+blk])
    return out
def whoosh(d=0.9, f0=300, f1=3500):
    n = int(d*SR); x = bandsweep(rng.standard_normal(n), f0, f1)
    t = np.linspace(0, 1, n); e = np.sin(np.pi*t**0.7)**2
    return (x*e/np.abs(x).max()*0.6).astype(np.float32)
def impact():
    t = T(1.6); f = 38 + 90*np.exp(-t*14)
    sub = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*2.6)
    click = rng.standard_normal(len(t)) * np.exp(-t*60) * 0.5
    sos = butter(2, 2500, "lowpass", fs=SR, output="sos")
    return (0.9*sub + sosfilt(sos, click)).astype(np.float32)
def hit():
    t = T(0.6); f = 60 + 160*np.exp(-t*30)
    body = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*7)
    sn = sosfilt(butter(2, [1500, 7000], "bandpass", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t*25)
    return (0.8*body + 0.35*sn).astype(np.float32)
def pop():
    t = T(0.18); f = 700 + 900*(1-np.exp(-t*40))
    return (np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*28) * 0.5).astype(np.float32)
def tick():
    t = T(0.06); return (np.sin(2*np.pi*2400*t) * np.exp(-t*90) * 0.4).astype(np.float32)
def bell():
    t = T(2.5); x = sum(a*np.sin(2*np.pi*880*m*t)*np.exp(-t*dd) for m, a, dd in
                        [(1, .5, 1.6), (2.76, .25, 2.5), (5.4, .12, 4), (8.9, .06, 6)])
    return (x*env(len(t), 0.002, 10)).astype(np.float32)
def riser(d=1.6):
    n = int(d*SR); t = np.linspace(0, 1, n)
    x = bandsweep(rng.standard_normal(n), 400, 6000, 1.5) * t**2
    tone = np.sin(2*np.pi*np.cumsum(200 + 600*t**2)/SR) * t**2 * 0.15
    y = x/np.abs(x).max()*0.5 + tone; y[-int(0.02*SR):] *= np.linspace(1, 0, int(0.02*SR))
    return y.astype(np.float32)

BANK = {"whoosh": whoosh(), "whoosh_long": whoosh(1.6, 150, 2500), "impact": impact(), "hit": hit(),
        "pop": pop(), "tick": tick(), "bell": bell(), "riser": riser()}
sfxL = np.zeros(N, np.float32)
for s in TL["sfx"]:
    x = BANK[s["name"]] * s["gain"]; i = int(s["t"]*SR)
    if s["name"] == "riser": i -= len(x)
    i = max(i, 0)
    sfxL[i:i+len(x)] += x[:N-i]
sf.write("sfx.wav", sfxL, SR)

# ------------------------------------------------------------------ musique (boucle sombre 100 BPM)
bpm = 100; beat = 60/bpm; tt = np.arange(N)/SR
mus = np.zeros(N, np.float32)
kick = (np.sin(2*np.pi*np.cumsum(45 + 110*np.exp(-T(0.4)*25))/SR) * np.exp(-T(0.4)*9)).astype(np.float32)
hat = (sosfilt(butter(2, 7000, "highpass", fs=SR, output="sos"), rng.standard_normal(int(0.05*SR))) * np.exp(-T(0.05)*80)).astype(np.float32)
roots = [55.0, 55.0, 43.65, 49.0]   # A, A, F, G
nb = int(TL["duration"]/beat)
music_start = TL["zoom"][1] - 4*beat
for b in range(nb):
    tb = b*beat
    i = int(tb*SR)
    if tb >= music_start and b % 1 == 0: mus[i:i+len(kick)] += kick[:N-i]*0.9
    j = int((tb + beat/2)*SR)
    mus[j:j+len(hat)] += hat[:N-j]*0.25
# basse + nappe
bar = (tt/(4*beat)).astype(int) % 4
f = np.array(roots)[bar]
bass = np.sign(np.sin(2*np.pi*np.cumsum(f)/SR)) * 0.18
bass = sosfilt(butter(2, 220, "lowpass", fs=SR, output="sos"), bass)
pad = sum(np.sin(2*np.pi*np.cumsum(f*m*(1+dt))/SR) for m in (4, 6, 8) for dt in (-0.003, 0.003)) * 0.03
pulse = 0.6 + 0.4*np.sin(2*np.pi*tt/(beat/2))**2
mus += (bass*pulse + pad).astype(np.float32)
fade_in = np.clip(tt/2.5, 0, 1); fade_out = np.clip((TL["duration"] - tt)/1.5, 0, 1)
mus *= fade_in*fade_out
sf.write("music.wav", mus.astype(np.float32), SR)
print(json.dumps({k: TL[k] for k in ("spinEnd", "zoom", "final", "duration")}))
