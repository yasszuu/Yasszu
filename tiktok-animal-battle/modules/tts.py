"""
Genere les fichiers audio de voix off avec edge-tts (gratuit, aucune cle API).
Met en cache les fichiers generes pour ne pas regenerer a chaque lancement.
Peut aussi renvoyer les instants (en secondes) ou chaque mot est prononce,
pour synchroniser des elements visuels sur la voix (ex. faire apparaitre un
animal au moment ou son nom est dit).
"""
import os
import json
import hashlib
import asyncio
import edge_tts

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache", "audio")


def _cache_key(text: str, voice: str, rate: str, volume: str, pitch: str) -> str:
    return hashlib.md5(f"{text}|{voice}|{rate}|{volume}|{pitch}".encode("utf-8")).hexdigest()


def _cache_path(text: str, voice: str, rate: str, volume: str, pitch: str) -> str:
    return os.path.join(CACHE_DIR, f"{_cache_key(text, voice, rate, volume, pitch)}.mp3")


async def _generate(text: str, voice: str, rate: str, volume: str, pitch: str, out_path: str):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume, pitch=pitch)
    await communicate.save(out_path)


async def _generate_with_timings(text: str, voice: str, rate: str, volume: str, pitch: str, out_path: str):
    """Comme _generate, mais capture aussi les instants ou chaque mot est prononce."""
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume, pitch=pitch)
    boundaries = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                boundaries.append({
                    "text": chunk["text"],
                    "offset": chunk["offset"] / 10_000_000,  # 100ns -> secondes
                    "duration": chunk["duration"] / 10_000_000,
                })
    return boundaries


def get_tts_audio(text: str, voice: str = "fr-FR-HenriNeural", rate: str = "+0%",
                   volume: str = "+0%", pitch: str = "+0Hz", force_refresh: bool = False) -> str:
    """
    Renvoie le chemin local vers le mp3 de la phrase donnee.
    Genere via edge-tts et met en cache si besoin.
    'rate' et 'volume' sont des pourcentages relatifs a la voix normale,
    ex. "+100%" = deux fois plus rapide / deux fois plus fort.
    'pitch' ajuste la hauteur de la voix, ex. "+20Hz" (plus aigu) ou
    "-20Hz" (plus grave).
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(text, voice, rate, volume, pitch)

    if os.path.exists(path) and not force_refresh:
        return path

    asyncio.run(_generate(text, voice, rate, volume, pitch, path))
    return path


def get_tts_audio_with_timings(text: str, voice: str = "fr-FR-HenriNeural", rate: str = "+0%",
                                volume: str = "+0%", pitch: str = "+0Hz",
                                force_refresh: bool = False):
    """
    Comme get_tts_audio, mais renvoie aussi la liste des mots avec leur
    instant de prononciation : [{"text":..., "offset":..., "duration":...}, ...]
    (offset/duration en secondes). Les timings sont mis en cache en JSON a
    cote du mp3.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = _cache_key(text, voice, rate, volume, pitch)
    audio_path = os.path.join(CACHE_DIR, f"{key}.mp3")
    timings_path = os.path.join(CACHE_DIR, f"{key}.timings.json")

    if os.path.exists(audio_path) and os.path.exists(timings_path) and not force_refresh:
        with open(timings_path, "r", encoding="utf-8") as f:
            return audio_path, json.load(f)

    boundaries = asyncio.run(_generate_with_timings(text, voice, rate, volume, pitch, audio_path))
    with open(timings_path, "w", encoding="utf-8") as f:
        json.dump(boundaries, f, ensure_ascii=False)
    return audio_path, boundaries


def list_available_french_voices():
    """Utilitaire pour lister les voix francaises disponibles (a lancer manuellement)."""
    async def _list():
        voices = await edge_tts.list_voices()
        return [v for v in voices if v["Locale"].startswith("fr-")]

    return asyncio.run(_list())


if __name__ == "__main__":
    for v in list_available_french_voices():
        print(v["ShortName"], "-", v["Gender"])
