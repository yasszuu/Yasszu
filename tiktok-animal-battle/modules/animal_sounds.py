"""
Cherche un court extrait sonore de l'animal (cri/chant/vocalisation) sur
Wikimedia Commons -- en "best effort" : la couverture est tres inegale
selon les especes (tres bonne pour beaucoup d'oiseaux, quasi inexistante
pour la plupart des insectes/poissons). Si rien d'exploitable n'est
trouve, renvoie None sans jamais faire planter la generation.
"""
import os
import hashlib
from modules.image_fetcher import _request_with_retry, HEADERS, COMMONS_API

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache", "sounds")

_EXT_BY_MIME = {
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/flac": ".flac",
}


def _cache_key(search_term: str) -> str:
    return hashlib.md5(search_term.lower().encode("utf-8")).hexdigest()


def _find_cached(search_term: str):
    key = _cache_key(search_term)
    if not os.path.isdir(CACHE_DIR):
        return None
    for f in os.listdir(CACHE_DIR):
        if f.startswith(key):
            return os.path.join(CACHE_DIR, f)
    return None


def _search_commons_sound(search_term: str):
    """Cherche un fichier audio pertinent sur Wikimedia Commons. Renvoie (url, extension) ou (None, None)."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{search_term} sound call OR song OR cry filetype:audio",
        "gsrnamespace": 6,
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|mime",
    }
    r = _request_with_retry("GET", COMMONS_API, params=params, headers=HEADERS)
    data = r.json()
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        infos = page.get("imageinfo", [])
        if not infos:
            continue
        info = infos[0]
        mime = info.get("mime", "")
        ext = _EXT_BY_MIME.get(mime)
        if ext:
            return info.get("url"), ext
    return None, None


def get_animal_sound(search_term: str):
    """
    Renvoie le chemin local (cache) vers un court son de cet animal, ou
    None si aucun n'a ete trouve/n'est exploitable. Ne leve jamais
    d'exception : une recherche/telechargement qui echoue est simplement
    traitee comme "pas de son disponible".
    """
    cached = _find_cached(search_term)
    if cached:
        return cached

    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        url, ext = _search_commons_sound(search_term)
        if not url:
            return None
        r = _request_with_retry("GET", url, headers=HEADERS)
        path = os.path.join(CACHE_DIR, _cache_key(search_term) + ext)
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    except Exception as e:
        print(f"     (pas de son trouve pour cet animal ({e}), on continue sans)")
        return None
