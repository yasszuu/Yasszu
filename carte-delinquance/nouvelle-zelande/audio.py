"""Nouvelle-Zélande, 22 moutons par habitant : timeline + bruitages + musique."""
import sys; sys.path.insert(0, "../shorts"); from shortaudio import build
GAP = {"n01": 1.5, "n02": 0.4, "n03": 0.45, "n04": 0.45, "n05": 0.45}
def cues(S, Ed, M, sfx, TL):
    sfx("whoosh", 1.3, 0.9); sfx("impact", M("n01", 0.15), 0.6)
    for k in range(22): sfx("pop", M("n01", 0.45) + k*0.06, 0.35)                 # 22 moutons qui poppent
    sfx("impact", M("n01", 0.92), 0.9)
    sfx("whoosh", S("n02") - 0.25, 0.8); sfx("pop", M("n02", 0.05), 0.8)
    TL["ticker"] = [[M("n02", 0.12), M("n02", 0.12) + 0.01, 1982, 1982, 1]]
    for k in range(3): sfx("pop", M("n02", 0.3) + k*0.14, 0.8)                    # 3 millions d'humains
    for k in range(24): sfx("pop", M("n02", 0.62) + k*0.045, 0.3)                 # 70 millions de moutons
    sfx("impact", M("n02", 0.95), 0.8)
    sfx("whoosh", S("n03") - 0.3, 0.9); sfx("shimmer", M("n03", 0.45), 0.5)
    for k in range(10): sfx("tick", M("n03", 0.45) + k*0.09, 0.5)                 # pièces
    sfx("hit", M("n03", 0.8), 0.7)
    TL["ticker"].append([S("n04") + 0.05, S("n04") + 1.0, 1982, 2024, 2])
    for k in range(21): sfx("tick", S("n04") + 0.05 + k*0.95/21, 0.4)
    sfx("whoosh", S("n04") + 0.2, 0.8); sfx("down", M("n04", 0.45), 0.5); sfx("pop", M("n04", 0.78), 0.9)
    sfx("whoosh", S("n05") - 0.2, 0.7); sfx("pop", S("n05") + 0.1, 0.8); sfx("pop", M("n05", 0.6), 0.8)
def sec(x): return dict(pad=0, pluck=0, drum=0) if x < 1.3 else dict(pad=.8, pluck=1., drum=1.)
TL = build(GAP, 1.6, cues, "assets/belement.mp3", 1.5, 0.9, extra_cry=[], music_sec=sec, bpm=112, minor=False)
print(TL["duration"], [(v["id"], v["start"], v["end"]) for v in TL["vo"]])
