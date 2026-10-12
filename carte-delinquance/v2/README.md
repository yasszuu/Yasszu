# Départements les plus criminogènes – v2 (DA satellite + son)

Vidéo 1080×1920 : globe satellite → zoom France → compte à rebours N°5 → N°1 → récap.

## Pipeline
1. `python3 textures.py` – textures satellite Natural Earth (déjà fournies : `tex_*.jpg`)
2. `python3 audio.py` – voix off (Piper `fr_FR-tom-medium` via sherpa-onnx), timeline, bruitages et musique synthétisés
3. `sh mix.sh` – mixage (compression voix, ducking musique, -14 LUFS)
4. `node build.js` – page HTML autonome (`departements-criminogenes.html`, lisible avec le son)
5. `node render.js` – rendu image par image + mux → `departements-criminogenes.mp4` (ou plus rapide : `render_par.js <début> <fin>` en plusieurs process, puis ffmpeg sur `frames/`)

Le texte de la voix off et des sous-titres se modifie dans `SCRIPT` (audio.py) ; `*mot*` = surligné en jaune.
Modèles voix : `https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-fr_FR-tom-medium.tar.bz2`
Dépendances : `pip install sherpa-onnx soundfile numpy scipy pillow`, `npm i` dans le dossier parent.
