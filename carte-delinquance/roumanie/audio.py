"""Roumanie, le pays des ours : timeline + bruitages + musique."""
import sys; sys.path.insert(0, "../shorts"); from shortaudio import build
GAP = {"r01": 1.6, "r02": 0.45, "r03": 0.45, "r04": 0.5, "r05": 0.5}
def cues(S, Ed, M, sfx, TL):
    sfx("whoosh", 1.35, 0.9); sfx("impact", S("r01") + 0.1, 0.6)
    for k in range(16): sfx("tick", M("r01", 0.2) + k*0.07, 0.45)                 # compteur 8 000
    sfx("impact", M("r01", 0.55), 0.9); sfx("hit", M("r01", 0.86), 1.0)
    sfx("whoosh", S("r02") - 0.3, 1.0); sfx("pop", M("r02", 0.05), 0.8); sfx("shimmer", M("r02", 0.18), 0.4)
    for k in range(20): sfx("pop", M("r02", 0.25) + k*0.04, 0.3)
    sfx("pop", M("r02", 0.55), 0.8); sfx("impact", M("r02", 0.72), 0.9)
    sfx("whoosh", S("r03") - 0.3, 0.9)
    for k in range(6): sfx("pop", M("r03", 0.25) + k*0.18, 0.5)
    sfx("hit", M("r03", 0.8), 0.7)
    sfx("down", S("r04") - 0.2, 0.5); sfx("whoosh", M("r04", 0.7), 0.6); sfx("whoosh", M("r04", 0.88), 0.6)
    sfx("riser", Ed("r04") + 0.35, 0.5); sfx("impact", Ed("r04") + 0.35, 0.8)
    sfx("pop", S("r05") + 0.1, 0.8); sfx("pop", M("r05", 0.6), 0.8)
def sec(x): return dict(pad=0, pluck=0, drum=0) if x < 1.4 else dict(pad=1., pluck=.7, drum=1.)
TL = build(GAP, 1.8, cues, "assets/grognement-ours.mp3", 1.7, 0.9, music_sec=sec, bpm=92)
print(TL["duration"], [(v["id"], v["start"], v["end"]) for v in TL["vo"]])
