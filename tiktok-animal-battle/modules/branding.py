"""
Cherche une image de logo/titre fournie par l'utilisateur (ex. "logo/"),
utilisee a la place du texte "DUELS D'ANIMAUX" dans l'ecran d'ouverture.
Renvoie None si le dossier est vide/absent (le titre texte reste alors
utilise par defaut).
"""
import os

VALID_EXTENSIONS = (".png",)


def find_logo_file(folder: str):
    if not folder or not os.path.isdir(folder):
        return None
    for f in sorted(os.listdir(folder)):
        if f.lower().endswith(VALID_EXTENSIONS):
            return os.path.join(folder, f)
    return None
