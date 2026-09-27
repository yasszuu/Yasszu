"""
Genere une paire de couleurs complementaires (opposees sur le cercle
chromatique) a chaque appel, pour habiller les zones haut/bas de chaque round
sans avoir besoin d'images de fond.
"""
import colorsys
import random


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def random_complementary_pair(saturation: float = 0.68, value: float = 0.60):
    """
    Renvoie (couleur_haut, couleur_bas) : deux teintes opposees (180 degres)
    sur le cercle chromatique, avec une saturation/luminosite choisie pour
    rester lisible avec du texte blanc (contour noir) par-dessus.
    """
    hue = random.random()
    comp_hue = (hue + 0.5) % 1.0
    return _hsv_to_hex(hue, saturation, value), _hsv_to_hex(comp_hue, saturation, value)


def random_single_color(saturation: float = None, value: float = None) -> str:
    """
    Une seule teinte aleatoire, PASTEL (claire et vive, pas delavee) pour
    capter l'attention des les premieres secondes (l'ecran d'ouverture ne
    doit jamais paraitre terne).
    """
    s = saturation if saturation is not None else random.uniform(0.38, 0.58)
    v = value if value is not None else random.uniform(0.86, 0.96)
    return _hsv_to_hex(random.random(), s, v)


def random_dark_color(saturation: float = None, value: float = None) -> str:
    """
    Une teinte sombre et dramatique (pour l'ecran "carte de combat"), assez
    saturee pour ne pas paraitre terne malgre l'obscurite.
    """
    s = saturation if saturation is not None else random.uniform(0.55, 0.75)
    v = value if value is not None else random.uniform(0.14, 0.22)
    return _hsv_to_hex(random.random(), s, v)


def random_corner_pair():
    """
    Fond des rounds : alterne au hasard entre (bleu en haut, rouge en bas)
    et l'inverse (rouge en haut, bleu en bas), façon coins de ring.
    """
    blue = "#1E50BE"
    red = "#BE231E"
    return (blue, red) if random.random() < 0.5 else (red, blue)
