# Histoires d'animaux · Ép. 6 — La sterne arctique

Vidéo 1080×1920, 1 min 34, voix ElevenLabs. Carte animée (route en S Groenland → Antarctique → Groenland, séparation
Afrique / Brésil, record 2016 autour du monde, Terre-Lune) avec l'image de sterne fournie, + **3 plans 3D Blender**
(style maquette, oiseau rouge stylisé) : Groenland (banquise, icebergs), Atlantique au coucher de soleil, Antarctique
(barrière de glace, icebergs tabulaires).

## Pipeline
1. `python3 align.py` – découpe la voix sur les répliques (Whisper + alignement) → `vo_bounds.json`
2. `VO_FILE=assets/voix-sterne.mp3 python3 audio.py` → `timeline.json` (dont `clips` = plans 3D), bruitages, musique ; `sh mix.sh`
3. Plans 3D : `SHOT=groenland|ocean|antarctique bl/bin/python shot.py ep/clips/<nom> 0 <n> 16 50` (bpy 4.5, Cycles CPU)
4. `node build.js` → `node render_par.js <a> <b>` (la page charge les images 3D de `clips/` à la volée) → ffmpeg

## Sources
- Egevang et al. 2010 (PNAS) : sternes du Groenland / Islande, ~70 900 km/an en moyenne, halte en Atlantique Nord,
  routes séparées au large de l'Afrique de l'Ouest (Afrique ou Brésil), retour en S ; >30 ans de vie → ~2,4 millions de km (≈ 3 A/R Terre-Lune)
- Newcastle University / BBC Springwatch 2016 : sterne des îles Farne (Angleterre), 96 000 km en 10 mois
- Poids ~100 g
