"""
Cherche une image de fond (9:16) fournie par l'utilisateur pour l'ecran
d'ouverture (ex. "fond_intro/"). Si plusieurs images sont presentes, en
choisit une au hasard a chaque generation. Renvoie None si le dossier est
vide/absent (un fond de couleur pastel aleatoire est alors utilise).
"""
import os
import random

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def list_background_files(folder: str):
    if not folder or not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f) for f in sorted(os.listdir(folder))
        if f.lower().endswith(VALID_EXTENSIONS)
    ]


def find_intro_background(folder: str):
    """Choisit une image de fond au hasard parmi celles du dossier (ou None si vide/absent)."""
    files = list_background_files(folder)
    if not files:
        return None
    return random.choice(files)
