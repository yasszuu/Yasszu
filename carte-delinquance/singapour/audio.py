"""Singapour, la ville du lion… sans lion : timeline + bruitages + musique."""
import sys; sys.path.insert(0, "../shorts"); from shortaudio import build
GAP = {"s01": 1.6, "s02": 0.3, "s03": 0.45, "s04": 0.35, "s05": 0.45, "s06": 0.45, "s07": 0.5, "s08": 0.35}
def cues(S, Ed, M, sfx, TL):
    sfx("whoosh", 1.35, 0.9); sfx("impact", S("s01") + 0.15, 0.7)
    sfx("pop", M("s01", 0.62), 0.8); sfx("pop", M("s01", 0.78), 0.8); sfx("impact", M("s01", 0.9), 0.9)    # SINGA / PURA
    sfx("hit", M("s02", 0.55), 1.0); sfx("down", M("s02", 0.6), 0.5)                                       # 0 lion
    sfx("whoosh", S("s03") - 0.25, 0.8); sfx("pop", M("s03", 0.5), 0.8)
    TL["ticker"] = [[S("s04") + 0.05, S("s04") + 1.1, 2025, 1299, 1]]
    for k in range(18): sfx("tick", S("s04") + 0.05 + k*1.05/18, 0.45)
    sfx("whoosh", M("s04", 0.3), 0.6); sfx("pop", M("s04", 0.62), 0.8); sfx("hit", M("s04", 0.9), 0.8)
    sfx("whoosh", S("s05") - 0.3, 1.0); sfx("pop", M("s05", 0.35), 0.8); sfx("impact", Ed("s05") - 0.2, 0.8)
    sfx("whoosh", S("s06") - 0.3, 0.9); sfx("riser", M("s06", 0.55), 0.6); sfx("impact", M("s06", 0.62), 1.0)
    TL["ticker"].append([S("s07") + 0.05, S("s07") + 0.9, 1299, 2025, 1])
    for k in range(14): sfx("tick", S("s07") + 0.05 + k*0.85/14, 0.45)
    sfx("whoosh", M("s07", 0.4), 0.8); sfx("pop", M("s07", 0.75), 0.9); sfx("shimmer", M("s07", 0.8), 0.4)
    sfx("pop", S("s08") + 0.05, 0.8); sfx("pop", S("s08") + 0.45, 0.8)
def sec(x): return dict(pad=0, pluck=0, drum=0) if x < 1.4 else dict(pad=.9, pluck=.8, drum=1.)
TL = build(GAP, 1.6, cues, "assets/rugissement.mp3", 1.7, 0.9, music_sec=sec, bpm=100)
print(TL["duration"], [(v["id"], v["start"], v["end"]) for v in TL["vo"]])
