# Histoires d'animaux · Ép. 5 — Le moustique tigre envahit la France

Vidéo 1080×1920, ~1 min 38, voix ElevenLabs. Priorité au motion design : seulement 3 photos plein écran (~2 s),
le reste sur la carte : demi-tour du globe vers l'Asie du Sud-Est, routes maritimes, bateau qui traverse
(Singapour → Suez → Albanie, Japon → Pacifique → Panama → Texas, Texas → Atlantique → Gibraltar → Gênes),
côte ligure jusqu'à Menton, camion qui remonte la vallée du Rhône jusqu'à Paris, départements qui s'allument
année par année avec compteur, foyers de chikungunya 2025. Flou de mouvement très léger.

## Pipeline
1. Texture régionale `tex_region.jpg` : `grade.py` (voir `../hippo/grade.py`) sur la boîte lon −6…22, lat 36…52
2. `VO_FILE=assets/voix-moustique.mp3 python3 audio.py` – découpe la voix, timeline, bruitages (bzz fourni + pack), musique
3. `sh mix.sh` → `node build.js` → `sh sheet.sh planche.jpg 5 30 60`
4. Rendu : `node render_par.js <début> <fin>` × 4, puis ffmpeg sur `frames/`
Départements : `../../dep.geojson` (IGN simplifié) + années dans `deps_years.py` → `deps.json`.

## Sources
- Origine : forêts d'Asie du Sud-Est ; voyage dans les pneus usagés ; Albanie 1979, Texas 1985, Italie (Gênes) 1990, Menton 2004 (Institut Pasteur, IRD)
- 81 départements colonisés au 1er janvier 2025, soit 84 % de la métropole ; +Aube et Eure-et-Loir fin 2025 (Santé publique France)
- 809 cas autochtones de chikungunya en métropole en 2025, record (Santé publique France / Vidal)
- Années par département : **approximation illustrative** calée sur les jalons publiés (06 2004 ; 2B 2006 ; 2A, 83 2007 ; 04, 13 2010 ;
  30, 34, 84 2011 ; 20 dép. fin 2014 ; Val-de-Marne 2015 ; Paris 2018 ; 51 début 2019 ; 71 en 2022 ; 78 en 2023 ; Marne, Haute-Marne,
  Haute-Saône 2024). Carte finale (2025) : 15 départements non colonisés (Creuse, Manche, Finistère, Ardennes, Nord, Calvados,
  Côtes-d'Armor, Aube, Eure-et-Loir, Orne, Seine-Maritime, Pas-de-Calais, Somme, Aisne, Meuse).
