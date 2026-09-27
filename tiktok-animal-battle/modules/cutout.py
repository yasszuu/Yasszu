"""
Detoure un animal de sa photo (fond supprime, PNG transparent) grace a
rembg (IA locale, aucune cle API). Le modele est fourni directement dans le
projet (dossier rembg_home/) pour qu'aucun telechargement ne soit necessaire
au premier lancement.

Si rembg n'est pas installe ou echoue pour une raison quelconque, les
fonctions renvoient None : l'appelant doit alors se rabattre sur un rendu
sans detourage (aucun crash de la generation).
"""
import os
import hashlib
from PIL import Image

# Le modele IA (u2net.onnx) est fourni dans ce dossier -> aucun telechargement
# necessaire. Doit etre defini AVANT le premier appel a rembg.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
os.environ.setdefault("REMBG_HOME", os.path.join(_PROJECT_ROOT, "rembg_home"))

CACHE_DIR = os.path.join(_PROJECT_ROOT, "cache", "cutouts")

_session = None
_available = None  # None = pas encore teste, True/False = resultat du test


def _get_session():
    global _session, _available
    if _available is False:
        return None
    if _session is not None:
        return _session
    try:
        from rembg import new_session
        _session = new_session("silueta")
        _available = True
        return _session
    except Exception as e:
        print(f"     (detourage IA indisponible ({e}), on continue sans)")
        _available = False
        return None


def get_cutout(photo_path: str, cache_key: str, force_refresh: bool = False):
    """
    Renvoie une image PIL RGBA detouree (fond transparent) pour ce fichier,
    mise en cache par 'cache_key' (ex. le terme de recherche de l'animal).
    Renvoie None si le detourage n'est pas disponible ou echoue.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.md5(cache_key.lower().encode("utf-8")).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{key}.png")

    if os.path.exists(cache_path) and not force_refresh:
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            pass  # cache corrompu -> on retente

    session = _get_session()
    if session is None:
        return None

    try:
        from rembg import remove
        img = Image.open(photo_path).convert("RGB")
        cutout = remove(img, session=session)
        cutout.save(cache_path, "PNG")
        return cutout
    except Exception as e:
        print(f"     (echec du detourage pour cet animal ({e}), on continue sans)")
        return None
