# Histoires d'animaux · Ép. 3 — Les lapins d'Australie

Vidéo 1080×1920, ~1 min 48, voix ElevenLabs. DA « Culture G » + animations façon mapmotion :
flou de vitesse pendant les zooms, textes cinétiques lettre par lettre (Lilita One), sous-titres mot par mot,
aplat d'invasion qui s'étend depuis Geelong, icônes de lapins qui se multiplient, drapeau australien dans le pays au premier zoom.

## Pipeline
1. `python3 grade.py full` – texture régionale Australie (`tex_region.jpg`, 108–158°E / 8–46°S) ; `tex_world.jpg` = celle de `../lion`
2. `VO_FILE=voix-lapin.mp3 python3 audio.py` – voix découpée, timeline, bruitages (tac de texte, piquets, corne, tampon…), musique enjouée
3. `sh mix.sh` (bruitages/musique -50 %, -14 LUFS) → `node build.js` → `sh sheet.sh planche.jpg 5 30 60`
4. Rendu : `node render_par.js <début> <fin>` × 4, puis ffmpeg sur `frames/`

## Sources
- 24 lapins arrivés à Noël 1859 chez Thomas Austin (Barwon Park, Geelong) ; 20 000 tués sur son domaine en 1865 ;
  jusqu'à 100 km/an, colonisation la plus rapide d'un mammifère introduit ; ~200 millions aujourd'hui, 70 % du territoire
  (Wikipédia « Rabbits in Australia », PNAS 2022, Smithsonian, Aussie Animals)
- Clôtures 1901–1907, 3 256 km au total (State Library of WA, Wikipédia) — tracés simplifiés sur la carte
- Myxomatose 1950 : de ~600 à ~100 millions en deux ans, puis résistance (Wikipédia « Rabbit plagues in Australia »)
- Portrait de Thomas Austin : gravure du XIXe siècle (domaine public)
