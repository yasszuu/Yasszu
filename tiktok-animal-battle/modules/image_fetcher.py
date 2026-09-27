"""
Recupere des images libres de droits (Wikimedia Commons) pour chaque animal,
les met en cache localement, et les recadre en portrait pret a l'emploi.

Strategie en deux temps pour maximiser les chances d'avoir une VRAIE photo
de l'animal (pas un fossile, un squelette, une salle de musee vide...) :
1) Chercher la categorie Wikimedia correspondant a l'animal (les categories
   sont des collections organisees par des humains, donc beaucoup plus
   fiables que la recherche plein texte) et piocher une image dedans.
2) Si aucune categorie exploitable n'est trouvee, se rabattre sur la
   recherche plein texte classique (avec le meme filtrage).
Dans les deux cas, les resultats visiblement hors-sujet (cartes, schemas,
logos, specimens de musee, fossiles, jouets...) sont ecartes.
"""
import os
import re
import time
import hashlib
import unicodedata
import requests
from PIL import Image, ImageOps

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "AnimalBattleVideoBot/1.0 (usage personnel non commercial)"}

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache", "images")
BANK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "banque_animaux")
BANK_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

MAX_RETRIES = 5

# Titres de fichiers Commons contenant l'un de ces mots -> tres probablement
# PAS une photo "nature" representative de l'animal vivant (carte, schema,
# logo, specimen de musee, fossile, os, salle d'exposition vide, jouet...).
BLOCKED_TITLE_WORDS = (
    "map", "distribution", "diagram", "skull", "skeleton", "logo", "icon",
    "flag", "drawing", "illustration", "illustrated", "sign ", "stamp",
    "coin", "postcard", "screenshot", "cartoon", "chart", "graph",
    "clipart", "clip art", "silhouette", "coat of arms", "emblem",
    "poster", "vector", "line art", "taxonomy", "anatomy", "cladogram",
    "phylogen", "location map", "range map", "comparison", "infographic",
    "statue", "sculpture", "painting", "mascot", "costume", "toy",
    "plush", "cake", "tattoo", "coloring page", "coloring book",
    "specimen", "museum", "fossil", "taxidermy", "mounted", "preserved",
    "exhibit", "diorama", "replica", "model", "figurine", "keychain",
    "sticker", "emoji", "meme", "video game", "aquarium logo", "menu",
    "dissection", "necropsy", "cross section", "jar", "herbarium",
    "book cover", "album cover", "advertisement", "advert", "label",
    "packaging", "recipe", "dish", "cooked", "fried", "grilled", "plate of",
    "jaw", "jawbone", "teeth", "tooth", "bone", "cast", "reconstruction",
    "interior", "empty tank", "tank interior", "viewing area",
    "observation deck", "signage", "plaque", "information board",
    "gallery interior", "display case", "release event", "conference",
    "meeting", "ceremony", "ticket", "brochure", "leaflet",
)


def _request_with_retry(method, url, **kwargs):
    """
    Comme requests.get/post, mais reessaie automatiquement en cas de
    limitation (429) ou d'erreur serveur temporaire (5xx), avec un delai
    croissant entre chaque tentative (et respecte l'en-tete Retry-After
    quand Wikimedia le fournit).
    """
    delay = 2
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.request(method, url, timeout=30, **kwargs)
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == MAX_RETRIES:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else delay
            print(f"     (limite Wikimedia atteinte, nouvelle tentative dans {wait:.0f}s...)")
            time.sleep(wait)
            delay *= 2
            continue
        response.raise_for_status()
        return response
    raise RuntimeError("Nombre maximum de tentatives depasse")


def _cache_path(search_term: str) -> str:
    key = hashlib.md5(search_term.lower().encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.jpg")


def _looks_like_photo(title: str) -> bool:
    """Ecarte les fichiers dont le titre laisse penser que ce n'est pas une photo de l'animal."""
    lower = title.lower()
    return not any(word in lower for word in BLOCKED_TITLE_WORDS)


def _title_relevance(title: str, search_term: str) -> int:
    """Nombre de mots de la recherche retrouves dans le titre du fichier (pertinence)."""
    title_words = set(re.findall(r"[a-zA-Z]+", title.lower()))
    search_words = [w for w in re.findall(r"[a-zA-Z]+", search_term.lower()) if len(w) > 2]
    if not search_words:
        return 0
    return sum(1 for w in search_words if w in title_words)


def _filter_imageinfo_pages(pages, search_term: str):
    """Convertit les 'pages' d'une reponse Wikimedia en candidats filtres/notes."""
    candidates = []
    for page in pages.values():
        infos = page.get("imageinfo", [])
        if not infos:
            continue
        info = infos[0]
        mime = info.get("mime", "")
        width = info.get("width", 0)
        height = info.get("height", 0)
        title = page.get("title", "")
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        if width < 500 or height < 500:
            continue
        aspect = width / height if height else 0
        if aspect < 0.35 or aspect > 3.2:  # ecarte les formats tres etires (bannieres, frises...)
            continue
        if not _looks_like_photo(title):
            continue
        url = info.get("thumburl") or info.get("url")
        relevance = _title_relevance(title, search_term)
        candidates.append((relevance, width * height, url))
    return candidates


def _find_category_title(search_term: str):
    """Cherche la categorie Wikimedia la plus pertinente pour ce terme (ou None)."""
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": search_term,
        "srnamespace": 14,  # namespace "Category:"
        "srlimit": 1,
    }
    r = _request_with_retry("GET", COMMONS_API, params=params, headers=HEADERS)
    results = r.json().get("query", {}).get("search", [])
    if not results:
        return None
    return results[0]["title"]  # ex. "Category:Carcharhinus leucas"


