# Générateur de vidéos "Qui gagne le combat ?" (TikTok)

Génère automatiquement une vidéo verticale (1080x1920) façon TikTok :
pour chaque round → **annonce du combat (voix off) → décompte 3-2-1 → résultat en %
→ phrase d'explication**, répété pour tous les rounds définis dans `config.json`.

- Voix off : générée automatiquement avec **edge-tts** (gratuit, aucune clé API).
- Images des animaux : récupérées automatiquement sur **Wikimedia Commons** (libres de droits).
- Aucun logiciel de montage à installer : tout est fait par le script (ffmpeg est
  embarqué via la librairie Python `imageio-ffmpeg`).

## 1. Installation (une seule fois)

Prérequis : **Python 3.10 ou plus récent** installé sur ta machine
(vérifiable avec `python --version` dans PowerShell — sinon installe-le depuis
[python.org](https://www.python.org/downloads/), en cochant bien "Add Python to PATH").

Dans PowerShell, place-toi dans le dossier du projet puis installe les dépendances :

```powershell
cd chemin\vers\le\dossier\tiktok-animal-battle
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> ⚠️ Cette installation est plus longue et plus lourde qu'avant : elle inclut
> maintenant `rembg` + `onnxruntime` (détourage IA des animaux pour l'écran
> d'ouverture). Le **modèle d'IA lui-même est déjà fourni** dans le dossier
> `rembg_home/` (aucun téléchargement de modèle au premier lancement), mais
> `pip install` devra tout de même récupérer ces nouveaux paquets Python.
>
> **Si ça échoue avec une erreur SSL** (`CERTIFICATE_VERIFY_FAILED`, fréquent
> derrière un proxy d'entreprise type Zscaler), installe ces deux paquets en
> mode hors-ligne à la place, avec les wheels déjà fournies dans le dossier
> `wheels_win/` :
> ```powershell
> pip install --no-index --find-links=wheels_win rembg onnxruntime
> ```

> Si PowerShell bloque l'activation du venv avec une erreur de "execution policy",
> lance une fois : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 2. Générer la vidéo

```powershell
python main.py
```

La vidéo finale est créée dans `output/battle_video.mp4`.
Le premier lancement est plus long (téléchargement des images + génération de la voix) ;
les lancements suivants sur les mêmes animaux sont beaucoup plus rapides grâce au cache
(`cache/images` et `cache/audio`).

### Options utiles

```powershell
python main.py --refresh-images   # force le re-téléchargement des photos
python main.py --refresh-audio    # force la régénération de la voix off
python main.py --config autre_config.json
```

## 3. Personnaliser les rounds

Tout se passe dans **`config.json`**. Le fichier contient une grande liste `"rounds_pool"`
(16 combats d'animaux par défaut) et le script en **pioche au hasard** un nombre
défini (`"rounds_per_video"`, 6 par défaut) à chaque lancement — donc chaque vidéo
générée est différente, avec des combats variés.

```json
{
  "animal_a": "Lion",
  "animal_b": "Tigre",
  "search_a": "lion animal",
  "search_b": "tiger animal",
  "percent_a": 43,
  "percent_b": 57,
  "explanation": "Le tigre est plus lourd et plus puissant, mais le lion compense..."
}
```

- `animal_a` / `animal_b` : les noms affichés à l'écran et lus par la voix (en français).
- `search_a` / `search_b` : le terme de recherche d'image (en anglais donne souvent de
  meilleurs résultats sur Wikimedia Commons — ex. `"tiger animal"` plutôt que `"tigre"`).
- `percent_a` / `percent_b` : doivent additionner 100. Le plus haut pourcentage gagne
  automatiquement (tag "GAGNANT" affiché + phrase de résultat générée).
- `explanation` : la phrase lue en voix off après le résultat.

Ajoute autant de combats que tu veux dans `rounds_pool` — plus il y en a, plus les
vidéos générées seront variées d'une fois sur l'autre.

### Options en ligne de commande

```powershell
python main.py --rounds 8          # génère une vidéo avec 8 rounds au lieu de 6
python main.py --seed 42            # rejoue exactement la même sélection aléatoire
```

### Fonds : couleurs complémentaires automatiques

Chaque round tire au hasard deux couleurs opposées sur le cercle chromatique
(ex. rouge/vert, violet/jaune) pour habiller les zones haut/bas — pas besoin
de fournir d'images, tout est généré automatiquement.

### Police personnalisée

Dépose ta police (ex. `Super Jello.ttf`) dans le dossier **`fonts/`**. Le
fichier `config.json` pointe déjà vers `fonts/Super Jello.ttf` pour les
titres/pourcentages/VS (`font_bold`). Si le fichier est absent, le script se
rabat automatiquement sur une police système (pas de crash).

### Durée de la vidéo : adaptative

Par défaut, le script vise une vidéo de **1min20 à 2min**
(`target_duration_min` / `target_duration_max` dans `config.json`, en
secondes) et **adapte automatiquement le nombre de rounds** pour rentrer
dans cette fourchette — pas besoin de calculer combien de rounds ça
représente. Pour forcer un nombre de rounds précis à la place :
```powershell
python main.py --rounds 8
```

### Visuel des animaux : silhouettes détourées

Pendant les rounds (et dans l'intro), les animaux ne sont plus affichés
dans un cadre rectangulaire : chaque photo est **détourée** (fond
supprimé) et affichée avec un **léger contour blanc**, mise à l'échelle
pour tenir "pile" dans son espace — ni trop grande, ni trop petite, quel
que soit le format d'origine de l'image (portrait, paysage, carré...).

**Banque d'images personnelle** : dépose tes propres photos d'animaux dans
le dossier **`banque_animaux/`**, nommées d'après le nom français exact
utilisé dans la vidéo (ex. `gorille.png`, `requin blanc.jpg` — accents et
majuscules n'ont pas d'importance). Le script vérifie D'ABORD ce dossier
avant de chercher sur Wikimedia : tu n'es pas obligé de tout fournir, juste
les animaux pour lesquels tu veux garantir une image de qualité. Les images
peuvent déjà être détourées (fond transparent) ou non — le script gère les
deux. La liste complète des animaux utilisables (avec le nom de fichier
suggéré pour chacun) se trouve dans **`LISTE_ANIMAUX.md`** à la racine du
projet.

**Détourage IA (rembg)** : pour les animaux non fournis dans la banque, le
script détoure automatiquement la photo trouvée sur Wikimedia. Le modèle
d'IA nécessaire (~44 Mo) est **fourni directement dans le dossier
`rembg_home/`** — aucun téléchargement n'est nécessaire au premier
lancement. Si le détourage échoue pour une raison quelconque (image
corrompue, etc.), la photo brute est utilisée à la place (avec son propre
contour), sans faire planter la génération.

### Couleurs de fond des rounds : bleu vs rouge

Chaque round alterne aléatoirement entre **bleu en haut / rouge en bas**
et l'inverse, façon coins de ring de boxe.

### Séquence d'ouverture

Chaque vidéo commence par un écran-titre ("DUELS D'ANIMAUX", ou ton logo si
tu en as déposé un dans `logo/`), **sans rien spoiler** : seul le combat le
plus **SERRÉ** de la vidéo (celui dont l'issue est la plus incertaine,
toujours gardé pour la fin) est teasé, avec les deux animaux concernés
(et seulement eux) qui apparaissent chacun au moment où son nom est
prononcé dans une question qui ne révèle rien ("Si un ours brun croise un
gorille dans la nature, qui ressort vivant ?").

**Effets d'impact** : chaque animal arrive avec un léger effet de rebond
(il apparaît un peu trop grand puis se stabilise), un petit "boom" sourd
retentit au moment où le second animal apparaît, une "stat choc" sans
spoiler s'affiche entre les deux (l'écart réel en points, jamais qui est
en tête), et un bref effet de zoom marque le moment où les deux sont enfin
réunis à l'écran.

**Fond personnalisé** : dépose une ou plusieurs images au format 9:16 dans
le dossier **`fond_intro/`** pour les utiliser comme fond de cet écran
(une est choisie au hasard à chaque génération). Dossier vide → fond de
couleur pastel aléatoire (comportement par défaut).

### Cris d'animaux (best effort)

Quand un animal apparaît (en intro ou pendant un round), le script essaie
de trouver un court extrait de son cri/chant sur Wikimedia Commons et de le
jouer juste après. La couverture est **très inégale** selon les espèces
(souvent excellente pour les oiseaux, quasi inexistante pour beaucoup
d'insectes/poissons) : quand rien n'est trouvé, l'animal apparaît
simplement sans son, sans jamais faire échouer la génération.

### Rythme variable

Pour casser la prévisibilité sur une vidéo à plusieurs rounds :
- **Décompte qui s'accélère** : 3 secondes pour le premier round, puis 0,3s
  de moins à chaque round suivant (jusqu'à un plancher de 1,5s).
- **Rounds "express"** : environ 30% des rounds (jamais le premier, jamais
  le dernier) sautent la phrase d'explication et enchaînent directement
  après le résultat.
- **Barre de progression discrète** : une fine ligne en haut de l'écran se
  remplit au fil de la vidéo, pour rassurer inconsciemment qu'il reste du
  contenu à voir.

### Transition entre les rounds : balayage rotatif

À la fin de chaque round, les deux zones se fondent d'abord vers le **noir**
(contraste net, pas de texte qui se "délave"), puis le badge VS et la barre
centrale **tournent sur 360° autour du point central** pour balayer le noir
et dévoiler les couleurs de la manche suivante (comme une aiguille d'horloge
qui repeint l'écran en tournant), accompagnés d'un léger souffle de vent.
Le badge VS reste toujours au-dessus de tous les calques, jamais recouvert.

### Intro : apparition animée + formulations variées

Chaque round commence sur un écran vide (juste le badge VS). L'intro est
tirée au hasard parmi 8 formulations différentes ("Dans la nature, qui
remporte...", "Face à face...", etc.), et chaque animal **grossit et
apparaît en fondu pile au moment où son nom est prononcé**, accompagné
d'un petit "pop". Le timing est calculé à partir des données de
prononciation mot-par-mot fournies par edge-tts — aucun réglage à faire.

### Décompte animé + son

Après l'annonce du combat, une barre horizontale fine (juste derrière le badge
VS) se remplit de gauche à droite pendant 3 secondes, accompagnée d'un effet
sonore de décompte (3 bips, un par seconde) généré directement par le script.

### Résultat

Au moment d'afficher les pourcentages, les photos sont assombries de 70%
pour que le chiffre ressorte bien. Chaque pourcentage est écrit dans la
couleur de fond de sa propre zone (haut/bas), avec un contour blanc. Un
petit "ding" retentit pile au moment du reveal, et le cadre du
**vainqueur** fait un bref flash doré.

### Pourcentages animés

Au moment du résultat, les deux pourcentages **grimpent de 0 jusqu'à leur
valeur finale** en ~0,6 s (effet compteur), pendant le clignotement vert/noir.

### Pas deux fois le même animal

Le script évite de montrer le même animal dans deux combats d'une même vidéo
(tant que le pool de combats le permet).

### Explication : sous-titres auto-générés

Une fois le résultat annoncé, toute la moitié du **perdant** (haut ou bas)
devient sa couleur unie, et le texte d'explication s'affiche en
**sous-titres façon TikTok** : quelques mots à la fois, en TRÈS gros,
synchronisés sur la voix (au lieu d'un paragraphe fixe). Le badge VS reste
toujours intact, jamais recouvert.

### Sortie de round animée

Juste avant la transition vers le round suivant, les deux zones (photo du
vainqueur + texte du perdant) se fondent en douceur dans leur couleur unie,
pour un enchaînement propre avec le balayage rotatif qui suit.

### Écran de fin (CTA)

Chaque vidéo se termine par un écran avec une incitation à l'action tirée
au hasard ("Commente qui aurait dû gagner...", "Abonne-toi...", etc.), fond
pastel aléatoire et voix.

### Vidéos de sortie

Chaque génération crée un nouveau fichier numéroté dans `output/`
(`video_1.mp4`, `video_2.mp4`, ...) sans jamais écraser les précédents.

### Musique de fond

Dépose **un ou plusieurs fichiers audio** (.mp3, .wav, .m4a, .aac, .ogg ou
.mp4) dans le dossier **`musique/`**. À chaque génération, le script en
choisit **un au hasard** et le mixe en fond sonore sur toute la vidéo (en
boucle si trop court, à volume réduit pour ne pas couvrir la voix — réglable
via `music_volume` dans `config.json`, entre 0 et 1). Dossier vide → vidéo
générée sans musique de fond.

### Sélection des images

Pour chaque animal, le script cherche d'abord la **catégorie Wikimedia**
correspondante (une collection organisée par des humains, donc bien plus
fiable) avant de se rabattre sur une recherche classique si besoin. Une
longue liste de mots-clés (fossile, squelette, spécimen de musée, salle
d'exposition vide, jouet, carte, schéma...) permet aussi d'écarter les
résultats qui ne sont visiblement pas des photos de l'animal vivant.

### Voix : vitesse et volume

Par défaut la voix est réglée à **deux fois plus rapide et deux fois plus forte**
que la normale (`voice_rate` et `voice_volume` à `"+100%"` dans `config.json`).
Modifie ces valeurs si tu veux revenir à une vitesse plus posée (ex. `"+30%"`).

### Autres réglages (`"video"` dans `config.json`)

| Clé | Rôle |
|---|---|
| `voice` | Voix edge-tts utilisée (ex. `fr-FR-HenriNeural`, `fr-FR-DeniseNeural`) |
| `voice_rate` | Vitesse de la voix (ex. `"+8%"`, `"-10%"`) |
| `accent_color_a` / `accent_color_b` | Couleurs des deux camps |
| `countdown_seconds`, `result_display_seconds`, ... | Durées des différentes phases |
| `output_file` | Chemin du fichier vidéo final |

Pour lister toutes les voix françaises disponibles :

```powershell
python modules\tts.py
```

## 4. Structure du projet

```
tiktok-animal-battle/
├── main.py                 <- à lancer (python main.py)
├── config.json              <- les rounds + réglages (à éditer)
├── requirements.txt
├── modules/
│   ├── image_fetcher.py     <- récupère les images (Wikimedia Commons)
│   ├── tts.py                <- génère la voix off (edge-tts)
│   ├── graphics.py           <- dessine les visuels (PIL)
│   └── video_builder.py      <- assemble tout avec moviepy
├── assets/fonts/             <- polices Anton + Poppins (incluses, licence OFL)
├── cache/                    <- images/audio mis en cache (auto-généré)
└── output/                   <- vidéo(s) générée(s)
```

## Notes légales

- Les images viennent de Wikimedia Commons : la plupart sont en domaine public ou
  en licence Creative Commons (CC-BY / CC-BY-SA), qui demande en théorie une
  attribution de l'auteur en cas de republication. Pour un usage TikTok personnel
  ça passe très largement inaperçu, mais garde ça en tête si tu montes en volume —
  tu peux consulter la fiche de chaque image sur commons.wikimedia.org.
- Les polices **Anton** et **Poppins** sont sous licence libre SIL Open Font License
  (incluses dans `assets/fonts/`, fichier `OFL.txt`).
- La voix edge-tts utilise le service de synthèse vocale de Microsoft Edge ;
  usage gratuit mais non garanti à 100% dans le temps (si ça casse un jour, il
  faudra remplacer `modules/tts.py` par un autre moteur TTS).

## Idées d'amélioration futures

- Ajouter une musique de fond libre de droits (mixée en fond sonore).
- Générer plusieurs vidéos en une fois à partir de plusieurs fichiers config.
- Ajouter une miniature/texte d'accroche pour le premier écran (hook).
