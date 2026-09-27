"""
Genere automatiquement une video "Qui remporte la bagarre entre X et X ?"
en piochant aleatoirement des rounds dans config.json (rounds_pool). Par
defaut, le nombre de rounds s'adapte automatiquement pour viser une duree
totale cible (~1min20 a 2min, reglable via target_duration_min/max dans
config.json).

Usage (PowerShell) :
    python main.py
    python main.py --config config.json
    python main.py --rounds 8                # force un nombre de rounds precis (ignore la duree cible)
    python main.py --refresh-images           # force le re-telechargement des images
    python main.py --refresh-audio             # force la regeneration de la voix off
    python main.py --seed 42                   # rejouer exactement la meme selection aleatoire
"""
import argparse
import json
import os
import re
import random
import sys

# Sur certains PC d'entreprise (Zscaler, proxy SSL, etc.), Python ne fait pas
# confiance aux certificats installes par l'IT dans le magasin Windows.
# "truststore" force Python a utiliser directement le magasin de certificats
# du systeme (celui que Zscaler alimente deja), ce qui resout les erreurs
# CERTIFICATE_VERIFY_FAILED sans avoir a desactiver la verification SSL.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from modules.video_builder import build_full_video


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def next_output_path(output_dir: str, basename: str = "video") -> str:
    """
    Renvoie un chemin de sortie qui ne s'ecrase jamais : video_1.mp4,
    video_2.mp4, etc. en fonction de ce qui existe deja dans output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    pattern = re.compile(rf"^{re.escape(basename)}_(\d+)\.mp4$")
    max_n = 0
    for f in os.listdir(output_dir):
        m = pattern.match(f)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return os.path.join(output_dir, f"{basename}_{max_n + 1}.mp4")


def main():
    parser = argparse.ArgumentParser(description="Generateur de video 'combat d'animaux' pour TikTok")
    parser.add_argument("--config", default="config.json", help="Chemin vers le fichier config.json")
    parser.add_argument("--rounds", type=int, default=None,
                         help="Force un nombre precis de rounds (ignore la duree cible)")
    parser.add_argument("--seed", type=int, default=None,
                         help="Graine aleatoire pour rejouer exactement la meme selection de rounds")
    parser.add_argument("--refresh-images", action="store_true",
                         help="Force le re-telechargement des images meme si elles sont en cache")
    parser.add_argument("--refresh-audio", action="store_true",
                         help="Force la regeneration des fichiers audio meme s'ils sont en cache")
    args = parser.parse_args()

    if args.refresh_images:
        import modules.image_fetcher as image_fetcher
        _orig = image_fetcher.get_animal_image
        image_fetcher.get_animal_image = lambda term, force_refresh=False: _orig(term, force_refresh=True)

    if args.refresh_audio:
        import modules.tts as tts
        _orig_tts = tts.get_tts_audio
        tts.get_tts_audio = lambda text, voice="fr-FR-HenriNeural", rate="+0%", volume="+0%", \
            pitch="+0Hz", force_refresh=False: \
            _orig_tts(text, voice, rate, volume, pitch, force_refresh=True)
        _orig_tts_timings = tts.get_tts_audio_with_timings
        tts.get_tts_audio_with_timings = lambda text, voice="fr-FR-HenriNeural", rate="+0%", \
            volume="+0%", pitch="+0Hz", force_refresh=False: \
            _orig_tts_timings(text, voice, rate, volume, pitch, force_refresh=True)

    config = load_config(args.config)

    if args.seed is not None:
        random.seed(args.seed)

    pool = list(config["rounds_pool"])
    random.shuffle(pool)

    if args.rounds is not None:
        # Mode "nombre de rounds impose" : on fournit exactement ce nombre
        # de candidats et on desactive la logique de duree cible (elle ne
        # s'arretera jamais avant d'avoir epuise la liste).
        count = min(args.rounds, len(pool))
        config["rounds"] = pool[:count]
        config["video"]["target_duration_min"] = 10 ** 9
        print(f"{count} rounds (nombre impose) parmi {len(pool)} combats disponibles :")
    else:
        # Mode par defaut : on fournit tout le pool (melange), et
        # build_full_video s'arretera de lui-meme des que la duree cible
        # (target_duration_min) est atteinte.
        config["rounds"] = pool
        dmin = config["video"].get("target_duration_min", 80)
        dmax = config["video"].get("target_duration_max", 120)
        print(f"Duree cible : {dmin:.0f}-{dmax:.0f}s (le nombre de rounds sera adapte automatiquement)")

    output_dir = config["video"].get("output_dir", "output")
    output_basename = config["video"].get("output_basename", "video")
    config["video"]["output_file"] = next_output_path(output_dir, output_basename)

    try:
        out_path = build_full_video(config)
    except Exception as e:
        print(f"\nErreur pendant la generation : {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nVideo prete : {out_path}")


if __name__ == "__main__":
    main()