def _search_in_category(category_title: str, search_term: str, limit: int = 40):
    """Renvoie les candidats trouves dans une categorie Wikimedia (fichiers uniquement)."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "categorymembers",
        "gcmtitle": category_title,
        "gcmtype": "file",
        "gcmlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": 1200,
    }
    r = _request_with_retry("GET", COMMONS_API, params=params, headers=HEADERS)
    pages = r.json().get("query", {}).get("pages", {})
    return _filter_imageinfo_pages(pages, search_term)


def _raw_commons_search(query: str, limit: int = 20):
    """Un seul appel de recherche plein texte Wikimedia (repli si la categorie ne donne rien)."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6,  # namespace "File:"
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": 1200,
    }
    r = _request_with_retry("GET", COMMONS_API, params=params, headers=HEADERS)
    pages = r.json().get("query", {}).get("pages", {})
    return _filter_imageinfo_pages(pages, query)


GENERIC_SUFFIX_WORDS = {
    "animal", "bird", "cat", "fish", "insect", "reptile", "snake",
    "lizard", "spider", "rodent",
}


def _best_from(candidates):
    """Trie (pertinence puis taille) et renvoie l'URL du meilleur candidat pertinent."""
    relevant = [c for c in candidates if c[0] > 0]
    pool = relevant if relevant else candidates
    pool.sort(reverse=True)
    return pool[0][2]


def _search_commons_image_url(search_term: str) -> str:
    """
    Cherche une image sur Wikimedia Commons et renvoie l'URL du fichier le
    plus pertinent. Priorite a la categorie de l'animal (beaucoup plus
    fiable qu'une recherche plein texte generale), avec repli sur la
    recherche classique si aucune categorie exploitable n'est trouvee.
    """
    category_title = _find_category_title(search_term)
    if category_title:
        cat_candidates = _search_in_category(category_title, search_term)
        if cat_candidates:
            return _best_from(cat_candidates)

    candidates = _raw_commons_search(search_term)

    if not candidates:
        words = search_term.split()
        if len(words) > 1 and words[-1].lower() in GENERIC_SUFFIX_WORDS:
            simplified = " ".join(words[:-1])
            candidates = _raw_commons_search(simplified)

    if not candidates:
        raise RuntimeError(f"Aucune image exploitable trouvee pour '{search_term}'")

    return _best_from(candidates)


def _slugify(name: str) -> str:
    """Normalise un nom pour la comparaison (accents/espaces/majuscules/tirets ignores)."""
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", normalized.lower())


def find_local_animal_image(animal_name: str):
    """
    Cherche une image fournie par l'utilisateur dans banque_animaux/ dont le
    nom de fichier correspond a 'animal_name' (comparaison insensible aux
    accents/espaces/majuscules). Renvoie le chemin trouve, ou None.
    """
    if not os.path.isdir(BANK_DIR):
        return None
    target = _slugify(animal_name)
    if not target:
        return None
    for f in os.listdir(BANK_DIR):
        base, ext = os.path.splitext(f)
        if ext.lower() in BANK_EXTENSIONS and _slugify(base) == target:
            return os.path.join(BANK_DIR, f)
    return None


def get_animal_image_smart(animal_name: str, search_term: str, force_refresh: bool = False) -> str:
    """
    Renvoie une image pour cet animal : d'abord la banque locale
    (banque_animaux/) si l'utilisateur en a fourni une, sinon la recherche
    Wikimedia habituelle.
    """
    local = find_local_animal_image(animal_name)
    if local:
        return local
    return get_animal_image(search_term, force_refresh=force_refresh)


def get_animal_image(search_term: str, force_refresh: bool = False) -> str:
    """
    Renvoie le chemin local (cache) vers une image de l'animal recherche.
    Telecharge et met en cache si besoin.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(search_term)

    if os.path.exists(path) and not force_refresh:
        return path

    url = _search_commons_image_url(search_term)
    r = _request_with_retry("GET", url, headers=HEADERS)

    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(r.content)

    # Normalise en JPEG RGB pour eviter les soucis de mode/format plus tard
    img = Image.open(tmp_path).convert("RGB")
    img = ImageOps.exif_transpose(img)
    img.save(path, "JPEG", quality=92)
    os.remove(tmp_path)

    # Petite pause entre chaque animal pour rester sous la limite de Wikimedia
    time.sleep(1.5)

    return path


def crop_to_portrait(image_path: str, out_path: str, width: int, height: int):
    """Recadre/centre une image pour remplir exactement width x height (crop 'cover')."""
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (width, height), method=Image.LANCZOS, centering=(0.5, 0.4))
    img.save(out_path, "JPEG", quality=92)
    return out_path
