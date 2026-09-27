"""
Cherche un fichier de musique de fond dans le dossier fourni par l'utilisateur
(ex. "musique/"). Si plusieurs fichiers sont presents, en choisit un au
hasard a chaque generation. Renvoie None si le dossier est vide/absent (le
script fonctionne alors sans musique de fond).
"""
import os
import random

VALID_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".mp4")


def list_music_files(folder: str):
    if not folder or not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f) for f in sorted(os.listdir(folder))
        if f.lower().endswith(VALID_EXTENSIONS)
    ]


def find_music_file(folder: str):
    """Choisit un fichier de musique au hasard parmi ceux du dossier (ou None si vide/absent)."""
    files = list_music_files(folder)
    if not files:
        return None
    return random.choice(files)
