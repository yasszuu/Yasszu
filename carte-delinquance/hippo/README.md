# Histoires d'animaux · Ép. 4 — Les hippopotames d'Escobar

Vidéo 1080×1920, ~1 min 47, voix ElevenLabs. Nouveautés : **séquences photo plein écran** (images fournies,
lent zoom + plongée avec flou à l'entrée) alternées avec la carte ; police unique Montserrat ;
**vrais bruitages** fournis (`assets/s_*.wav` : woosh, pop, tick, impact, cri d'hippopotame) ;
aucun pictogramme dessiné (uniquement éléments de carte : drapeau, fleuve, trajets, épingles).

## Pipeline
1. `python3 grade.py full` – texture régionale Colombie (`tex_region.jpg`) ; `tex_world.jpg` = celle de `../lion`
2. `VO_FILE=assets/voix-hippo.mp3 python3 audio.py` – découpe la voix, timeline (photos + carte), place les bruitages, musique
3. `sh mix.sh` → `node build.js` → `sh sheet.sh planche.jpg 5 30 60`
4. Rendu : `node render_par.js <début> <fin>` × 4, puis ffmpeg sur `frames/`
Fleuves Magdalena / Cauca : Natural Earth `ne_10m_rivers_lake_centerlines` (`rivers.json`).
Images p1…p8 et PNG détourés : fournis par l'utilisateur (dossier Drive « hippo escobar »).

## Sources
- 4 hippopotames (1 mâle, 3 femelles) importés par Pablo Escobar à l'Hacienda Nápoles dans les années 80 ; Escobar tué en 1993 à Medellín
- ~169–170 individus en 2023 (Institut Humboldt) ; espèce invasive depuis 2022 ; projections jusqu'à ~1 000 en 2035
- Plan 2023 : 60 vers l'Inde (Gujarat), 10 vers le Mexique — aucun transfert réalisé
- Avril 2026 : euthanasie autorisée pour ~80 hippopotames (Mongabay, CNN Español) ; habitants de Doradal opposés (Infobae)
