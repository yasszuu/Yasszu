"""Short « Quel animal tue le plus d'humains ? » : voix découpée + cris + bruitages + musique -> timeline.json, vo.wav, sfx.wav, music.wav"""
import json, subprocess, numpy as np, soundfile as sf
SR = 44100
def load(p, ss=None, t=None):
    cmd = ["ffmpeg", "-loglevel", "error"] + (["-ss", str(ss), "-t", str(t)] if ss is not None else []) + ["-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()
x = load("assets/voix.mp3"); B = json.load(open("vo_bounds.json")); SC = json.load(open("script.json"))
GAP = {"t1": 1.3, "t2": 0.8, "t3": 0.8, "t4": 0.8, "t5": 0.8, "t6": 0.9, "t7": 0.5}
TL = {"vo": [], "sfx": [], "cries": []}; t = 0; segs = []
for (a, b), (k, _, cap) in zip(B, SC):
    s = x[a:b]; nz = np.where(np.abs(s) > 0.01)[0]; s = s[max(nz[0] - 300, 0): nz[-1] + 2000]
    t += GAP[k]; TL["vo"].append({"id": k, "start": round(t, 3), "end": round(t + len(s)/SR, 3), "cap": cap}); segs.append((t, s)); t += len(s)/SR
TL["duration"] = round(t + 1.4, 3); N = int(TL["duration"]*SR) + SR
vo = np.zeros(N, np.float32)
for t0, s in segs: i = int(t0*SR); vo[i:i+len(s)] += s
sf.write("vo.wav", vo, SR)
V = {v["id"]: v for v in TL["vo"]}; S = lambda k: V[k]["start"]; Ed = lambda k: V[k]["end"]; M = lambda k, f: S(k) + (Ed(k) - S(k))*f
def sfx(n, tt, g=1.0): TL["sfx"].append({"name": n, "t": round(tt, 3), "gain": g})
sfx("impact", 0.02, 0.8); sfx("woosh", 0.5, 0.8); sfx("impact", M("t1", 0.75), 0.8)
CR = {"t2": ("assets/cri-loup.mp3", 0.1, 1.3), "t3": ("assets/rugissement.mp3", 0.0, 1.3), "t4": ("assets/cri-hippo.wav", 0.0, 1.2), "t5": ("assets/aboiement.mp3", 0.0, 1.1), "t6": ("assets/bzz.wav", 0.0, 1.5)}
for k in ("t2", "t3", "t4", "t5", "t6"):
    TL["cries"].append({"id": k, "t": round(S(k) - 0.75, 3)}); sfx("woosh", S(k) - 0.8, 0.6)
sfx("impact", M("t3", 0.62), 0.8); sfx("impact", M("t4", 0.45), 0.8); sfx("impact", M("t5", 0.6), 0.9); sfx("impact", M("t6", 0.42), 1.0)
sfx("pop", M("t5", 0.88), 0.8); sfx("pop", M("t6", 0.86), 0.8); sfx("pop", S("t7") + 0.1, 0.8)
for f in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7): sfx("pop", M("t4", 0.62) + (f - 0.2)*1.2, 0.35)
json.dump(TL, open("timeline.json", "w"), ensure_ascii=False, indent=1)
fx = np.zeros(N, np.float32)
BANK = {k: load(f"assets/s_{k}.wav") for k in ("woosh", "pop", "impact", "tick")}
for s in TL["sfx"]:
    a = BANK[s["name"]]*s["gain"]; i = max(int(s["t"]*SR), 0); fx[i:i+len(a)] += a[:N-i]
for c in TL["cries"]:
    p, ss, d = CR[c["id"]]; a = load(p, ss, d); a = a/np.abs(a).max()*0.85; n = len(a); a *= np.clip((d - np.arange(n)/SR)/0.35, 0, 1)
    i = int(c["t"]*SR); fx[i:i+n] += a[:N-i]
sf.write("sfx.wav", fx, SR)
m = load("../moust2/music.wav"); m = np.concatenate([m, m])[:N]; tt = np.arange(N)/SR
m *= np.clip(tt/1.2, 0, 1)*np.clip((TL["duration"] - tt)/1.5, 0, 1); sf.write("music.wav", m, SR)
print(TL["duration"], [(v["id"], v["start"], v["end"]) for v in TL["vo"]])
