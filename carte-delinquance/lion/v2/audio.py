"""Épisode « Le lion de l'Atlas » : découpe la voix ElevenLabs, construit la timeline,
synthétise les bruitages et la musique (gamme orientale, percussions).

Usage : VO_FILE=voix-lion.mp3 python3 audio.py
Sorties : vo.wav, sfx.wav, music.wav, timeline.json
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(7)

# (id, texte, sous-titre (*mot* = jaune))
SCRIPT = [
 ("l01", "On le disait le plus grand lion du monde… et il vivait au Maroc.", "On le disait le *plus grand lion du monde*… et il vivait au *Maroc*."),
 ("l02", "Voici l'histoire du lion de l'Atlas.", "Voici l'histoire du *lion de l'Atlas*."),
 ("l03", "", "Il y a *2 000 ans*, il régnait sur toute l'*Afrique du Nord*, du Maroc jusqu'à l'Égypte."),
 ("l04", "", "Sa *crinière sombre* descendait jusqu'au ventre, et les chasseurs parlaient de mâles de près de *300 kilos*."),
 ("l05", "", "Mais les *Romains* en capturent des milliers, pour les jeux du *Colisée*."),
 ("l06", "", "Puis, avec les *fusils* et les primes à la chasse, il recule jusque dans les montagnes de l'*Atlas*."),
 ("l07", "", "En *1925*, depuis un avion, un photographe capture l'une des *dernières images* d'un lion sauvage."),
 ("l08", "", "Et en *1942*, le *dernier lion connu* est abattu près du col du *Tizi n'Tichka*."),
 ("l09", "", "Le lion de l'Atlas a *disparu de la nature*."),
 ("l10", "", "Pourtant… l'histoire *ne s'arrête pas là*."),
 ("l11", "", "Pendant des siècles, les tribus offraient des lions aux *sultans du Maroc*."),
 ("l12", "", "Et la *ménagerie royale* les a gardés… jusqu'à aujourd'hui."),
 ("l13", "", "Leurs descendants vivent au *zoo de Rabat*, qui abrite le plus grand groupe de lions de l'Atlas au monde."),
 ("l14", "", "Dans tous les zoos de la planète, ils sont *moins d'une centaine*."),
 ("l15", "", "Et même si leur *pureté génétique* fait débat, ils sont le dernier lien avec ce lion légendaire."),
 ("l16", "", "En *2025*, *quatre lionceaux* de l'Atlas sont nés dans un zoo, en *Tchéquie*…"),
 ("l17", "", "et on parle même de les *réintroduire* un jour au *Maroc* !"),
 ("l18", "", "Aujourd'hui, il reste le *symbole du pays*… au point de donner son nom à l'*équipe nationale* de football."),
 ("l19", "", "Alors… est-ce que tu aimerais le revoir rugir dans les montagnes de l'Atlas ?"),
 ("l20", "", "Dis-le en commentaire ! Et abonne-toi pour ne pas rater le prochain épisode."),
]
# silences ajoutés avant chaque réplique (respiration / mouvements de caméra)
GAPS = {"l01": 1.7, "l02": 0.3, "l03": 0.5, "l04": 0.45, "l05": 0.5, "l06": 0.45, "l07": 0.5, "l08": 0.4, "l09": 0.45,
        "l10": 0.7, "l11": 0.5, "l12": 0.3, "l13": 0.45, "l14": 0.4, "l15": 0.35, "l16": 0.5, "l17": 0.25, "l18": 0.5,
        "l19": 0.7, "l20": 0.3}
def load_external():
    return {k: sf.read(f"vo/{k}.wav", dtype="float32")[0] for k, *_ in SCRIPT}
clips = load_external()
dur = {k: len(v)/SR for k, v in clips.items()}

# ------------------------------------------------------------------ timeline
TL = {"vo": [], "cue": {}, "ticker": [], "sfx": [], "clips": []}
t = 0.0
for k, _, cap in SCRIPT:
    t += GAPS[k]
    TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + dur[k], 3), "cap": cap})
    t += dur[k]
    if k == "l06": t += 2.4                                   # plan 3D : le lion dans l'Atlas
V = {v["id"]: v for v in TL["vo"]}
S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]; M = lambda k, f: S(k) + (Ed(k) - S(k))*f
TL["duration"] = round(Ed("l20") + 2.0, 3)
cue = TL["cue"]
TL["clips"].append({"name": "atlas", "a": round(M("l06", 0.55), 3), "b": round(M("l06", 0.55) + 4.5, 3)})
def sfx(name, tt, gain=1.0): TL["sfx"].append({"name": name, "t": round(tt, 3), "gain": gain})

# repères visuels (partagés avec la page)
cue["intro"] = [0.0, M("l01", 0.55), Ed("l01") + 0.2]     # recul → demi-tour du globe → plongée sur le Maroc
cue["roarIn"] = M("l01", 0.62)
cue["maroc"] = S("l02") - 0.1
cue["range"] = [S("l03") - 0.4, M("l03", 0.9)]
cue["mane"] = S("l04") - 0.2
cue["rome"] = [S("l05") - 0.5, S("l05") + 0.6]
cue["arcs"] = [S("l05") + 0.4, Ed("l05")]
cue["shrink"] = [S("l06") - 0.3, Ed("l06")]
cue["plane"] = [S("l07") - 0.2, Ed("l07")]
cue["photo"] = M("l07", 0.62)
cue["tichka"] = [S("l08") - 0.6, S("l08") + 0.6]
cue["shot"] = M("l08", 0.62)
cue["extinct"] = S("l09") + 0.2
cue["revive"] = S("l10") + 0.5
cue["tribes"] = [S("l11"), Ed("l11")]
cue["menagerie"] = S("l12") + 0.2
cue["rabat"] = [S("l13") - 0.5, S("l13") + 0.6]
cue["zoos"] = [S("l14") - 0.4, Ed("l14")]
cue["dna"] = S("l15") + 0.2
cue["czech"] = [S("l16") - 0.6, S("l16") + 0.6]
cue["cubs"] = M("l16", 0.55)
cue["reintro"] = [S("l17") - 0.2, Ed("l17")]
cue["foot"] = [S("l18") - 0.5, M("l18", 0.6)]
cue["outro"] = S("l19") - 0.5
cue["cta"] = S("l20") + 0.2

# frise des années : [t0, t1, an0, an1, pas]
TL["ticker"] = [
    [S("l06"), Ed("l06"), 1830, 1920, 10],
    [S("l07"), S("l07") + 0.6, 1920, 1925, 1],
    [S("l08"), S("l08") + 0.8, 1925, 1942, 1],
    [S("l12") + 0.3, Ed("l12"), 1942, 2025, 10],
]
cue["tickerShow"] = [S("l06") - 0.3, Ed("l09")]

# ------------------------------------------------------------------ bruitages (positions)
C3 = TL["clips"][0]
sfx("impact", 0.02, 0.7)
sfx("whoosh", M("l01", 0.72), 0.7); sfx("impact", M("l01", 0.8), 0.8)
sfx("whoosh_long", S("l02") - 0.2, 0.7); sfx("hit", M("l02", 0.6), 0.6)
sfx("whoosh", S("l03") - 0.3, 0.7)
for i in range(5): sfx("pop", M("l03", 0.55) + i*0.22, 0.55)
sfx("whoosh", S("l04") - 0.2, 0.6); sfx("hit", M("l04", 0.8), 0.7)
sfx("whoosh_long", S("l05") - 0.4, 0.8); sfx("crowd", M("l05", 0.5), 0.55)
for i in range(8): sfx("pop", M("l05", 0.35) + i*0.12, 0.35)
sfx("whoosh", S("l06") - 0.2, 0.6)
for i in range(4): sfx("gunshot", M("l06", 0.12) + i*0.32, 0.35)
sfx("whoosh_long", C3["a"] - 0.25, 0.8); sfx("whoosh", C3["b"] - 0.3, 0.6)
sfx("plane", S("l07") - 0.2, 0.6); sfx("shutter", M("l07", 0.62), 1.0)
sfx("whoosh_long", S("l08") - 0.4, 0.8); sfx("gunshot", M("l08", 0.62), 0.85)
sfx("stamp", M("l09", 0.45), 1.0)
sfx("riser", S("l10") + 0.5, 0.7); sfx("impact", S("l10") + 0.5, 0.7)
for i in range(5): sfx("pop", M("l11", 0.35) + i*0.2, 0.5)
sfx("bell", M("l12", 0.2), 0.45)
sfx("whoosh_long", S("l13") - 0.4, 0.8); sfx("pop", M("l13", 0.3), 0.7)
sfx("whoosh_long", S("l14") - 0.3, 0.7)
for i in range(10): sfx("pop", M("l14", 0.3) + i*0.12, 0.35)
sfx("hit", M("l15", 0.4), 0.6)
sfx("whoosh_long", S("l16") - 0.4, 0.8)
for i in range(4): sfx("pop", M("l16", 0.55) + i*0.18, 0.6)
sfx("shimmer", M("l16", 0.55), 0.45)
sfx("whoosh_long", S("l17") - 0.2, 0.7); sfx("impact", M("l17", 0.8), 0.6)
sfx("whoosh", S("l18") - 0.3, 0.7); sfx("crowd", M("l18", 0.62), 0.6); sfx("impact", M("l18", 0.62), 0.6)
sfx("whoosh_long", S("l19") - 0.4, 0.7)
sfx("pop", S("l20") + 0.2, 0.7)
last = -9
for t0, t1, y0, y1, step in TL["ticker"]:
    for y in range(int(y0) + step, int(y1) + 1, step):
        tt = t0 + (t1 - t0)*(y - y0)/(y1 - y0)
        if tt - last > 0.14: sfx("tick", tt, 0.5); last = tt

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


def roar(d=2.6):
    """Rugissement : grondement grave modulé + souffle rauque, saturation douce."""
    t = T(d); n = len(t)
    f = np.interp(t, [0, .25, .9, d], [70, 150, 120, 60])
    jitter = lp(rng.standard_normal(n), 30)*25
    ph = 2*np.pi*np.cumsum(f + jitter)/SR
    tone = sum(np.sin(k*ph)/k**0.8 for k in range(1, 14))
    rasp = bp(rng.standard_normal(n), 250, 2200) * (1 + np.sin(ph))*0.6
    x = np.tanh((tone*0.5 + rasp)*2.2)
    x = bp(x, 60, 3800)
    env = np.clip(t/0.15, 0, 1)**1.2 * np.clip((d - t)/1.2, 0, 1)
    return norm(reverb(x*env, 1.8, 0.3), 0.85)
def plane(d=3.2):
    t = T(d); f = 95*(1 + 0.06*np.interp(t, [0, d/2, d], [1, 0, -1]))      # léger effet Doppler
    ph = 2*np.pi*np.cumsum(f)/SR
    buzz = np.sign(np.sin(ph))*0.5 + np.sin(2*ph)*0.3
    buzz = lp(buzz + 0.2*rng.standard_normal(len(t)), 1400)
    env = np.sin(np.pi*np.clip(t/d, 0, 1))**1.5
    return norm(buzz*env, 0.45)
def shutter():
    t = T(0.35); x = np.zeros(len(t))
    for o in (0, 0.09):
        i = int(o*SR); m = int(0.03*SR); x[i:i+m] += hp(rng.standard_normal(m), 2000)*np.exp(-np.arange(m)/SR*120)
    return norm(x, 0.7)
def gunshot():
    t = T(2.2); crack = hp(rng.standard_normal(len(t)), 800)*np.exp(-t*45)
    boom = lp(rng.standard_normal(len(t)), 300)*np.exp(-t*9)
    return norm(reverb(crack + 2*boom, 2.6, 0.45), 0.9)
def crowd(d=3.0):
    t = T(d); n = len(t); x = np.zeros(n)
    for f0 in (350, 520, 700, 950):
        x += bp(rng.standard_normal(n), f0*0.8, f0*1.25)*(1 + 0.3*np.sin(2*np.pi*(2 + f0/400)*t))
    env = np.clip(t/0.8, 0, 1)*np.clip((d - t)/1.0, 0, 1)
    return norm(reverb(x*env, 1.5, 0.4), 0.4)

BANK = {"roar": roar(), "whoosh": whoosh(), "whoosh_long": whoosh(1.6, 150, 2500), "impact": impact(), "hit": hit(),
        "stamp": stamp(), "pop": pop(), "tick": tick(), "bell": bell(), "shimmer": shimmer(), "riser": riser(),
        "plane": plane(), "shutter": shutter(), "gunshot": gunshot(), "crowd": crowd()}
fx = np.zeros(N, np.float32)
import subprocess
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "0.0", "-t", "1.9", "-i", "assets/rugissement.mp3", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
rg = np.frombuffer(raw, np.float32).copy(); rg *= np.clip((1.9 - np.arange(len(rg))/SR)/0.3, 0, 1); fx[:len(rg)] += norm(rg, 0.95)
for s in TL["sfx"]:
    x = BANK[s["name"]]*s["gain"]; i = int(s["t"]*SR)
    if s["name"] == "riser": i -= len(x)
    i = max(i, 0); fx[i:i+len(x)] += x[:N-i]
sf.write("sfx.wav", fx, SR)

# ------------------------------------------------------------------ musique : mode hijaz sur ré, 92 BPM
bpm = 92; beat = 60/bpm; bar = 4*beat
D = 73.42
HIJAZ = [0, 1, 4, 5, 7, 8, 10, 12]                     # ré mib fa# sol la sib do ré
MOTIFS = [[0, 1, 4, 5, 4, 1, 0, -1], [7, 5, 4, 5, 4, 1, 0, 1], [0, 4, 5, 7, 8, 7, 5, 4], [5, 4, 1, 0, 1, 0, -1, 0]]
def section(x):
    if x < 1.3:      return dict(drone=0, oud=0, drum=0)
    if x < S("l03"):  return dict(drone=.8, oud=.6, drum=1.)
    if x < S("l07"):  return dict(drone=.8, oud=.8, drum=.8)
    if x < S("l10"):  return dict(drone=.7, oud=.3, drum=0)
    if x < S("l14"):  return dict(drone=.9, oud=1., drum=1.)
    if x < S("l19"):  return dict(drone=.9, oud=.8, drum=.9)
    return dict(drone=1., oud=1., drum=1.)
def note(i):                                              # indice dans la gamme (négatif = octave en dessous)
    o, k = divmod(i, 7); return D*4*2**((HIJAZ[k] + 12*o)/12)
mus = np.zeros(N)
for b in range(int(TL["duration"]/bar) + 1):
    t0 = b*bar; sec = section(t0 + 0.01); i0 = int(t0*SR)
    n = int(bar*SR) + int(0.6*SR); tl = np.arange(n)/SR
    env = np.clip(tl/0.5, 0, 1)*np.clip((bar + 0.6 - tl)/0.6, 0, 1)
    drone = (np.sin(2*np.pi*D*tl) + 0.6*np.sin(2*np.pi*D*1.5*tl) + 0.3*np.sin(2*np.pi*D*2*tl))*env*0.12*sec["drone"]
    seg = drone.copy()
    if sec["oud"]:
        for k, s in enumerate(MOTIFS[b % 4]):
            st = int(k*beat/2*SR); f = note(s); tn = np.arange(int(0.9*SR))/SR
            bend = 1 + 0.01*np.exp(-tn*30)                                # attaque légèrement glissée (oud)
            ph = 2*np.pi*np.cumsum(f*bend)/SR
            pl = sum(np.sin(h*ph)/h*np.exp(-tn*(4 + 3*h)) for h in range(1, 7))
            e = min(len(pl), n - st); seg[st:st+e] += pl[:e]*0.06*sec["oud"]
    if sec["drum"]:
        for pos, kind in [(0, "doum"), (1.5, "tek"), (2, "doum"), (3, "tek"), (3.5, "tek")]:
            st = int(pos*beat*SR); tn = np.arange(int(0.4*SR))/SR
            if kind == "doum": h = np.sin(2*np.pi*np.cumsum(65 + 60*np.exp(-tn*25))/SR)*np.exp(-tn*8)*0.32
            else: h = hp(rng.standard_normal(len(tn)), 2500)*np.exp(-tn*55)*0.12
            seg[st:st+len(h)] += h*sec["drum"]
    e = min(n, N - i0)
    if e > 0: mus[i0:i0+e] += seg[:e]
mus = reverb(mus, 2.2, 0.3)[:N]
mus *= np.clip(tt/1.5, 0, 1)*np.clip((TL["duration"] - tt)/2.0, 0, 1)
sf.write("music.wav", norm(mus, 0.6), SR)
print(json.dumps({"duration": TL["duration"]}))
